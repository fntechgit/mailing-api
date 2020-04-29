import logging
import sys

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, GenericAPIView
from rest_framework.parsers import JSONParser
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from .exceptions import EntityNotFound
from ..models import MailTemplate, Client
from ..security import OAuth2Authentication, oauth2_scope_required
from ..serializers import MailTemplateReadSerializer, MailTemplateWriteSerializer
from ..utils import JinjaRender, config


class CustomClientSchema(AutoSchema):
    def _get_serializer(self, method, path):
        if method == 'GET':
            return MailTemplateReadSerializer()
        return MailTemplateWriteSerializer()

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


class MailTemplateFilter(FilterSet):
    class Meta:
        model = MailTemplate
        fields = {
            'subject': ['contains'],
            'identifier': ['contains'],
            'is_active': ['exact'],
            'locale': ['exact'],
            'from_email': ['contains'],
        }


class MailTemplateListCreateAPIView(ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MailTemplateFilter
    schema = CustomClientSchema()
    # ordering
    ordering_fields = ['id', 'created', 'updated', 'subject', 'identifier', 'is_active', 'max_retries', 'locale']
    ordering = ['id']
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return MailTemplate.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request is not None and self.request.method == 'POST':
            return MailTemplateWriteSerializer
        return MailTemplateReadSerializer

    @oauth2_scope_required()
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @oauth2_scope_required()
    def post(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailTemplateCreateAPIView::post')
            return self.create(request, *args, **kwargs)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MailTemplateRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)
    schema = CustomClientSchema()

    def get_queryset(self):
        pk = self.kwargs['pk'] if 'pk' in self.kwargs else 0
        if pk > 0:
            return MailTemplate.objects.get_queryset().filter(pk=pk).order_by('id')
        return MailTemplate.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request is not None and self.request.method == 'GET':
            return MailTemplateReadSerializer
        return MailTemplateWriteSerializer

    @oauth2_scope_required()
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @oauth2_scope_required()
    def put(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailTemplateRetrieveUpdateDestroyAPIView::put')
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
            logging.getLogger('api').debug('calling MailTemplateRetrieveUpdateDestroyAPIView::destroy')
            return self.destroy(request, *args, **kwargs)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RenderMailTemplateAPIView(GenericAPIView):
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)
    serializer_class = MailTemplateReadSerializer
    schema = CustomClientSchema()

    def get_queryset(self):
        return MailTemplate.objects.get_queryset().order_by('id')

    @oauth2_scope_required()
    def put(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailTemplateRetrieveUpdateDestroyAPIView::put')
            data = request.data
            instance = self.get_object()
            render = JinjaRender()
            plain, html = render.render(instance, data, True)
            return Response({'plain_content':plain, 'html_content': html }, status=status.HTTP_200_OK)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MailTemplateAllowedClientsAPIView(GenericAPIView):
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)
    renderer_classes = (StaticHTMLRenderer,)
    serializer_class = MailTemplateReadSerializer
    schema = CustomClientSchema()

    def get_queryset(self):
        return MailTemplate.objects.get_queryset().order_by('id')

    @oauth2_scope_required()
    def put(self,request, pk, client_id,  *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailTemplateAllowedClientsAPIView::put')
            template = MailTemplate.objects.filter(pk=pk).first()
            if not template:
                raise EntityNotFound()
            client = Client.objects.filter(pk=client_id).first()
            if not client:
                raise EntityNotFound()

            if template.is_allowed_client(client_id):
                raise ValidationError(
                    'client {client_id} already is allowed on template {pk}'.format(pk=pk, client_id=client_id))

            template.allowed_clients.add(client)

            template.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except EntityNotFound as e:
            logging.getLogger('api').warning(e)
            return Response('Entity not found.', status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @oauth2_scope_required()
    def delete(self, request, pk, client_id, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailTemplateAllowedClientsAPIView::delete')
            template = MailTemplate.objects.filter(pk=pk).first()
            if not template:
                raise EntityNotFound()
            client = Client.objects.get(pk=client_id)
            if not client:
                raise EntityNotFound()

            if not template.is_allowed_client(client_id):
                raise ValidationError(
                    'client {client_id} does not belong to allowed clients for template {pk}'.format(pk=pk, client_id=client_id))

            template.allowed_clients.remove(client)

            template.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except EntityNotFound as e:
            logging.getLogger('api').warning(e)
            return Response('Entity not found.', status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


