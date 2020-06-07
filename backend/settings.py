"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
ENV = os.getenv("ENV")
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False if ENV == 'production' else True

ALLOWED_HOSTS = ['*']

# https://github.com/sklarsa/django-sendgrid-v5
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"

FROM_EMAIL = os.getenv("FROM_EMAIL")
# https://docs.djangoproject.com/en/3.0/howto/error-reporting/
# string should have this format
# name1,email1|name2,email2|....|nameN,emailN
ADMINS = [tuple(x.split(',')) for x in os.getenv('ADMINS', []).split('|')]
# admin from email
SERVER_EMAIL = os.getenv('SERVER_EMAIL')
# Application definition

INSTALLED_APPS = [
    'rest_framework',
    'corsheaders',
    'model_utils',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'django_extensions',
    'django_injector',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_injector.middleware.inject_request_middleware',
]

# https://docs.djangoproject.com/en/3.0/ref/settings/#std:setting-ROOT_URLCONF
ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.getenv("DB_ENGINE"),
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
APPEND_SLASH = False

# file upload
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = (
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_LOCATION"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.getenv("REDIS_PASSWORD")
        },
        "KEY_PREFIX": "marketing_api"
    }
}

# https://docs.djangoproject.com/en/3.0/topics/logging/
# logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'console': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
        'file': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'filters': ['require_debug_true'],
        },
        'file': {
            'formatter': 'file',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "logs/api.log"),
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'email_backend': 'sendgrid_backend.SendgridBackend',
            'filters': ['require_debug_false'],
            'level': 'ERROR',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'mail_admins'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'api': {
            'handlers': ['file', 'mail_admins'],
            'level': os.getenv('API_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'serializers': {
            'handlers': ['file', 'mail_admins'],
            'level': os.getenv('API_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'oauth2': {
            'handlers': ['file', 'console'],
            'level': os.getenv('OAUTH2_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'jobs': {
            'handlers': ['file', 'console'],
            'level': os.getenv('CRON_JOBS_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'test': {
            'handlers': ['console'],
            'level': os.getenv('TEST_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
    },
}

DEFAULT_RENDERER_CLASSES = ['rest_framework.renderers.JSONRenderer']

if DEBUG:
    DEFAULT_RENDERER_CLASSES = [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': DEFAULT_RENDERER_CLASSES,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PERMISSION_CLASSES': [
        # default one
        'rest_framework.permissions.AllowAny',
    ],
    'SEARCH_PARAM': 'filter',
    'ORDERING_PARAM': 'order',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_PAGINATION_CLASS': 'api.utils.pagination.LargeResultsSetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/min',
        'user': '10000/min'
    }
}

# https://docs.djangoproject.com/en/3.0/ref/settings/
LOCALE_PATHS = [
    os.path.join(BASE_DIR, "api/locale")
]

DEFAULT_FILE_STORAGE = 'api.utils.storage.SwiftStorage'

OAUTH2 = {
    'IDP': {
        'BASE_URL': os.getenv('OAUTH2_IDP_BASE_URL'),
        'INTROSPECTION_ENDPOINT': os.getenv('OAUTH2_IDP_INTROSPECTION_ENDPOINT')
    },
    'CLIENT': {
        'ID': os.getenv('OAUTH2_CLIENT_ID'),
        'SECRET': os.getenv('OAUTH2_CLIENT_SECRET'),
        'ENDPOINTS': {
            # clients
            '/api/v1/clients': {
                'get': {
                    'name': _('GetAllClients'),
                    'desc': _('Get all Registered Clients'),
                    'scopes':os.getenv('OAUTH2_SCOPE_LIST_CLIENTS')
                },
                'post':{
                    'name': _('AddClient'),
                    'desc': _('Register Client'),
                    'scopes': os.getenv('OAUTH2_SCOPE_ADD_CLIENT'),
                }
            },
            '/api/v1/clients/{id}':{
                'get':{
                    'name': _('GetClientById'),
                    'desc': _('Get Client By Id'),
                    'scopes': os.getenv('OAUTH2_SCOPE_READ_CLIENT'),
                },
                'put': {
                    'name': _('UpdateClient'),
                    'desc': _('Update Client'),
                    'scopes': os.getenv('OAUTH2_SCOPE_UPDATE_CLIENT')
                },
                'delete': {
                    'name': _('DeleteClient'),
                    'desc': _('Delete Client'),
                    'scopes': os.getenv('OAUTH2_SCOPE_DELETE_CLIENT')
                },
            },
            # templates
            '/api/v1/mail-templates':{
                'get':{
                    'name': _('GetAllEmailTemplates'),
                    'desc': _('Get All Email Templates'),
                    'scopes': os.getenv('OAUTH2_SCOPE_LIST_TEMPLATES')
                },
                'post': {
                    'name': _('AddEmailTemplate'),
                    'desc': _('Create Email Template'),
                    'scopes': os.getenv('OAUTH2_SCOPE_ADD_TEMPLATE')
                },
            },
            '/api/v1/mail-templates/{id}':{
                'get':{
                    'name': _('GetEmailTemplateById'),
                    'desc': _('Get Email Template By Id'),
                    'scopes': os.getenv('OAUTH2_SCOPE_READ_TEMPLATE')
                },
                'put': {
                    'name': _('UpdateEmailTemplate'),
                    'desc': _('Update Email Template'),
                    'scopes': os.getenv('OAUTH2_SCOPE_UPDATE_TEMPLATE')
                },
                'delete': {
                    'name': _('DeleteEmailTemplate'),
                    'desc': _('Delete Email Template'),
                    'scopes': os.getenv('OAUTH2_SCOPE_DELETE_TEMPLATE')
                }
            },
            '/api/v1/mail-templates/{id}/render':{
                'put':{
                    'name': _('RenderEmailTemplate'),
                    'desc': _('Render Email Template'),
                    'scopes': os.getenv('OAUTH2_SCOPE_RENDER_TEMPLATE')
                }
            },
            '/api/v1/mail-templates/{id}/allowed-clients/{client_id}':{
                'put':{
                    'name': _('AddAllowedClientToEmailTemplate'),
                    'desc': _('Add Allowed Client to Email Template'),
                    'scopes': os.getenv('OAUTH2_SCOPE_TEMPLATE_ADD_ALLOWED_CLIENT')
                },
                'delete':{
                    'name': _('RemoveAllowedClientFromEmailTemplate'),
                    'desc': _('Remove Allowed Client from Email Template'),
                    'scopes': os.getenv('OAUTH2_SCOPE_TEMPLATE_DELETE_ALLOWED_CLIENT')
                }
            },
            # emails
            '/api/v1/mails': {
                'get': {
                    'name': _('GetAllEmails'),
                    'desc': _('Get All emails'),
                    'scopes': os.getenv('OAUTH2_SCOPE_LIST_EMAILS')
                },
                'post': {
                    'name': _('SendEmail'),
                    'desc': _('Send Email'),
                    'scopes': os.getenv('OAUTH2_SCOPE_SEND_EMAIL')
                },
            },
            '/api/v1/mails/sent': {
                'get': {
                    'name': _('GetAllSentEmails'),
                    'desc': _('Get All Sent emails'),
                    'scopes': os.getenv('OAUTH2_SCOPE_LIST_EMAILS')
                },
            }
        }
    }
}

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "backend/media"),
]

SUPPORTED_LOCALES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
}

INJECTOR_MODULES = ['api.ioc.ApiAppModule']

SEND_EMAILS_JOB_BATCH = os.getenv('SEND_EMAILS_JOB_BATCH', 10000)
DEV_EMAIL = os.getenv('DEV_EMAIL')