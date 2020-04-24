import json
import random
import string

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Client, MailTemplate


class ClientEndpointsTest(APITestCase):

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        letters = string.ascii_lowercase
        client = None
        for i in range(10):
            client = Client.objects.create(client_id="OAUTH2_CLIENT_ID_{suffix}".format(suffix=self.randomString(10)))
        parent = MailTemplate.objects.create(
            identifier="parent_{suffix}".format(suffix=self.randomString(10)),
            is_active=True,
            subject="subject {suffix}".format(suffix=self.randomString(10)),
            plain_content="content {suffix}".format(suffix=self.randomString(10)),
            html_content="<p>content {suffix}</p>".format(suffix=self.randomString(10)),
        )
        for i in range(10):
            child = MailTemplate.objects.create(
                identifier="id_{suffix}".format(suffix=self.randomString(10)),
                is_active=True,
                subject="subject {suffix}".format(suffix=self.randomString(10)),
                plain_content="content {suffix}".format(suffix=self.randomString(10)),
                html_content="<p>content {suffix}</p>".format(suffix=self.randomString(10)),
                parent=parent
            )
            child.allowed_clients.add(client)
            # child.save()

    def test_get_all(self):
        url = reverse('mail-template-endpoints:list-create')
        response = self.client.get('{url}?page=2&per_page=5&expand=parent'.format(url=url))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['current_page'], 2)
        self.assertEqual(json_response['per_page'], 5)

