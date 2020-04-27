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

from ..models import MailTemplate
from ..security import OAuth2Authentication, oauth2_scope_required
from ..serializers import MailTemplateReadSerializer, MailTemplateWriteSerializer
from ..utils import config, JinjaRender


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
    # ordering
    ordering_fields = ['id', 'created', 'updated', 'subject', 'identifier', 'is_active', 'max_retries', 'locale']
    ordering = ['id']
    authentication_classes = [OAuth2Authentication]
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return MailTemplate.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return MailTemplateWriteSerializer
        return MailTemplateReadSerializer

    @oauth2_scope_required(required_scope=config('OAUTH2_SCOPE_LIST_TEMPLATES'))
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @oauth2_scope_required(required_scope=config('OAUTH2_SCOPE_ADD_TEMPLATE'))
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

    def get_queryset(self):
        pk = self.kwargs['pk'] if 'pk' in self.kwargs else 0
        if pk > 0:
            return MailTemplate.objects.get_queryset().filter(pk=pk).order_by('id')
        return MailTemplate.objects.get_queryset().order_by('id')

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'GET':
            return MailTemplateReadSerializer(
                expand=self.request.QUERY_PARAMS['expand'] if 'expand' in self.request.QUERY_PARAMS else None)
        return MailTemplateWriteSerializer

    @oauth2_scope_required(required_scope=config('OAUTH2_SCOPE_READ_TEMPLATE'))
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @oauth2_scope_required(required_scope=config('OAUTH2_SCOPE_UPDATE_TEMPLATE'))
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

    @oauth2_scope_required(required_scope=config('OAUTH2_SCOPE_DELETE_TEMPLATE'))
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
    renderer_classes = (StaticHTMLRenderer,)

    def get_queryset(self):
        return MailTemplate.objects.get_queryset().order_by('id')

    @oauth2_scope_required(required_scope=config('OAUTH2_SCOPE_RENDER_TEMPLATE'))
    def put(self, request, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling MailTemplateRetrieveUpdateDestroyAPIView::put')
            data = request.data
            instance = self.get_object()
            render = JinjaRender()
            html = render.render(instance, data, True)
            return Response(html, status=status.HTTP_200_OK)
        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(sys.exc_info())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


