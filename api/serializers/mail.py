import logging

from django.core.validators import EmailValidator
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ValidationError

from . import MailTemplateReadSerializer
from . import TimestampField
from ..models import MailTemplate, Client, Mail
from ..utils import is_empty, JinjaRender


class MailReadSerializer(serializers.ModelSerializer):
    created = TimestampField()
    modified = TimestampField()
    template = SerializerMethodField("get_template_serializer")

    def get_template_serializer(self, obj):
        expand = self.get_expand()
        if not obj.template_id:
            return None

        if 'template' in expand:
            return MailTemplateReadSerializer(obj.template, context=self.context).data
        return obj.template_id

    def get_expand(self):
        request = self.context.get('request')
        str_expand = request.GET.get('expand', '') if request else None
        return str_expand.split(',') if str_expand else []

    class Meta:
        model = Mail
        fields = '__all__'


class MailWriteSerializer(serializers.ModelSerializer):

    template = serializers.SlugRelatedField(many=False,
                                            queryset=MailTemplate.objects.all(),
                                            required=True,
                                            slug_field='identifier',
                                            allow_null=False)
    payload = serializers.JSONField()
    subject = serializers.CharField(required=False)
    created = TimestampField(read_only=True)
    modified = TimestampField(read_only=True)

    def get_current_client_id(self):
        request = self.context.get('request')
        token_info = request.auth
        return token_info['client_id'] if token_info is not None and 'client_id' in token_info else None

    def get_owner(self):
        client_id = self.get_current_client_id()
        if is_empty(client_id):
            raise ValidationError(_('missing client id.'))

        client = Client.objects.filter(client_id=client_id).first()
        if client is None:
            raise ValidationError(_('client {client_id} is not registered.'.format(client_id=client_id)))

        return client

    def validate(self, data):
        validate_email = EmailValidator()
        to_email = data['to_email'] if 'to_email' in data else None
        subject = data['subject'] if 'subject' in data else None

        owner = self.get_owner()
        if owner is None:
            raise ValidationError(_("owner is mandatory."))

        template = data['template'] if 'template' in data else None

        if is_empty(to_email):
            raise ValidationError(_("to_email is mandatory."))

        # validate if its a list of emails
        for r in to_email.split(','):
            validate_email(r)

        if template is None:
            raise ValidationError(_("template is mandatory."))

        if not template.is_active:
            raise ValidationError(_("template is not active."))

        if not template.is_allowed_client(owner.id):
            raise ValidationError(_(
                "client {client_id} is not allowed to send emails template of type {type_id}.".format(client_id=owner.id,
                                                                                                     type_id=template.id)))
        data['owner'] = owner

        if is_empty(subject):
            data['subject'] = template.subject

        return data

    def create(self, validated_data):
        payload = validated_data['payload'] if 'payload' in validated_data else []
        render = JinjaRender()
        instance = Mail(**validated_data)
        plain, html = render.render(instance.template, payload, True)
        instance.html_content = html
        instance.plain_content = plain
        instance.from_email = instance.template.from_email

        if is_empty(instance.from_email):
            raise ValidationError(_("from_email is mandatory."))

        if is_empty(instance.subject):
            raise ValidationError(_("subject is mandatory."))

        if is_empty(instance.plain_content) and is_empty(instance.html_content):
            raise ValidationError(_("content is mandatory (HTML/PLAIN)."))

        instance.subject = render.render_subject(instance.subject, payload)
        instance.save()

        logging.getLogger('serializers').debug('MailWriteSerializer.create plain_content {plain_content} html_content '
                                               '{html_content}'.format(plain_content=plain, html_content=html))
        return instance

    class Meta:
        model = Mail
        fields = ['created', 'modified', 'to_email', 'template', 'payload', 'subject']
        read_only_fields = ['html_content', 'plain_content']
