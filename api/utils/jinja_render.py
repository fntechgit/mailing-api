from django.utils.translation import ugettext_lazy as _
from jinja2 import Environment, DictLoader, meta
from rest_framework.serializers import ValidationError

from ..models import MailTemplate
from api.utils import Render
from api.utils.empty_str import is_empty

class JinjaRender(Render):

    INDEX_FILE = 'index.html'
    LAYOUT_FILE = 'layout.html'

    def __init__(self):
        self.env = None

    def validate(self, templates) -> str:
        self.env = Environment(loader=DictLoader(templates))
        # validate source
        # If you have incorrect syntax, you will get a TemplateSyntaxError
        template_source = self.env.loader.get_source(self.env, JinjaRender.INDEX_FILE)
        parsed_content = self.env.parse(template_source)

        if JinjaRender.LAYOUT_FILE in templates:
            ref_templates = list(meta.find_referenced_templates(parsed_content))
            if JinjaRender.LAYOUT_FILE not in ref_templates:
                raise ValidationError(_("You need to define a {%- extends 'layout.html' %} on your child template."))

        return parsed_content

    @staticmethod
    def build_dic(content:str, parent_content:str) -> dict:
        templates = {
            JinjaRender.INDEX_FILE: content,
        }
        if not is_empty(parent_content):
            templates[JinjaRender.LAYOUT_FILE] = parent_content

        return templates

    def render(self, mail_template: MailTemplate, data: dict, validate_data: bool) -> str:
        html_content = mail_template.html_content
        html_parent_content = None

        if is_empty(html_content):
            raise ValidationError(_("missing HTML content"))

        if mail_template.has_parent > 0 and is_empty(mail_template.parent.html_content):
            html_parent_content = mail_template.get_parent_html_content()

        parsed_content = self.validate(JinjaRender.build_dic(html_content, html_parent_content))
        t = self.env.get_template(JinjaRender.INDEX_FILE)

        if validate_data:
            # This will yield list of undeclared variables since this is not executed
            # at run time, it will yield list of all variables.
            # Note: This will yield html files which are included using include and
            # extends.
            t_vars = meta.find_undeclared_variables(parsed_content)
            for tk in t_vars:
                # check if template vars have their counterpart on data
                if tk not in data.keys():
                    raise ValidationError(_("Missing template defined variable '{tk}'.".format(tk=tk)))

        r = t.render(**data)

        return r


