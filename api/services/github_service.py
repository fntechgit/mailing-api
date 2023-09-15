from github import Auth
from github import GithubIntegration, GithubException
import os
import base64
from api.services import VCSService
import logging


class GithubService(VCSService):
    def __init__(self):
        super().__init__()
        self.initialized = False
        try:
            # config values
            private_key = os.getenv('GITHUB_APP_PRIVATE_KEY', None)
            if private_key is None:
                raise Exception ('GithubService GITHUB_APP_PRIVATE_KEY is missing')

            app_id = os.getenv('GITHUB_APP_ID', None)
            if app_id is None:
                raise Exception('GithubService GITHUB_APP_ID is missing')

            repo_name = os.getenv("GITHUB_APP_REPO", None)
            if repo_name is None:
                raise Exception('GithubService GITHUB_APP_REPO is missing')

            # decode it from b64
            decoded_bytes = base64.b64decode(private_key)
            private_key = decoded_bytes.decode("utf-8")

            # we need app id and app pk on pem format ( app params)
            auth = Auth.AppAuth(app_id, private_key)
            self.gi = GithubIntegration(auth=auth)
            installation = self.gi.get_installations()[0]
            self.g = installation.get_github_for_installation()
            # we need repo info ( user name and repo name)
            self.repo = self.g.get_repo(repo_name)
            self.initialized = True
            logging.getLogger('vcs').debug('GithubService initialized')
        except GithubException as e:
            logging.getLogger('vcs').error(e)
        except Exception as e:
            logging.getLogger('vcs').error(e)

    def save_file(self, filename:str, content:str, commit_message:str = None):
        branch = os.getenv("GITHUB_APP_REPO_BRANCH", "main")
        exists = True
        contents = None
        try:
            contents = self.repo.get_contents(filename, ref=branch)
        except GithubException as e:
            print(e)
            exists = False
        if not exists:
            return self.repo.create_file(filename, commit_message, content, branch=branch)
        else:
            return self.repo.update_file(contents.path, commit_message, content, contents.sha, branch=branch)

    def get_file_versions(self, filename:str):
        try:
            return self.repo.get_commits(path=filename)
        except GithubException as e:
            logging.getLogger('vcs').error(e)
        return []

    def get_file_content_by_sha1(self, filename: str, sha1: str):
        try:
            contents = self.repo.get_contents(filename, ref=sha1)
            decoded_bytes = base64.b64decode(contents.content)
            return decoded_bytes.decode("utf-8")
        except GithubException as e:
            logging.getLogger('vcs').error(e)
        return None

    def is_initialized(self) -> bool:
        return self.initialized


