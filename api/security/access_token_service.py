import logging
import sys

import requests
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from .abstract_access_token_service import AbstractAccessTokenService
from ..utils import config


class AccessTokenService(AbstractAccessTokenService):

    def validate(self, access_token:str):
        """
              Authenticate the request, given the access token.
              """
        cached_token_info = None

        # try get access_token from DB and check if not expired
        cached_token_info = cache.get(access_token)

        if cached_token_info is None:
            try:
                response = requests.post(
                    '{base_url}/{endpoint}'.format
                        (
                        base_url=config('OAUTH2.IDP.BASE_URL', None),
                        endpoint=config('OAUTH2.IDP.INTROSPECTION_ENDPOINT', None)
                    ),
                    auth=(config('OAUTH2.CLIENT.ID', None), config('OAUTH2.CLIENT.SECRET', None),),
                    params={'token': access_token},
                    verify=config('DEBUG', False)
                )

                if response.status_code == requests.codes.ok:
                    cached_token_info = response.json()
                    cache.set(access_token, cached_token_info, timeout=cached_token_info['expires_in'])
                else:
                    logging.getLogger('oauth2').warning(
                        'http code {code} http content {content}'.format(code=response.status_code,
                                                                         content=response.content))
                    return None
            except requests.exceptions.RequestException as e:
                logging.getLogger('oauth2').error(e)
                return None
            except:
                logging.getLogger('oauth2').error(sys.exc_info())
                return None

        return AnonymousUser, cached_token_info