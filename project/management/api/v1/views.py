import django_filters.rest_framework as drf_filters
from rest_framework import filters, generics, permissions, status, viewsets

from gpt_integration.api.v1.serializers import ChatSerializer
from gpt_integration.models import Chat, SystemPrompt
from management.models import get_site_config
from users.api.v1.permissions import IsAuthenticatedSuperuser

from .filters import ChatFilter
from .serializers import SiteConfigurationSerializer, SystemPromptSerializer


class SystemPromptAdminViewSet(viewsets.ModelViewSet):
    """
    A Admin only ViewSet for viewing and editing system prompts.
    """
    queryset = SystemPrompt.objects.all()
    serializer_class = SystemPromptSerializer
    permission_classes = [IsAuthenticatedSuperuser]


class ChatAdminViewSet(viewsets.ModelViewSet):
    """
    A Admin only ViewSet for viewing and editing chats.
    """
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticatedSuperuser]
    filter_backends = (drf_filters.DjangoFilterBackend, filters.SearchFilter)
    filterset_class = ChatFilter
    search_fields = [
        "owner__email",
        "owner__first_name",
        "owner__last_name",
        "owner__username"
    ]


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
