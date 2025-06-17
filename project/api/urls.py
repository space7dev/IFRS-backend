from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from widgets.api.v1.urls import api_patterns as widgets_api_patterns

from django.urls import include, path

from gpt_integration.api.v1.urls import (
    api_patterns as gpt_integration_api_patterns,
)
from whisper_integration.api.v1.urls import (
    api_patterns as whisper_integration_api_patterns,
)
from management.api.v1.urls import api_patterns as management_api_patterns
from users.api.v1.urls import api_patterns as registration_api_patterns

# Documentation Schema settings for generating API Docs
schema_view = get_schema_view(
    openapi.Info(
        title="ChatGPT Scaffold API",
        default_version="v1",
        description="Base API to scaffold projects using a REST architecture",
        contact=openapi.Contact(email="info@ideamaker.agency"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("v1/", include(registration_api_patterns)),
    path(
        "v1/docs/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("v1/gpt-integration/", include(gpt_integration_api_patterns)),
    path("v1/whisper-integration/", include(whisper_integration_api_patterns)),
    path("v1/management/", include(management_api_patterns)),
    path("v1/widgets/", include(widgets_api_patterns)),
]
