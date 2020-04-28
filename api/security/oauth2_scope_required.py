import os

from django.utils.functional import wraps
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
import logging


def oauth2_scope_required(required_scope):
    """
      Decorator to make a view only accept particular scopes:
    """
    def decorator(func):
        @wraps(func)
        def inner(view, *args, **kwargs):

            request = view.request
            token_info = request.auth

            env = os.environ.get('ENV')
            # break validation on test
            if env == 'test' and token_info is None:
                return func(view, *args, **kwargs)

            if token_info is None:
                raise PermissionDenied(_("token info not present."))

            if 'scope' in token_info:
                current_scope = token_info['scope']

                logging.getLogger('oauth2').debug('current scope {current} required scope {required}'.
                                                  format(current=current_scope, required=required_scope))
                # check origins
                # check scopes

                if len(set.intersection(set(required_scope.split()), set(current_scope.split()))):
                    return func(view, *args, **kwargs)

            raise PermissionDenied(_("token scopes not present"))
        return inner
    return decorator
