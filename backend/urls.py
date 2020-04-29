"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from api.urls import private_urlpatterns as private_api_v1
from api.views import MailingApiSchemaGenerator

api_urlpatterns = [
    path('v1/',  include(private_api_v1)),
]

urlpatterns = [
    path('api/', include(api_urlpatterns)),
    path('admin', admin.site.urls),
    path('openapi', get_schema_view(
        generator_class=MailingApiSchemaGenerator,
        title="Mailing API",
        description="Mailing API",
        version="1.0.0",
        patterns=api_urlpatterns,
    ), name='openapi-schema'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
