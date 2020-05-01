from django_injector import inject
from rest_framework import exceptions
from rest_framework.authentication import get_authorization_header, BaseAuthentication

from .abstract_access_token_service import AbstractAccessTokenService


class OAuth2Authentication(BaseAuthentication):

    @inject
    def __init__(self, service:AbstractAccessTokenService):
        self.service = service

    def authenticate(self, request):

        auth = get_authorization_header(request).split()

        if len(auth) == 1:
            msg = 'Invalid bearer header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid bearer header. Token string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        if auth and auth[0].lower() == b'bearer':
            access_token = auth[1]
        elif 'access_token' in request.POST:
            access_token = request.POST['access_token']
        elif 'access_token' in request.GET:
            access_token = request.GET['access_token']
        else:
            return None

        return self.service.validate(access_token)
