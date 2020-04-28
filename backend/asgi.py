"""
ASGI config for api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os
from dotenv import load_dotenv

from django.core.asgi import get_asgi_application

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
env = os.getenv('ENV')
filename = '.env'
if env:
    filename = '{filename}.{env}'.format(filename=filename, env=env)

ENV_FILE = os.path.join(CURRENT_PATH, filename)
load_dotenv(ENV_FILE)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_asgi_application()
