from django.db import models
from model_utils.models import TimeStampedModel


class Client(TimeStampedModel):
    name = models.CharField(max_length=255, blank=False, unique=True)
    client_id = models.CharField(max_length=255,blank=False,unique=True)

    def __str__(self):
        return self.client_id
