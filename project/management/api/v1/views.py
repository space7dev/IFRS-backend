from rest_framework import generics, permissions

from management.models import SiteConfiguration, get_site_config
from users.api.v1.permissions import IsAuthenticatedSuperuser

from .serializers import SiteConfigurationSerializer


class SiteConfigurationBaseAPIView(generics.GenericAPIView):
    """
    A base view for site configuration model.
    """
    queryset = get_site_config()
    serializer_class = SiteConfigurationSerializer
    permission_classes = [IsAuthenticatedSuperuser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # fixes swagger warns
            return SiteConfiguration.objects.none()
        return super().get_queryset()

    def get_object(self):
        # SiteConfiguration.get_solo() already returns single instance
        obj = self.get_queryset()
        self.check_object_permissions(self.request, obj)
        return obj


class SiteConfigurationUpdateAPIView(SiteConfigurationBaseAPIView, generics.UpdateAPIView):
    """
    A view for updating site configuration.
    """
    pass


class SiteConfigurationRetrieveAPIView(SiteConfigurationBaseAPIView, generics.RetrieveAPIView):
    """
    A view for retrieving site configuration.
    """
    permission_classes = [permissions.IsAuthenticated]
