from rest_framework.schemas.openapi import SchemaGenerator
from api.utils import config


class MailingApiSchemaGenerator(SchemaGenerator):

    # Define all supported scopes in your OAuth security definition
    def get_oauth2_scopes(self):
        scopes = []
        endpoints = config('OAUTH2.CLIENT.ENDPOINTS')
        for path in endpoints:
            endpoint = endpoints[path]
            for verb in endpoint:
                scopes.append(endpoint[verb]['scopes'])
        return scopes

    # https://swagger.io/docs/specification/authentication/
    # https://swagger.io/docs/specification/authentication/oauth2/
    def get_security_schemes(self):
        return {'OAuth2': {
            'type': 'oauth2',
            'flows': {
                'implicit': {
                    'authorizationUrl': '',
                    'scopes': self.get_oauth2_scopes()
                }
            }
        }}

    def has_view_permissions(self, path, method, view):
        # api does not support PATCH
        if str(method).lower() == 'patch':
            return False
        return super().has_view_permissions(path, method, view)

    def get_components(self):
        return {
            'securitySchemes': self.get_security_schemes()
        }

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema['components'] = self.get_components()
        return schema
