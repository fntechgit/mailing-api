import logging
import traceback
import datetime

from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from ..models import Mail
from ..security import OAuth2Authentication, oauth2_scope_required
from ..serializers import MailReadSerializer, MailWriteSerializer
from ..utils import config
from django.db.models import Q
from django_filters import FilterSet


class CustomClientSchema(AutoSchema):
    def _get_serializer(self, method, path):
        if method == 'GET':
            return MailReadSerializer()
        return MailWriteSerializer()

    def get_security(self, scopes):
        return {
            'OAuth2': scopes
        }

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        path = '/api{path}'.format(path=path)
        endpoints = config('OAUTH2.CLIENT.ENDPOINTS')
        method = str(method).lower()
        endpoint = endpoints[path] if path in endpoints else None
        endpoint = endpoint[method] if endpoint is not None and method in endpoint else None

        if endpoint:
            operation['operationId'] = str(endpoint['name'])
            operation['description'] = str(endpoint['desc'])
            operation['security'] = self.get_security(str(endpoint['scopes']))

        return operation


class MailFilter(FilterSet):
    is_sent = filters.BooleanFilter(method='filter_is_sent')
    term = filters.CharFilter(method='filter_term')
    from_sent_date = filters.NumberFilter(method='filter_from_sent_date')
    to_sent_date = filters.NumberFilter(method='filter_to_sent_date')

    class Meta:
        model = Mail
        fields = {
            'subject': ['contains'],
            'from_email': ['contains'],
            'to_email': ['contains'],
            'id': ['in'],
            'template__identifier': ['in'],
        }

    def filter_term(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(subject__icontains=value) | Q(to_email__icontains=value) | Q(template__identifier__icontains=value))
        return queryset

    def filter_is_sent(self, queryset, name, value):
        if value:
            return queryset.filter(sent_date__isnull=False)
        return queryset.filter(sent_date__isnull=True)

    def filter_from_sent_date(self, queryset, name, value):
        if value:
            return queryset.filter(sent_date__gte=datetime.datetime.utcfromtimestamp(int(value)))
        return queryset.filter()

    def filter_to_sent_date(self, queryset, name, value):
        if value:
            return queryset.filter(sent_date__lte=datetime.datetime.utcfromtimestamp(int(value)))
        return queryset.filter()


class MailListCreateAPIView(ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MailFilter
    schema = CustomClientSchema()
    # ordering
    ordering_fields = ['id', 'created', 'updated', 'subject', 'locale', 'sent_date']
    ordering = ['id']
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return Mail.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request is not None and self.request.method == 'POST':
            return MailWriteSerializer
        return MailReadSerializer

    # @oauth2_scope_required()
    def get(self, request, *args, **kwargs):
        logging.getLogger('api').debug('calling MailListCreateAPIView::get')
        return self.list(request, *args, **kwargs)

    @oauth2_scope_required()
    def post(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailListCreateAPIView::post')
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
            logging.getLogger('api').error(traceback.format_exc())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
