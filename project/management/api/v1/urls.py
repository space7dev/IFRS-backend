from django.urls import include, path

from .views import (
    SiteConfigurationRetrieveAPIView,
    SiteConfigurationUpdateAPIView,
)


api_patterns = [
    path("site-configuration/", include([
        path("", SiteConfigurationRetrieveAPIView.as_view(),
             name='site_configuration_view'),
        path("update/", SiteConfigurationUpdateAPIView.as_view(),
             name='site_configuration_update'),
    ])),
]
