import json
import random
import string

from django.apps import apps
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from injector import Injector
from rest_framework import status
from rest_framework.test import APITestCase

from .test_ioc import TestApiAppModule
from ..models import Client, MailTemplate


class ClientEndpointsTest(APITestCase):

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        apps.app_configs['django_injector'].injector = Injector([TestApiAppModule()])
        # create a mock token
        self.access_token = self.randomString(25)
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
        response = self.client.get('{url}?page=2&per_page=5&expand=parent&access_token={access_token}'.format(url=url, access_token=self.access_token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['current_page'], 2)
        self.assertEqual(json_response['per_page'], 5)

    def test_add(self):

        url = reverse('mail-template-endpoints:list-create')
        html_content = '''
                <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
          <link rel="stylesheet" href="style.css" />
          <title>{% block title %}{% endblock %} - My Webpage</title>
          {% block html_head %}{% endblock %}
        </head>
        <body>
          <div id="content">
            {% block content %}{% endblock %}
          </div>

          <div id="footer">
            {% block footer %}
            &copy; Copyright 2006 by <a href="http://mydomain.tld">myself</a>.
            {% endblock %}
          </div>
        </body>
                '''

        data = {
            'identifier': 'identifier_1',
            'locale': 'es',
            'html_content': html_content,
            'from_email': 'test@test.com',
            'subject': 'test subject',
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['identifier'], 'identifier_1')

    def test_render(self):
        url = reverse('mail-template-endpoints:list-create')
        html_content = '''
                        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                <html xmlns="http://www.w3.org/1999/xhtml">
                <head>
                  <link rel="stylesheet" href="style.css" />
                  <title>{{title}} - My Webpage</title>
                </head>
                <body>
                  <div id="content">
                  {{content}}
                  </div>

                  <div id="footer">
                    {{footer}}
                    &copy; Copyright 2006 by <a href="http://mydomain.tld">myself</a>.
                  </div>
                </body>
                        '''

        data = {
            'identifier': 'identifier_1',
            'locale': 'es',
            'html_content': html_content,
            'from_email': 'test@test.com',
            'subject': 'test subject',
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        url = reverse('mail-template-endpoints:render', kwargs={'pk': json_response['id']})
        data = {
            'footer': "this is the footer content",
            'content': 'this is the content',
            'title': 'this is title content'
        }

        response = self.client.put('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        print(response.content)
        self.assertContains(response, "this is title content", 1)
        self.assertContains(response, "this is the footer content", 1)
        self.assertContains(response, "this is the content", 1)

    def test_add_then_add_allowed_client(self):
        url = reverse('mail-template-endpoints:list-create')

        data = {
            'identifier': 'identifier_1',
            'locale': 'es',
            'from_email': 'test@test.com',
            'subject': 'test subject',
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['identifier'], 'identifier_1')

        pk = int(json_response['id'])

        client = Client.objects.first()

        url = reverse('mail-template-endpoints:allowed_clients', kwargs={'pk': pk, 'client_id': client.id})
        response = self.client.put('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_update_activate_fails(self):
        url = reverse('mail-template-endpoints:list-create')

        data = {
            'identifier': 'identifier_1',
            'locale': 'es',
            'from_email': 'test@test.com',
            'subject': 'test subject',
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['identifier'], 'identifier_1')

        pk = int(json_response['id'])

        data = {
            'is_active': True
        }
        url = reverse('mail-template-endpoints:retrieve_update_destroy', kwargs={'pk': pk})
        response = self.client.put('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)
        json_response = json.loads(response.content)
        self.assertEqual(json_response[0],
                         _('If you activate the template at least should have a body content (HTML/PLAIN)'))

    def test_add_update_activate_ok(self):
        url = reverse('mail-template-endpoints:list-create')

        data = {
            'identifier': 'identifier_1',
            'locale': 'es',
            'from_email': 'test@test.com',
            'subject': 'test subject',
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(response.content)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['identifier'], 'identifier_1')

        pk = int(json_response['id'])

        data = {
            'html_content': 'Hello {{username}}!',
            'is_active': True
        }
        url = reverse('mail-template-endpoints:retrieve_update_destroy', kwargs={'pk': pk})
        response = self.client.put('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = json.loads(response.content)
