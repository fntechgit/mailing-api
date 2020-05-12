from django.utils.translation import ugettext_lazy as _
from jinja2 import Environment, DictLoader, meta, TemplateSyntaxError
from rest_framework.serializers import ValidationError
import logging
from ..models import MailTemplate
from api.utils import Render
from api.utils.empty_str import is_empty


class JinjaRender(Render):

    INDEX_FILE = 'index'
    LAYOUT_FILE = 'layout'

    def __init__(self):
        self.env = None

    def validate(self, templates) -> str:
        self.env = Environment(loader=DictLoader(templates))
        # validate source
        # If you have incorrect syntax, you will get a TemplateSyntaxError
        template_source,_,_ = self.env.loader.get_source(self.env, JinjaRender.INDEX_FILE)
        template_source = template_source.replace("\\'", "'")
        parsed_content = self.env.parse(template_source)

        if JinjaRender.LAYOUT_FILE in templates:
            ref_templates = list(meta.find_referenced_templates(parsed_content))
            if JinjaRender.LAYOUT_FILE not in ref_templates:
                raise ValidationError(_("You need to define a {%- extends 'layout' %} block on your child template in "
                                        "order to use template inheritance."))

        return parsed_content

    @staticmethod
    def build_dic(content:str, parent_content:str) -> dict:
        templates = {
            JinjaRender.INDEX_FILE: content,
        }
        if not is_empty(parent_content):
            templates[JinjaRender.LAYOUT_FILE] = parent_content

        return templates

    def _render_content(self, content:str, parent_content:str, data: dict, validate_data: bool):

        parsed_content = self.validate(JinjaRender.build_dic(content, parent_content))
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

        return t.render(**data)

    def render_subject(self, mail_template: MailTemplate, data: dict) -> str:
        try:
            subject_content = mail_template.subject
            if not is_empty(subject_content):
                return self._render_content(subject_content, '', data, False)
            return subject_content
        except TemplateSyntaxError as e:
            logging.getLogger('api').warning(e)
            raise ValidationError(_("Invalid template syntax."))

    def render(self, mail_template: MailTemplate, data: dict, validate_data: bool) -> tuple:
        try:
            html_content = mail_template.html_content
            plain_content = mail_template.plain_content
            html_parent_content = None
            plain_parent_content = None

            if mail_template.has_parent:
                html_parent_content = mail_template.get_parent_html_content()
                plain_parent_content = mail_template.get_parent_plain_content()

            html_render = ''
            plain_render = ''
            has_content = False

            if not is_empty(html_content):
                has_content = True
                html_render = self._render_content(html_content, html_parent_content, data, validate_data)

            if not is_empty(plain_content):
                has_content = True
                plain_render = self._render_content(plain_content, plain_parent_content, data, validate_data)

            if not has_content:
                raise ValidationError(_("missing content (HTML or Plain)"))

            return plain_render, html_render
        except TemplateSyntaxError as e:
            logging.getLogger('api').warning(e)
            raise ValidationError(_("Invalid template syntax."))



