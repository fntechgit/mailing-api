from abc import abstractmethod

from api.models import MailTemplate


class Render:

    @abstractmethod
    def render(self, mail_template: MailTemplate, data: dict, validate_data: bool) -> str:
        pass
