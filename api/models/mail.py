from django.db import models
from model_utils.models import TimeStampedModel
from .mail_template import MailTemplate
from .client import Client


class Mail(TimeStampedModel):
    from_email = models.EmailField(blank=False)
    to_email = models.CharField(max_length=1024, blank=False)
    subject = models.CharField(max_length=256, blank=False)
    plain_content = models.TextField(blank=True, default='')
    html_content = models.TextField(blank=True, default='')
    sent_date = models.DateTimeField(null=True, )
    last_error = models.TextField(blank=True, default='')
    retries = models.IntegerField(default=0)
    next_retry_date = models.DateTimeField(null=True)

    # relations

    owner = models.ForeignKey(Client, on_delete=models.DO_NOTHING, null=False, blank=False)
    template = models.ForeignKey(MailTemplate, on_delete=models.DO_NOTHING, null=False, blank=False)
