from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ValidationError
from . import TimestampField, ClientReadSerializer
from ..models import MailTemplate, Client
from ..utils import is_empty, JinjaRender
from ..services import VCSService
from django_injector import inject
from rest_framework.fields import empty


class MailTemplateReadSerializer(serializers.ModelSerializer):

    created = TimestampField()
    modified = TimestampField()

    parent = SerializerMethodField("get_parent_serializer")
    allowed_clients = SerializerMethodField("get_allowed_clients_serializer")
    versions = SerializerMethodField("get_versions_serializer")

    @inject
    def __init__(self, instance=None, data=empty, vcs_service:VCSService = None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.vcs_service = vcs_service

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

    def get_versions_serializer(self, obj):
        expand = self.get_expand()
        if 'versions' in expand:
            identifier = obj.identifier
            ext = 'html' if is_empty(obj.mjml_content) else 'mjml'

            if not self.vcs_service is None and self.vcs_service.is_initialized():
                filename = f'{identifier}.{ext}'

                commits = self.vcs_service.get_file_versions(filename)
                return [ {
                    'type': ext,
                    'sha': c.sha,
                    'html_url': c.html_url,
                    'last_modified' : c.last_modified,
                    'commit_message': c.commit.message,
                    'content': self.vcs_service.get_file_content_by_sha1(filename, c.sha)
                } for c in commits ]

        return []

    class Meta:
        model = MailTemplate
        fields = '__all__'


class MailTemplateWriteSerializer(serializers.ModelSerializer):

    created = TimestampField(read_only=True)
    modified = TimestampField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(many=False, queryset=MailTemplate.objects.all(), required=False, allow_null=True)
    allowed_clients = serializers.PrimaryKeyRelatedField(many=True, queryset=Client.objects.all(), required=False)
    versions = SerializerMethodField("get_versions_serializer")

    def get_current_user_name(self):
        request = self.context.get('request')
        token_info = request.auth
        current_user = f'{token_info["user_first_name"]} {token_info["user_last_name"]} ({token_info["user_email"]})' if 'user_identifier' in token_info else 'Anonymous User'
        return current_user

    @inject
    def __init__(self, instance=None, data=empty, vcs_service:VCSService = None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.vcs_service = vcs_service

    def create(self, validated_data):
        html_content = validated_data['html_content'] if 'html_content' in validated_data else None
        plain_content = validated_data['plain_content'] if 'plain_content' in validated_data else None
        mjml_content = validated_data['mjml_content'] if 'mjml_content' in validated_data else None
        identifier = validated_data['identifier'] if 'identifier' in validated_data else None

        has_content = not is_empty(html_content) or not is_empty(plain_content)
        parent = validated_data['parent'] if 'parent' in validated_data else None
        if 'is_active' not in validated_data:
            validated_data['is_active'] = False

        is_active = validated_data['is_active']

        if is_active and not has_content:
            raise ValidationError(_("If you activate the template at least should have a body content (HTML/PLAIN)."))
        if is_active and parent and not parent.is_active:
            raise ValidationError(_("If you activate the template, parent should be activated too."))
        file_content = html_content if is_empty(mjml_content) else mjml_content
        file_ext = "html" if is_empty(mjml_content) else "mjml"

        if not self.vcs_service is None and self.vcs_service.is_initialized():
            self.vcs_service.save_file(f'{identifier}.{file_ext}', file_content ,f'Added by {self.get_current_user_name() }')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        html_content = validated_data['html_content'] if 'html_content' in validated_data else None
        plain_content = validated_data['plain_content'] if 'plain_content' in validated_data else None
        identifier = validated_data['identifier'] if 'identifier' in validated_data else None
        has_content_for_update = not is_empty(html_content) or not is_empty(plain_content)
        has_content_on_db = not is_empty(instance.html_content) or not is_empty(instance.plain_content)
        is_active_for_update = validated_data['is_active'] if 'is_active' in validated_data else None
        mjml_content = validated_data['mjml_content'] if 'mjml_content' in validated_data else None

        file_content =  html_content if is_empty(mjml_content) else mjml_content
        file_ext = "html" if is_empty(mjml_content) else "mjml"

        if is_active_for_update and not has_content_for_update and not has_content_on_db:
            raise ValidationError(_("If you activate the template at least should have a body content (HTML/PLAIN)."))
        if not is_empty(identifier) and identifier != instance.identifier and instance.is_system:
            raise ValidationError(_("You can not change the identifier of a system template."))

        if not self.vcs_service is None and self.vcs_service.is_initialized():
            self.vcs_service.save_file(f'{identifier}.{file_ext}', file_content, f'Updated by {self.get_current_user_name()}')

        return super().update(instance, validated_data)

    def get_expand(self):
        request = self.context.get('request')
        str_expand = request.GET.get('expand', '') if request else None
        return str_expand.split(',') if str_expand else []

    def get_versions_serializer(self, obj):
        expand = self.get_expand()
        if 'versions' in expand:
            identifier = obj.identifier
            ext = 'html' if is_empty(obj.mjml_content) else 'mjml'

            if not self.vcs_service is None and self.vcs_service.is_initialized():
                filename = f'{identifier}.{ext}'

                commits = self.vcs_service.get_file_versions(filename)
                return [{
                    'type': ext,
                    'sha': c.sha,
                    'html_url': c.html_url,
                    'last_modified': c.last_modified,
                    'commit_message': c.commit.message,
                    'content': self.vcs_service.get_file_content_by_sha1(filename, c.sha)
                } for c in commits]

        return []

    def validate(self, data):
        from_email = data['from_email'] if 'from_email' in data else None
        identifier = data['identifier'] if 'identifier' in data else None
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

        is_update = self.instance is not None
        # validate parent ( parent should be a root , that is parent.parent_id = 0 )
        if parent and parent.has_parent :
            raise ValidationError(_("Parent should be a root on the hierarchy."))

        if is_empty(from_email) and not is_update:
            raise ValidationError(_("from_email is mandatory."))

        if is_empty(identifier) and not is_update:
            raise ValidationError(_("identifier is mandatory."))

        # enforce unique IDX
        query = MailTemplate.objects.filter(identifier=identifier)
        if is_update:
            query = query.filter(~Q(pk=self.instance.id))

        if query.count() > 0:
            raise ValidationError(_('Already exist an Email Template for that identifier.'))

        return data

    class Meta:
        model = MailTemplate
        fields = '__all__'
