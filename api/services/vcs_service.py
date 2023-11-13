from abc import abstractmethod


class VCSService:

    @abstractmethod
    def save_file(self, filename:str, content:str, commit_message:str = None):
        pass

    @abstractmethod
    def get_file_versions(self, filename:str):
        pass

    @abstractmethod
    def get_file_content_by_sha1(self, filename:str, sha1:str):
        pass

    def is_initialized(self) -> bool:
        return False
