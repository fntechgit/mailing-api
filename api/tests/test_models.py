from django.test import TestCase

from api.models import MailTemplate, Client


class TestModels(TestCase):

    def test_create_template_with_parent(self):
        parent_body = """
        {% block useless %}{% endblock %}
        """
        parent = MailTemplate.objects.create\
            (
                from_email='test@test.com', html_content=parent_body, is_active = True,
                identifier="1"
            )

        parent.save()
        child_body = """
          {%- extends 'layout.html' %}
           {% block useless %}
               {% for x in [1, 2, 3] %}
                   {% block testing scoped %}
                       {{ x }}
                   {% endblock %}
               {% endfor %}
           {% endblock %}
        """

        child = MailTemplate.objects.create(from_email='test@test.com', html_content=child_body, identifier="2", is_active = True, parent=parent)

        child.save()

        child_from_db = MailTemplate.objects.get(pk=child.id)
        self.assertEqual(child_from_db.parent_id, parent.id)
        self.assertTrue(child_from_db.parent)
        self.assertEqual(child_from_db.parent.html_content, parent_body)

    def test_create_client_permission(self):
        child_body = """
                 {%- extends 'layout.html' %}
                  {% block useless %}
                      {% for x in [1, 2, 3] %}
                          {% block testing scoped %}
                              {{ x }}
                          {% endblock %}
                      {% endfor %}
                  {% endblock %}
               """

        child = MailTemplate.objects.create(identifier="1", from_email='test@test.com', html_content=child_body, is_active=True)

        client = Client.objects.create(client_id="OAUTH2_CLIENT_ID")

        child.allowed_clients.add(client)

        child.save()

        self.assertTrue(child.allowed_clients.all().count() == 1)






