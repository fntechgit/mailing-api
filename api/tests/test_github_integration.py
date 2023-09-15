from django.test import TestCase
from api.services.github_service import GithubService


class TestGitHubIntegration(TestCase):

    def setUp(self):
        pass

    def test_connect(self):
        service = GithubService()

        res = service.save_file("another.html", "test" ,"test comment")
        self.assertTrue(not res is None)

        commits = service.get_file_versions("another.html")
        self.assertTrue(not commits is None)
        for c in commits:
            print(c.sha)
            print(c.html_url)
            print(c.last_modified)
            print(c.commit.message)
            content = service.get_file_content_by_sha1("another.html", c.sha)
            print(content)



