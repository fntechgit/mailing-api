from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
import re
from .client import Client


class MailTemplate(TimeStampedModel):

    from_email = models.EmailField(blank=False, null=False)
    identifier = models.SlugField(blank=False, max_length=256)
    subject = models.CharField(max_length=256, blank=False, null=False)
    plain_content = models.TextField(blank=True, default='')
    html_content = models.TextField(blank=True, default='')
    max_retries = models.IntegerField(default=1)
    is_active = models.BooleanField(default=False)
    locale = models.CharField(max_length=2, default='en', blank=False)

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

    class Meta:
        unique_together = ('identifier', 'locale',)

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
        return self.allowed_clients.filter(id=client_id).count() > 0


