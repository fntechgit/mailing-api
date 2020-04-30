from abc import abstractmethod


class EmailService:

    @abstractmethod
    def process_pending_emails(self, batch:int) -> int:
        pass
