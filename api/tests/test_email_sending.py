from django.test import TestCase
import json
import random
import string
from rest_framework.test import APITestCase
from api.models import MailTemplate, Client


class TestEmailSending(APITestCase):

    def randomString(self, str_len):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(str_len))

    def setUp(self):
        letters = string.ascii_lowercase
        client = None
        for i in range(10):
            client = Client.objects.create(client_id="OAUTH2_CLIENT_ID_{suffix}".format(suffix=self.randomString(10)))

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
            plain_content="content {suffix}".format(suffix=self.randomString(10)),
            html_content=parent_html_content,
        )

        child_html_content = '''
        {% extends "layout" %}
        
        {% block content %}
            <h1>{{title}}</h1>
            <p class="important">
              Welcome on my awsome homepage.
            </p>
        {% endblock %}
        '''

        for i in range(10):
            child = MailTemplate.objects.create(
                identifier="id_{suffix}".format(suffix=self.randomString(10)),
                is_active=True,
                subject="subject {suffix}".format(suffix=self.randomString(10)),
                plain_content="content {suffix}".format(suffix=self.randomString(10)),
                html_content=child_html_content,
                parent=parent
            )
            child.allowed_clients.add(client)
            # child.save()

    def test_email_send(self):
        pass

