import json
import os
import random
import string

from django.apps import apps
from django.urls import reverse
from injector import Injector
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import MailTemplate, Client, Mail
from .test_ioc import TestApiAppModule
from ..services.sendgrid_email_service import SendGridEmailService
import base64

from ..utils import config


class EmailSendingTests(APITestCase):
    fixtures = ["mailtemplates.json"]

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        apps.app_configs['django_injector'].injector = Injector([TestApiAppModule()])
        # create a mock token
        self.access_token = self.randomString(25)
        client = Client.objects.create \
                (
                client_id="OAUTH2_CLIENT_ID_{suffix}".format(suffix=self.randomString(10)),
                name="OAUTH2_CLIENT_NAME_{suffix}".format(suffix=self.randomString(10)),
            )

        self.child = MailTemplate.objects.get(pk=4)
        self.child.allowed_clients.add(client)

    def test_email_send(self):
        url = reverse('mail-endpoints:list-send')
        base_dir = config('BASE_DIR')

        with open(os.path.join(base_dir, "api/tests/attachments/ticket.pdf"), "rb")  as pdf_file:
            pdf_data = base64.b64encode(pdf_file.read())

        with open(os.path.join(base_dir, "api/tests/attachments/qr.png"), "rb") as qr_file:
            image_data = base64.b64encode(qr_file.read())

        data = {
            'payload': {
                'summit_name': 'Test Summit',
                'order_owner_full_name': 'Sebastian Marcet',
                'edit_ticket_link': 'https://registration.test,com',
                'order_number': 'ORDER_NBR_1',
                'owner_email': 'smarcet@gmail.com',
                'owner_full_name': 'Sebastian Marcet',
                'promo_code': '',
                'ticket_type_name': 'FULL PASS',
                'ticket_currency_symbol': '$',
                'ticket_amount': '1000.00',
                'ticket_currency': 'USD',
                'ticket_number':'TICKET_NBR_1',
                'support_email': 'support@test.com',
                'manage_orders_url': 'https://registration.test.com/orders',
                'attachments': [
                    {'name': 'qr.png', 'content': image_data, 'type': 'application/octet-stream',
                     'disposition': 'inline', 'content_id': 'qrcid'},
                    {'name': 'ticket.pdf', 'content': pdf_data, 'type': 'application/pdf',
                     'disposition': 'attachment', }
                ]
            },
            'to_email': 'smarcet@gmail.com,sebastian@tipit.net',
            'cc_email': 'smarcet+3@gmail.com',
            'bcc_email': 'smarcet+2@gmail.com',
            'template': self.child.identifier,
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token),
                                    data, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        service = SendGridEmailService()

        res = service.process_pending_emails(10)

        self.assertEqual(res, 1)

        m = Mail.objects.first()
        self.assertTrue(m.is_sent)
