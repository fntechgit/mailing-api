from injector import Module, singleton

from api.security.abstract_access_token_service import AbstractAccessTokenService
from api.security.access_token_service import AccessTokenService
from api.services.email_service import EmailService
from api.services.sendgrid_email_service import SendGridEmailService
from api.services.vcs_service import VCSService
from api.services.github_service import GithubService


# define here all root ioc bindings
class ApiAppModule(Module):
    def configure(self, binder):
        # services
        email_service = SendGridEmailService()
        binder.bind(EmailService, to=email_service, scope=singleton)

        access_token_service = AccessTokenService()
        binder.bind(AbstractAccessTokenService, to=access_token_service, scope=singleton)

        vcs_service = GithubService()
        binder.bind(VCSService, to=vcs_service, scope=singleton)
