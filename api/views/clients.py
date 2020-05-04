import logging
import sys

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from ..models import Client
from ..security import OAuth2Authentication, oauth2_scope_required
from ..serializers import ClientReadSerializer, ClientWriteSerializer
from ..utils import config


class CustomClientSchema(AutoSchema):
    def _get_serializer(self, method, path):
        if method == 'GET':
            return ClientReadSerializer()
        return ClientWriteSerializer()

    def get_security(self, scopes):
        return {
            'OAuth2' : scopes
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


class ClientFilter(FilterSet):
    class Meta:
        model = Client
        fields = {
            'client_id': ['contains'],
            'name': ['contains'],
        }


class ClientListCreateAPIView(ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ClientFilter
    schema = CustomClientSchema()
    # ordering
    ordering_fields = ['id', 'created', 'updated', 'client_id', 'name']
    ordering = ['id']
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return Client.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request is not None and self.request.method == 'POST':
            return ClientWriteSerializer
        return ClientReadSerializer

    @oauth2_scope_required()
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @oauth2_scope_required()
    def post(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling ClientListCreateAPIView::post')
            return self.create(request, *args, **kwargs)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)
    schema = CustomClientSchema()

    def get_queryset(self):
        pk = self.kwargs['pk'] if 'pk' in self.kwargs else 0
        if pk > 0:
            return Client.objects.get_queryset().filter(pk=pk).order_by('id')
        return Client.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request is not None and self.request.method == 'GET':
            return ClientReadSerializer
        return ClientWriteSerializer

    @oauth2_scope_required()
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @oauth2_scope_required()
    def put(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling ClientRetrieveUpdateDestroyAPIView::put')
            return self.partial_update(request, *args, **kwargs)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        pass

    @oauth2_scope_required()
    def delete(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling ClientRetrieveUpdateDestroyAPIView::destroy')
            return self.destroy(request, *args, **kwargs)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
