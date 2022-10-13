from injector import Module, singleton

from api.security.abstract_access_token_service import AbstractAccessTokenService
from api.security.access_token_service import AccessTokenService
from api.services import MaintenanceService
from api.services.email_service import EmailService
from api.services.emails_maintenance_service import EmailsMaintenanceService
from api.services.sendgrid_email_service import SendGridEmailService


# define here all root ioc bindings
class ApiAppModule(Module):
    def configure(self, binder):
        # services
        email_service = SendGridEmailService()
        binder.bind(EmailService, to=email_service, scope=singleton)

        maintenance_service = EmailsMaintenanceService()
        binder.bind(MaintenanceService, to=maintenance_service, scope=singleton)

        access_token_service = AccessTokenService()
        binder.bind(AbstractAccessTokenService, to=access_token_service, scope=singleton)


