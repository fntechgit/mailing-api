from injector import Module, singleton
from api.services.email_service import EmailService
from api.services.sendgrid_email_service import SendGridEmailService


# define here all root ioc bindings
class ApiAppModule(Module):
    def configure(self, binder):
        # services
        service = SendGridEmailService()
        binder.bind(EmailService, to=service, scope=singleton)
