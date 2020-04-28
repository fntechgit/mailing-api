import logging
import sys

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListCreateAPIView, GenericAPIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from .exceptions import EntityNotFound
from ..models import MailTemplate, Mail
from ..security import OAuth2Authentication, oauth2_scope_required
from ..serializers import MailReadSerializer, MailWriteSerializer
from ..utils import config


class MailFilter(FilterSet):
    class Meta:
        model = Mail
        fields = {
            'subject': ['contains'],
            'from_email': ['contains'],
            'to_email': ['contains'],
        }


class MailListCreateAPIView(ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MailFilter
    # ordering
    ordering_fields = ['id', 'created', 'updated', 'subject', 'locale']
    ordering = ['id']
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return MailTemplate.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return MailWriteSerializer
        return MailReadSerializer

    @oauth2_scope_required(required_scope=config('OAUTH2.CLIENT.SCOPES.LIST_EMAILS'))
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @oauth2_scope_required(required_scope=config('OAUTH2.CLIENT.SCOPES.SEND_EMAIL'))
    def post(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailTemplateCreateAPIView::post')
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            serializer = MailReadSerializer(instance)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
