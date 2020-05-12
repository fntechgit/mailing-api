from django.test import TestCase
from api.models import MailTemplate
from api.utils import JinjaRender


class TestRender(TestCase):
    fixtures = ["mailtemplates.json"]

    def test_render_1_need_details(self):
        template = MailTemplate.objects.get(pk=1)
        self.assertEqual(template.identifier, "REGISTRATION_INVITE_ATTENDEE_TICKET_EDITION")

        render = JinjaRender()
        payload = {
            'summit_name' : 'Test Summit',
            'order_owner_full_name': 'Sebastian Marcet',
            'edit_ticket_link': 'https://registration.test,com',
            'ticket_number': 'TICKET_NBR_1',
            'ticket_type_name': 'TICKET_TYPE_NAME',
            'owner_email': 'smarcet@gmail.com',
            'promo_code': '',
            'ticket_currency_symbol': '$',
            'ticket_amount': '1000.00',
            'ticket_currency': 'USD',
            'need_details': True,
            'support_email': 'support@test.com',
        }
        plain, html = render.render(template, payload, True)
        print(html)
        self.assertIn("Price: $1000.00 USD", html)
        self.assertIn("Additional Information Required to Issue Ticket", html)

        subject = render.render_subject(template, payload)

        self.assertIn("[Test Summit] You have been registered for Test Summit", subject)

    def test_render_2_need_details(self):
        template = MailTemplate.objects.get(pk=2)
        self.assertEqual(template.identifier, "REGISTRATION_REGISTERED_MEMBER_ORDER_PAID")

        render = JinjaRender()
        payload = {
            'summit_name': 'Test Summit',
            'order_owner_full_name': 'Sebastian Marcet',
            'edit_ticket_link': 'https://registration.test,com',
            'order_number': 'ORDER_NBR_1',
            'owner_email': 'smarcet@gmail.com',
            'owner_full_name': 'Sebastian Marcet',
            'promo_code': '',
            'order_currency_symbol': '$',
            'order_amount': '1000.00',
            'order_currency': 'USD',
            'tickets': [
                {
                    'ticket_type_name': 'TICKET_TYPE_NAME',
                    'has_owner': True,
                    'owner_email': 'smarcet@gmail.com',
                    'promo_code': {'code':'PROMO_1'},
                    'price': '1000.00',
                    'currency': 'USD',
                    'need_details': True,
                }
            ],
            'support_email': 'support@test.com',
            'manage_orders_url': 'https://registration.test.com/orders'
        }
        plain, html = render.render(template, payload, True)
        print(html)
        self.assertIn("Price: $1000.00 USD", html)
        self.assertIn("Additional Information Required to Issue Ticket", html)

        subject = render.render_subject(template, payload)

        self.assertIn("[Test Summit] Order Confirmation for Test Summit", subject)

    def test_render_2_unassigned(self):
        template = MailTemplate.objects.get(pk=2)
        self.assertEqual(template.identifier, "REGISTRATION_REGISTERED_MEMBER_ORDER_PAID")

        render = JinjaRender()
        payload = {
            'summit_name': 'Test Summit',
            'edit_ticket_link': 'https://registration.test,com',
            'order_number': 'ORDER_NBR_1',
            'owner_email': 'smarcet@gmail.com',
            'owner_full_name': 'Sebastian Marcet',
            'promo_code': '',
            'order_currency_symbol': '$',
            'order_amount': '1000.00',
            'order_currency': 'USD',
            'tickets': [
                {
                    'ticket_type_name': 'TICKET_TYPE_NAME',
                    'has_owner': False,
                    'owner_email': 'smarcet@gmail.com',
                    'promo_code': {'code':'PROMO_1'},
                    'price': '1000.00',
                    'currency': 'USD',
                    'need_details': True,
                }
            ],
            'support_email': 'support@test.com',
            'manage_orders_url': 'https://registration.test.com/orders'
        }
        plain, html = render.render(template, payload, True)
        print(html)
        self.assertIn("Price: $1000.00 USD", html)
        self.assertIn("Additional Information Required to Issue Ticket", html)
        self.assertIn("Attendee: UNASSIGNED", html)
        self.assertIn("PROMO_1", html)

        subject = render.render_subject(template, payload)

        self.assertIn("[Test Summit] Order Confirmation for Test Summit", subject)
