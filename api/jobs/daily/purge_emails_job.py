import logging
import traceback

from django_extensions.management.jobs import DailyJob
from django_injector import inject

from api.services import MaintenanceService
from api.utils import FileLock, config


class Job(DailyJob):
    help = "Mailing API Email Purge Job"
    code = 'api.jobs.purge_emails_job'  # an unique code

    @inject
    def execute(self, service: MaintenanceService):
        try:
            logging.getLogger('jobs').debug('calling MailCronJob.execute')
            with FileLock(self.__class__, False):
                service.purge(config('PURGE_EMAILS_JOB_MIN_AGE_DAYS'))
        except:
            logging.getLogger('jobs').error(traceback.format_exc())
