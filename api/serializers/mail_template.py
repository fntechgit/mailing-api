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

    created = TimestampField(read_only=True)
    modified = TimestampField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(many=False, queryset=MailTemplate.objects.all(), required=False, allow_null=True)
    allowed_clients = serializers.PrimaryKeyRelatedField(many=True, queryset=Client.objects.all(), required=False)

    def create(self, validated_data):
        html_content = validated_data['html_content'] if 'html_content' in validated_data else None
        plain_content = validated_data['plain_content'] if 'plain_content' in validated_data else None
        has_content = not is_empty(html_content) or not is_empty(plain_content)
        parent = validated_data['parent'] if 'parent' in validated_data else None
        if 'is_active' not in validated_data:
            validated_data['is_active'] = False

        is_active = validated_data['is_active']

        if is_active and not has_content:
            raise ValidationError(_("If you activate the template at least should have a body content (HTML/PLAIN)"))
        if is_active and parent and not parent.is_active:
            raise ValidationError(_("If you activate the template, parent should be activated too."))

        return super().create(validated_data)

    def update(self, instance, validated_data):
        html_content = validated_data['html_content'] if 'html_content' in validated_data else None
        plain_content = validated_data['plain_content'] if 'plain_content' in validated_data else None
        has_content_for_update = not is_empty(html_content) or not is_empty(plain_content)
        has_content_on_db = not is_empty(instance.html_content) or not is_empty(instance.plain_content)
        is_active_for_update = validated_data['is_active'] if 'is_active' in validated_data else None
        if is_active_for_update and not has_content_for_update and not has_content_on_db:
            raise ValidationError(_("If you activate the template at least should have a body content (HTML/PLAIN)"))
        return super().update(instance, validated_data)

    def validate(self, data):
        from_email = data['from_email'] if 'from_email' in data else None
        identifier = data['identifier'] if 'identifier' in data else None
        locale = data['locale'] if 'locale' in data else None
        parent = data['parent'] if 'parent' in data else None
        html_content = data['html_content'] if 'html_content' in data else None
        plain_content = data['plain_content'] if 'plain_content' in data else None

        # content validation
        render = JinjaRender()
        if not is_empty(plain_content):
            parent_content = parent.plain_content if parent else None
            render.validate(JinjaRender.build_dic(plain_content, parent_content))

        if not is_empty(html_content):
            parent_content = parent.html_content if parent else None
            render.validate(JinjaRender.build_dic(html_content, parent_content))

        if not is_empty(locale) and locale not in config('SUPPORTED_LOCALES'):
            raise ValidationError(_('locale {locale} not supported.'.format(locale=locale)))

        is_update = self.instance is not None
        # validate parent ( parent should be a root , that is parent.parent_id = 0 )
        if parent and parent.has_parent :
            raise ValidationError(_("Parent should be a root on the hierarchy."))

        if is_empty(from_email) and not is_update:
            raise ValidationError(_("from_email is mandatory."))

        if is_empty(identifier) and not is_update:
            raise ValidationError(_("identifier is mandatory."))

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
