import json
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


class EmailSendingTests(APITestCase):

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        apps.app_configs['django_injector'].injector = Injector([TestApiAppModule()])
        # create a mock token
        self.access_token = self.randomString(25)
        client = Client.objects.create\
            (
                client_id="OAUTH2_CLIENT_ID_{suffix}".format(suffix=self.randomString(10)),
                name="OAUTH2_CLIENT_NAME_{suffix}".format(suffix=self.randomString(10)),
            )

        parent_html_content = '''
                              <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                       "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                      <html xmlns="http://www.w3.org/1999/xhtml">
                      <head>
                        <link rel="stylesheet" href="style.css" />
                        <title>{{title}} - My Webpage</title>
                      </head>
                      <body>
                        <div id="content">
                        {% block content %}
                        {% endblock %}
                        </div>

                        <div id="footer">
                          {{footer}}
                          &copy; Copyright 2006 by <a href="http://mydomain.tld">myself</a>.
                        </div>
                      </body>
                              '''

        parent = MailTemplate.objects.create(
            identifier="parent_{suffix}".format(suffix=self.randomString(10)),
            is_active=True,
            subject="subject {suffix}".format(suffix=self.randomString(10)),
            html_content=parent_html_content,
        )

        child_html_content = '''
        {% extends "layout" %}
        
        {% block content %}
            <h1>{{h1_title}}</h1>
            <p class="important">
              {{content}}
            </p>
        {% endblock %}
        '''

        self.child = MailTemplate.objects.create(
            identifier="id_{suffix}".format(suffix=self.randomString(10)),
            is_active=True,
            subject="subject {suffix}".format(suffix=self.randomString(10)),
            html_content=child_html_content,
            parent=parent,
            from_email='smarcet@gmail.com'
        )
        self.child.allowed_clients.add(client)


    def test_email_send(self):
        url = reverse('mail-endpoints:list-send')

        data = {
            'payload': {
                'title': 'this is the title',
                'h1_title': 'this is the subtitle',
                'content': 'this is the content',
                'footer': 'this is the footer'
            },
            'to_email': 'smarcet@gmail.com,sebastian@tipit.net',
            'template': self.child.id,
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
