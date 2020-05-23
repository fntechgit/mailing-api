from django.test import TestCase
from api.serializers import MailTemplateWriteSerializer
from api.models import MailTemplate


class TestSerializers(TestCase):

    def test_mail_template_serializer(self):
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
            'identifier' : 'identifier_1',
            'html_content' : html_content,
            'from_email' : 'test@test.com',
            'subject': 'test subject',
        }

        serializer = MailTemplateWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        template = MailTemplate.objects.get(identifier='identifier_1')

        self.assertTrue(template is not None)
        self.assertEqual(template.identifier, 'identifier_1')
        self.assertEqual(template.subject, 'test subject')
        self.assertEqual(template.from_email, 'test@test.com')