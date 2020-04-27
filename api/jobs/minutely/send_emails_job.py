from django_extensions.management.jobs import MinutelyJob
from random import random
import logging
import time, sys

from api.utils import FileLock


class Job(MinutelyJob):
    help = "Mailing API Email Send Job"
    code = 'api.jobs.send_emails_job'  # an unique code

    def execute(self):
        try:
            logging.getLogger('jobs').debug('calling MailCronJob.execute')
            with FileLock(self.__class__, False):
                time.sleep(random() * 5 * 60)
        except:
            logging.getLogger('jobs').error(sys.exc_info())
