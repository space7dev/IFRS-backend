from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    ChatAdminViewSet,
    SiteConfigurationRetrieveAPIView,
    SiteConfigurationUpdateAPIView,
    SystemPromptAdminViewSet,
)

admin_router = DefaultRouter()
admin_router.register("system-prompts", SystemPromptAdminViewSet)
admin_router.register("chats", ChatAdminViewSet)


api_patterns = [
    path("", include(admin_router.urls)),
    path("site-configuration/", include([
        path("", SiteConfigurationRetrieveAPIView.as_view(),
             name='site_configuration_view'),
        path("update/", SiteConfigurationUpdateAPIView.as_view(),
             name='site_configuration_update'),
    ])),
]
