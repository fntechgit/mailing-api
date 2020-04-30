import logging
from datetime import datetime

from django.db import transaction
from django.db.models import F
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import ValidationError
from sendgrid import sendgrid
from sendgrid.helpers.mail import Mail as SendGridMail, Content, To, Email

from api.models import Mail
from api.services import EmailService
from api.utils import is_empty, config


class SendGridEmailService(EmailService):
    def __init__(self):
        super().__init__()
        self.sg = sendgrid.SendGridAPIClient(api_key=config('SEND_GRID_API_KEY'))

    def process_pending_emails(self, batch: int) -> int:
        logging.getLogger('jobs').debug('SendGridEmailService.process_pending_emails batch {batch}'.format(batch=batch))
        count = 0
        # get all not sent emails
        # which retries are not greather than template max_retries
        # and retry_date <= utc now
        for m in Mail.objects.filter(
                Q(sent_date__isnull=True) &
                (
                        Q(next_retry_date__isnull=True) | Q(next_retry_date__lte=datetime.utcnow())
                )
        ).filter(template__max_retries__gt=F('retries')).order_by('id'):
            if self._send_email(m):
                count += 1
        logging.getLogger('jobs').debug(
            "SendGridEmailService.process_pending_emails processed {count}".format(count=count))

        return count

    @transaction.atomic
    def _send_email(self, m: Mail) -> bool:

        if is_empty(m.subject):
            raise ValidationError(_('subject is empty for email {id}'.format(id=m.id)))
        if is_empty(m.from_email):
            raise ValidationError(_('from_email is empty for email {id}'.format(id=m.id)))
        if is_empty(m.to_email):
            raise ValidationError(_('to_email is empty for email {id}'.format(id=m.id)))
        if is_empty(m.html_content) and is_empty(m.plain_content):
            raise ValidationError(_('content is empty for email {id}'.format(id=m.id)))

        try:
            from_email = Email(m.from_email)
            to_email = To(m.to_email)
            html_content = Content("text/html", m.html_content) if not is_empty(m.html_content) else None
            plain_content = Content("text/plain", m.plain_content) if not is_empty(m.plain_content) else None
            mail = SendGridMail(from_email, to_email, m.subject)

            if html_content is not None:
                mail.add_content(html_content)
            if plain_content is not None:
                mail.add_content(plain_content)

            # https://sendgrid.com/docs/API_Reference/Web_API_v3/Mail/errors.html
            request_body = mail.get()
            logging.getLogger('jobs').debug(
                'sending email {id} request {request}'.format(id=m.id, request=request_body))
            response = self.sg.send(mail)
            logging.getLogger('jobs').debug(
                'response.status_code {status_code}'.format(status_code=response.status_code))
            logging.getLogger('jobs').debug('response.body {body}'.format(body=response.body))
            logging.getLogger('jobs').debug('response.headers {headers}'.format(headers=response.headers))

            if response.status_code not in [200, 202]:
                logging.getLogger('jobs').warning(
                    'email {id} failed'.format(id=m.id))
                m.mark_retry(response.body)
                m.save(force_update=True)
                return False

            m.mark_as_sent()
            m.save(force_update=True)
            logging.getLogger('jobs').debug('email {id} successfully sent'.format(id=m.id))
        except Exception as e:
            logging.getLogger('jobs').warning(
                'email {id} failed'.format(id=m.id))
            logging.getLogger('jobs').error(e)
            m.mark_retry(e.__str__())
            m.save(force_update=True)

        return True
