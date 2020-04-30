from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from .models import MailTemplate, Client, Mail
# custom models
from .utils import config
from django.forms.widgets import DateTimeInput
admin.site.site_header = _('Mailing API Admin')


class MailTemplateForm(forms.ModelForm):
    html_content = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'ckeditor'})
    )

    locale = forms.ChoiceField(
        required=False,
        choices=list(config('SUPPORTED_LOCALES').items())
    )

    class Meta:
        model = MailTemplate
        fields = '__all__'

    def clean(self):
        identifier = self.cleaned_data.get('identifier')
        # enforce unique IDX
        pk = self.instance.id if not self.instance is None else 0
        if MailTemplate.objects.filter(identifier=identifier).filter(~Q(pk=pk)).count() > 0:
            raise ValidationError(_('Already exits that template identifier.'))

        return self.cleaned_data


class MailTemplateAdmin(admin.ModelAdmin):
    form = MailTemplateForm
    filter_horizontal = ['allowed_clients']

    my_id_for_formfield = None

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj:
            self.my_id_for_formfield = obj.id
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = MailTemplate.objects.all() if self.my_id_for_formfield is None else MailTemplate.objects.filter(~Q(pk=self.my_id_for_formfield ))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # https://docs.djangoproject.com/en/3.0/ref/contrib/admin/#modeladmin-asset-definitions
    class Media:
        # css fix for chkeditor
        # recall to run $ python manage.py  collectstatic
        css = {
            "all": ("admin/css/mail_template.css",)
        }
        js = ('//cdn.ckeditor.com/4.14.0/standard/ckeditor.js',)


class MailForm(forms.ModelForm):
    sent_date = forms.DateTimeField(
        required=False,
        widget=DateTimeInput(attrs={'type': 'datetime-local'}),
    )

    next_retry_date = forms.DateTimeField(
        required=False,
        widget=DateTimeInput(attrs={'type': 'datetime-local'}),
    )

    class Meta:
        model = Mail
        fields = '__all__'

    def clean(self):
        return self.cleaned_data


class MailAdmin(admin.ModelAdmin):
    form = MailForm


admin.site.register(MailTemplate, MailTemplateAdmin)
admin.site.register(Client)
admin.site.register(Mail, MailAdmin)