from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
import re
from .client import Client


class MailTemplate(TimeStampedModel):

    from_email = models.CharField(max_length=254,blank=False, null=False)
    identifier = models.SlugField(blank=False, max_length=255, unique=True)
    # @see https://stackoverflow.com/questions/46554484/use-emoticon-in-subject-line-for-sendgrid-email
    # https://graphemica.com/%F0%9F%8E%89
    subject = models.CharField(max_length=256, blank=False, null=False)
    plain_content = models.TextField(blank=True, default='')
    html_content = models.TextField(blank=True, default='')
    # @see https://mjml.io/
    mjml_content = models.TextField(blank=True, default='')
    max_retries = models.IntegerField(default=1)
    is_active = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)

    @property
    def has_parent(self) -> bool:
        try:
            return self.parent_id > 0
        except:
            return False

    def get_parent_html_content(self) -> str:
        return self.parent.html_content if self.has_parent else None

    def get_parent_plain_content(self) -> str:
        return self.parent.plain_content if self.has_parent else None

    def save(self, *args, **kwargs):
        if not self.html_content is None:
            # fix for enclosing jinja2 blocks with p
            pattern = re.compile("<p>({%.*%})</p>")
            self.html_content = pattern.sub(r"\1", self.html_content)
        super().save(*args, **kwargs)

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

    # methods

    def is_allowed_client(self, client_id:int) -> bool:
        # if allowed clients is empty then is available for any
        # registered OAUTH2 client
        if self.allowed_clients.count() == 0:
            return True
        return self.allowed_clients.filter(id=client_id).count() > 0


