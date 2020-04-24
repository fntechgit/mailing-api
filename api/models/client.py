from django.db import models
from model_utils.models import TimeStampedModel


class Client(TimeStampedModel):
    client_id = models.TextField(blank=False,unique=True)

    def __str__(self):
        return self.client_id
