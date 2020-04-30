import logging
import sys

from django_extensions.management.jobs import MinutelyJob
from django_injector import inject

from api.services import EmailService
from api.utils import FileLock, config


class Job(MinutelyJob):
    help = "Mailing API Email Send Job"
    code = 'api.jobs.send_emails_job'  # an unique code

    @inject
    def execute(self, service: EmailService):
        try:
            logging.getLogger('jobs').debug('calling MailCronJob.execute')
            with FileLock(self.__class__, False):
                service.process_pending_emails(config('SEND_EMAILS_JOB_BATCH'))
        except:
            logging.getLogger('jobs').error(sys.exc_info())
