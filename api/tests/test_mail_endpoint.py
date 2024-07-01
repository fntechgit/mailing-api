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
from ..models import MailTemplate


class EmailEndpointsTests(APITestCase):
    access_token = None
    child = None

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        apps.app_configs['django_injector'].injector = Injector([TestApiAppModule()])
        # create a mock token
        self.access_token = self.randomString(25)
        client = Client.objects.create(
            client_id="4zOaAu.JjXRT5eH3B~6-~AxtH06SPBZP.openstack.client",
            name="OAUTH2_CLIENT_NAME_{suffix}".format(suffix=self.randomString(10)),
        )
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
        plain_content = '''
        {% block title %}{% endblock %} 
        {% block head %}{% endblock %}
        {% block content %}{% endblock %}
        {% block footer %}
        &copy; Copyright 2006 by <a href="http://mydomain.tld">myself</a>.
        {% endblock %}
        '''

        parent = MailTemplate.objects.create(
            identifier="parent_{suffix}".format(suffix=self.randomString(10)),
            is_active=True,
            subject="subject {suffix}".format(suffix=self.randomString(10)),
            plain_content=plain_content,
            html_content=html_content,
        )
        child_html_content = '''
        {% extends "layout" %}
        {% block title %}{{title}}{% endblock %}
        {% block html_head %}
        <style type="text/css">
        .important {
        color: #336699;
        }
        </style>
        {% endblock %}
        {% block content %}
        <h1>{{title}}</h1>
        <p class="important">
        Welcome on my awsome homepage.
        </p>
        {% endblock %}
        '''

        child_plain_content = '''
        {% extends "layout" %}
        {% block title %}{{title}}{% endblock %}
        {% block content %}
        {{content}}
        {% endblock %}
        '''

        self.child = MailTemplate.objects.create(
            from_email='admin@admin.com',
            identifier="id_{suffix}".format(suffix=self.randomString(10)),
            is_active=True,
            subject="subject {suffix}".format(suffix=self.randomString(10)),
            plain_content=child_plain_content,
            html_content=child_html_content,
            parent=parent
        )

        self.child.allowed_clients.add(client)

    def test_send_fail_invalid_to(self):

        url = reverse('mail-endpoints:list-send')

        data = {
          'payload': {
              'title': 'this is the title',
              'content': 'this is the content',
          },
          'to_email': 'smarcet@gmail.com,sebastian@tipit',
          'template' : self.child.id,
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token = self.access_token), data, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)

    def test_send_ok(self):
        url = reverse('mail-endpoints:list-send')

        data = {
            'payload': {
                'title': 'this is the title',
                'content': 'this is the content',
            },
            'to_email': 'smarcet@gmail.com,sebastian@tipit.net',
            'template': self.child.identifier,
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token),
                                    data, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list(self):
        url = reverse('mail-endpoints:list-send')

        data = {
            'payload': {
                'title': 'this is the title',
                'content': 'this is the content',
            },
            'to_email': 'smarcet@gmail.com,sebastian@tipit.net',
            'template': self.child.identifier,
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=self.access_token),
                                    data, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get('{url}?access_token={access_token}&from_sent_date=1594092783'.format(url=url, access_token=self.access_token))
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


