from .clients import ClientListCreateAPIView, ClientRetrieveUpdateDestroyAPIView

from .mail_templates import MailTemplateListCreateAPIView, MailTemplateRetrieveUpdateDestroyAPIView, \
    RenderMailTemplateAPIView, MailTemplateAllowedClientsAPIView

from .mails import MailListCreateAPIView

from .openapi_schema import MailingApiSchemaGenerator
