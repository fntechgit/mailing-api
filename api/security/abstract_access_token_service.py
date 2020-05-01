from abc import abstractmethod


class AbstractAccessTokenService:

    @abstractmethod
    def validate(self, access_token:str):
        pass
