import logging
from datetime import datetime

import pytz

from api.services import MaintenanceService
from django.db import connection, transaction


class EmailsMaintenanceService(MaintenanceService):

    def purge(self, older_than_days: int):
        logging.getLogger('jobs').debug(f'EmailsMaintenanceService.purge older than {older_than_days} days')

        with transaction.atomic(), connection.cursor() as cursor:
            now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            cursor.execute(
                "DELETE FROM api_mail WHERE api_mail.sent_date IS NOT NULL AND DATE_SUB(%s, INTERVAL %s DAY) > api_mail.created",
                [now, older_than_days])
            records = cursor.rowcount
            logging.getLogger('jobs').debug(f'EmailsMaintenanceService.purge deleted records: {records}')
