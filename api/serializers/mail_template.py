from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ValidationError

from . import TimestampField, ClientReadSerializer
from ..models import MailTemplate, Client
from ..utils import is_empty, JinjaRender, config


class MailTemplateReadSerializer(serializers.ModelSerializer):
    created = TimestampField()
    modified = TimestampField()

    parent = SerializerMethodField("get_parent_serializer")
    allowed_clients = SerializerMethodField("get_allowed_clients_serializer")

    def get_expand(self):
        request = self.context.get('request')
        str_expand = request.GET.get('expand', '') if request else None
        return str_expand.split(',') if str_expand else []

    def get_parent_serializer(self, obj):
        expand = self.get_expand()
        if not obj.parent_id:
            return None

        if 'parent' in expand:
            return MailTemplateReadSerializer(obj.parent, context=self.context).data
        return obj.parent_id

    def get_allowed_clients_serializer(self, obj):
        expand = self.get_expand()
        if 'allowed_clients' in expand:
            return ClientReadSerializer(obj.allowed_clients.all(), many=True, context=self.context)
        return [ x.id for x in obj.allowed_clients.all()]

    class Meta:
        model = MailTemplate
        fields = '__all__'


class MailTemplateWriteSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(many=False, queryset=MailTemplate.objects.all(), required=False, allow_null=True)
    allowed_clients = serializers.PrimaryKeyRelatedField(many=True, queryset=Client.objects.all(), required=False)

    def validate(self, data):
        identifier = data['identifier'] if 'identifier' in data else None
        locale = data['locale'] if 'locale' in data else None
        parent = data['parent'] if 'parent' in data else None
        html_content = data['html_content'] if 'html_content' in data else None

        if not is_empty(html_content):
            parent_content = parent.html_content if parent and parent.parent_id > 0 else None
            render = JinjaRender()
            render.validate(JinjaRender.build_dic(html_content, parent_content))

        if not is_empty(locale) and locale not in config('SUPPORTED_LOCALES'):
            raise ValidationError(_('locale {locale} not supported.'.format(locale=locale)))

        is_update = self.instance is not None
        # validate parent ( parent should be a root , that is parent.parent_id = 0 )
        if parent and parent.parent_id > 0:
            raise ValidationError(_("Parent should be a root on the hierarchy."))

        # enforce unique IDX
        query = MailTemplate.objects.filter(identifier=identifier).filter(locale=locale)
        if is_update:
            query = query.filter(~Q(pk=self.instance.id))

        if query.count() > 0:
            raise ValidationError(_('Already exist an Email Template identifer/locale combination.'))

        return data

    class Meta:
        model = MailTemplate
        fields = '__all__'
