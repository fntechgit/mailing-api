import json
import random
import string

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Client


class ClientEndpointsTest(APITestCase):

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        letters = string.ascii_lowercase
        for i in range(10):
            Client.objects.create(client_id="OAUTH2_CLIENT_ID_{suffix}".format(suffix=self.randomString(10)))

    def test_get_all(self):
        url = reverse('client-endpoints:list-create')
        response = self.client.get('{url}?page=2&per_page=5'.format(url=url))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['current_page'] , 2)
        self.assertEqual(json_response['per_page'] ,5)

    def test_add_client(self):
        url = reverse('client-endpoints:list-create')

        data = {
            'client_id': 'CLIENT_ID_1',
        }

        response = self.client.post('{url}'.format(url=url), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_1')

    def test_add_update_client(self):
        url = reverse('client-endpoints:list-create')

        data = {
            'client_id': 'CLIENT_ID_1',
        }

        response = self.client.post('{url}'.format(url=url), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_1')
        pk = int(json_response['id'])

        url = reverse('client-endpoints:retrieve_update_destroy', kwargs={'pk': pk})

        data = {
            'client_id': 'CLIENT_ID_12',
        }

        response = self.client.put('{url}'.format(url=url), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_12')
