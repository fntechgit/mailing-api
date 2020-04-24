from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from .client import Client


class MailTemplate(TimeStampedModel):

    from_email = models.EmailField(blank=False)
    identifier = models.SlugField(blank=False, unique=True)
    subject = models.CharField(max_length = 256, blank=False)
    plain_content = models.TextField(blank=True, default='')
    html_content = models.TextField(blank=True, default='')
    max_retries = models.IntegerField(default=1)
    is_active = models.BooleanField(default=False)

    # relationships
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    allowed_clients = models.ManyToManyField(
        Client,
        verbose_name=_('Allowed Clients'),
        blank=True,
        help_text=_(
            'The clients that can send emails using this template.'
        ),
        related_name="allowed_clients",
        related_query_name="allowed_client",
    )


