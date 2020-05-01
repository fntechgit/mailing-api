from django.contrib.auth.models import AnonymousUser
from injector import Module, singleton

from api.models import Client
from api.security.abstract_access_token_service import AbstractAccessTokenService
from api.services.email_service import EmailService
from api.utils import config


class MockSendGridEmailService(EmailService):

    def process_pending_emails(self, batch: int) -> int:
        return 1


class MockAccessTokenService(AbstractAccessTokenService):

    def validate(self, access_token: str):
        scopes = []
        endpoints = config('OAUTH2.CLIENT.ENDPOINTS')
        for path in endpoints:
            endpoint = endpoints[path]
            for verb in endpoint:
                scopes.append(endpoint[verb]['scopes'])
        client = Client.objects.first();
        cached_token_info = {
            'scope' : " ".join(scopes),
        }

        if client:
            cached_token_info['client_id'] = client.client_id

        return AnonymousUser, cached_token_info


# define here all root ioc bindings
class TestApiAppModule(Module):
    def configure(self, binder):
        # services
        test_email_service = MockSendGridEmailService()
        binder.bind(EmailService, to=test_email_service, scope=singleton)

        test_access_token_service = MockAccessTokenService()
        binder.bind(AbstractAccessTokenService, to=test_access_token_service, scope=singleton)
