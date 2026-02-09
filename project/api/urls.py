from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from django.urls import include, path

from management.api.v1.urls import api_patterns as management_api_patterns
from users.api.v1.urls import api_patterns as registration_api_patterns
from model_definitions.api.v1.urls import api_patterns as model_definitions_api_patterns

schema_view = get_schema_view(
    openapi.Info(
        title="IFRS Application API",
        default_version="v1",
        description="IFRS Model Definitions, Audit, and Reporting API",
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
    path("v1/management/", include(management_api_patterns)),
    path("v1/model-definitions/", include(model_definitions_api_patterns)),
]
