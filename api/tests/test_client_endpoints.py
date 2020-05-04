import json
import random
import string

from django.apps import apps
from django.urls import reverse
from injector import Injector
from rest_framework import status
from rest_framework.test import APITestCase

from .test_ioc import TestApiAppModule
from ..models import Client


class ClientEndpointsTest(APITestCase):

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        apps.app_configs['django_injector'].injector = Injector([ TestApiAppModule()])
        # create a mock token
        self.access_token = self.randomString(25)
        for i in range(10):
            Client.objects.create(
                client_id="OAUTH2_CLIENT_ID_{suffix}".format(suffix=self.randomString(10)),
                name="OAUTH2_CLIENT_NAME_{suffix}".format(suffix=self.randomString(10)),
            )

    def test_get_all(self):
        url = reverse('client-endpoints:list-create')
        response = self.client.get('{url}?page=2&per_page=5&access_token={access_token}'.format(url=url, access_token=self.access_token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['current_page'] , 2)
        self.assertEqual(json_response['per_page'] ,5)

    def test_add_client(self):
        url = reverse('client-endpoints:list-create')

        data = {
            'client_id': 'CLIENT_ID_1',
            'name': 'NAME_1'
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_1')

    def test_add_update_client(self):
        url = reverse('client-endpoints:list-create')

        data = {
            'client_id': 'CLIENT_ID_1',
            'name': 'NAME_1'
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_1')
        pk = int(json_response['id'])

        url = reverse('client-endpoints:retrieve_update_destroy', kwargs={'pk': pk})

        data = {
            'client_id': 'CLIENT_ID_12',
            'name': 'NAME_1'
        }

        response = self.client.put('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_12')

    def test_add_get_client(self):
        url = reverse('client-endpoints:list-create')

        data = {
            'client_id': 'CLIENT_ID_1',
            'name': 'NAME_1'
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_1')
        pk = int(json_response['id'])

        url = reverse('client-endpoints:retrieve_update_destroy', kwargs={'pk': pk})

        response = self.client.get('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['client_id'], 'CLIENT_ID_1')
