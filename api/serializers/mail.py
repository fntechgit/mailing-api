from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ValidationError

from . import TimestampField, ClientReadSerializer
from ..models import MailTemplate, Client, Mail
from ..utils import is_empty, JinjaRender, config


class MailReadSerializer(serializers.ModelSerializer):
    created = TimestampField()
    modified = TimestampField()

    class Meta:
        model = Mail
        fields = '__all__'


class MailWriteSerializer(serializers.ModelSerializer):
    pass