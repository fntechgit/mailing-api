import logging
import random
import string
from datetime import datetime

import pytz
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import ValidationError
from sendgrid import sendgrid
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
from sendgrid.helpers.mail import Mail as SendGridMail, Content, To, Cc, Bcc, Email

from api.models import Mail
from api.services import EmailService
from api.utils import is_empty, config
from python_http_client.exceptions import HTTPError
from django.db import connection, transaction


class SendGridEmailService(EmailService):
    def __init__(self):
        super().__init__()
        self.sg = sendgrid.SendGridAPIClient(api_key=config('SEND_GRID_API_KEY'))

    def process_pending_emails(self, batch: int) -> int:

        logging.getLogger('jobs').debug('SendGridEmailService.process_pending_emails batch {batch}'.format(batch=batch))

        with transaction.atomic(), connection.cursor() as cursor:
            now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            cursor.execute(
                "CREATE TEMPORARY TABLE temp_api_email AS SELECT `api_mail`.`id` FROM `api_mail` "
                "INNER JOIN `api_mailtemplate` ON (`api_mail`.`template_id` = `api_mailtemplate`.`id`) "
                "WHERE (`api_mail`.`lock_date` IS NULL AND  `api_mail`.`sent_date` IS NULL "
                "AND (`api_mail`.`next_retry_date` IS NULL OR `api_mail`.`next_retry_date` <= %s ) "
                "AND `api_mailtemplate`.`max_retries` > `api_mail`.`retries`) "
                "ORDER BY `api_mail`.`id` LIMIT %s", [now, batch])
            cursor.execute(
                "UPDATE `api_mail` "
                "SET `api_mail`.`lock_date` = %s "
                "WHERE EXISTS (SELECT 1 FROM temp_api_email where temp_api_email.id = api_mail.id)", [now])
            cursor.execute("SELECT ID FROM temp_api_email")
            records = cursor.fetchall()

        count = 0
        # get all not sent emails
        # which retries are not greather than template max_retries
        # and retry_date <= utc now
        for row in records:
            try:
                mail_id = row[0]
                logging.getLogger('jobs').debug(
                    "SendGridEmailService.process_pending_emails processing mail {mail_id}".format(mail_id=mail_id))
                if self._send_email(mail_id):
                    count += 1
            except Exception as e:
                logging.getLogger('jobs').error(e)

        logging.getLogger('jobs').debug(
            "SendGridEmailService.process_pending_emails processed {count}".format(count=count))

        return count

    @staticmethod
    def _generate_content_id(file: dict):
        letters = string.ascii_letters
        return 'CID_'.join(random.choice(letters) for i in range(10))

    @transaction.atomic
    def _send_email(self, mail_id: int) -> bool:

        m = Mail.objects.select_for_update().get(pk=mail_id)
        if not m:
            raise Mail.DoesNotExist

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
            cc_emails = []
            bcc_emails = []
            to_emails = To(config('DEV_EMAIL')) if config('DEBUG', False) else list(
                map(lambda e: To(e), m.to_email.split(',')))
            # CC ( only on non debug mode)
            if not config('DEBUG', False) and not is_empty(m.cc_email):
                logging.getLogger('jobs').debug(
                    "SendGridEmailService._send_email mail_id {mail_id} cc_email {cc_email}".format(mail_id=mail_id,
                                                                                                    cc_email=m.cc_email))
                cc_emails = list(map(lambda e: Cc(e), m.cc_email.split(',')))

            # BCC ( only on non debug mode)
            if not config('DEBUG', False) and not is_empty(m.bcc_email):
                logging.getLogger('jobs').debug(
                    "SendGridEmailService._send_email mail_id {mail_id} bcc_email {bcc_email}".format(mail_id=mail_id,
                                                                                                      bcc_email=m.bcc_email))
                bcc_emails = list(map(lambda e: Bcc(e), m.bcc_email.split(',')))

            html_content = Content("text/html", m.html_content) if not is_empty(m.html_content) else None
            plain_content = Content("text/plain", m.plain_content) if not is_empty(m.plain_content) else None
            mail = SendGridMail(from_email, to_emails, m.subject)

            if cc_emails is not None and len(cc_emails) > 0:
                logging.getLogger('jobs').debug(
                    "SendGridEmailService._send_email mail_id {mail_id} adding cc".format(mail_id=mail_id))
                mail.add_cc(cc_emails)

            if bcc_emails is not None and len(bcc_emails) > 0:
                logging.getLogger('jobs').debug(
                    "SendGridEmailService._send_email mail_id {mail_id} adding bcc".format(mail_id=mail_id))
                mail.add_bcc(bcc_emails)

            if html_content is not None:
                mail.add_content(html_content)
            if plain_content is not None:
                mail.add_content(plain_content)
            if m.payload:
                if 'attachments' in m.payload:
                    for file in m.payload['attachments']:
                        if 'content' in file and 'type' in file and 'name' in file:
                            disposition = file['disposition'] if 'disposition' in file else 'attachment'
                            attachment = Attachment()
                            attachment.file_content = FileContent(file['content'])
                            attachment.file_type = FileType(file['type'])
                            attachment.file_name = FileName(file['name'])
                            attachment.disposition = Disposition(disposition)
                            content_id = file['content_id'] if 'content_id' in file else self._generate_content_id(file)
                            if disposition == 'inline':
                                # https://sendgrid.com/blog/embedding-images-emails-facts/
                                attachment.content_id = ContentId(content_id)
                            mail.add_attachment(attachment)

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
        except HTTPError as e:
            logging.getLogger('jobs').warning(
                'email {id} failed'.format(id=m.id))
            logging.getLogger('jobs').error(e.to_dict)
            m.mark_retry(e.__str__())
            m.save(force_update=True)
        except Exception as e:
            logging.getLogger('jobs').warning(
                'email {id} failed'.format(id=m.id))
            logging.getLogger('jobs').error(e)
            m.mark_retry(e.__str__())
            m.save(force_update=True)

        return True
