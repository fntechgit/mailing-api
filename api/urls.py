from django.urls import path, include
from .views import ClientRetrieveUpdateDestroyAPIView, ClientListCreateAPIView, \
    MailTemplateListCreateAPIView, MailTemplateRetrieveUpdateDestroyAPIView, RenderMailTemplateAPIView

client_patterns = ([
    path('', ClientListCreateAPIView.as_view(), name='list-create'),
    path('/<int:pk>', ClientRetrieveUpdateDestroyAPIView.as_view(), name='retrieve_update_destroy'),
], 'client-endpoints')

mail_template_patterns = ([
    path('', MailTemplateListCreateAPIView.as_view(), name='list-create'),
    path('/<int:pk>', MailTemplateRetrieveUpdateDestroyAPIView.as_view(), name='retrieve_update_destroy'),
    path('/<int:pk>/render', RenderMailTemplateAPIView.as_view(), name='render'),
], 'mail-template-endpoints')

private_urlpatterns = [
    path('clients', include(client_patterns)),
    path('mail-templates', include(mail_template_patterns)),
]
