from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from . import TimestampField
from ..models import Client
from ..utils import is_empty


class ClientReadSerializer(serializers.ModelSerializer):
    created = TimestampField()
    modified = TimestampField()

    class Meta:
        model = Client
        fields = '__all__'


class ClientWriteSerializer(serializers.ModelSerializer):
    created = TimestampField(read_only=True)
    modified = TimestampField(read_only=True)

    def validate(self, data):
        client_id = data['client_id'] if 'client_id' in data else None
        name = data['name'] if 'name' in data else None
        is_update = self.instance is not None

        # only mandatory on add
        if is_empty(client_id):
            raise ValidationError(_('Client Id is not set.'))

        if is_empty(name):
            raise ValidationError(_('Name is not set.'))

        # enforce unique IDX
        query = Client.objects.filter(client_id=client_id)
        if is_update:
            query = query.filter(~Q(pk=self.instance.id))

        if query.count() > 0:
            raise ValidationError(_('Already exist Client Id.'))

        query = Client.objects.filter(name=name)
        if is_update:
            query = query.filter(~Q(pk=self.instance.id))

        if query.count() > 0:
            raise ValidationError(_('Already exist Name'))

        return data

    class Meta:
        model = Client
        fields = '__all__'
