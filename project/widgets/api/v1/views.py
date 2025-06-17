from rest_framework import exceptions, generics
from widgets.api.v1.permissions import HasSessionUserIDHeader

from gpt_integration.api.v1.serializers import ChatListSerializer
from gpt_integration.api.v1.views import (
    ChatBaseAPIView,
    ChatCreateAPIView,
    ChatDeleteAPIView,
    ChatDetailAPIView,
    ChatListAPIView,
    ChatMessageCreateAPIView,
    ChatMessageCreateStreamAPIView,
    ChatUpdateAPIView,
)
from gpt_integration.models import Chat
from users.api.v1.permissions import IsAnonymous


class AnonymousChatBaseAPIView(ChatBaseAPIView):
    permission_classes = [IsAnonymous & HasSessionUserIDHeader]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # fixes swagger warns
            return Chat.objects.none()
        qs = super(ChatBaseAPIView, self).get_queryset()
        qs = qs.filter(
            session_user_id=self.request.headers.get('Session-User-ID'))
        return qs


class AnonymousChatListAPIView(AnonymousChatBaseAPIView, generics.ListAPIView):
    serializer_class = ChatListSerializer


class AnonymousChatUpdateAPIView(AnonymousChatBaseAPIView, generics.UpdateAPIView):
    pass


class AnonymousChatDetailAPIView(AnonymousChatBaseAPIView, generics.RetrieveAPIView):
    pass


class AnonymousChatDeleteAPIView(AnonymousChatBaseAPIView, generics.DestroyAPIView):
    pass


class AnonymousChatCreateAPIView(AnonymousChatBaseAPIView, generics.CreateAPIView):
    def perform_create(self, serializer):
        serializer.save(
            session_user_id=self.request.headers.get('Session-User-ID'))


class AnonymousChatMessageCreateAPIView(ChatMessageCreateAPIView):
    permission_classes = [IsAnonymous & HasSessionUserIDHeader]

    def get_object(self, pk):
        try:
            return Chat.objects.get(session_user_id=self.request.headers.get('Session-User-ID'), pk=pk)
        except Chat.DoesNotExist:
            raise exceptions.NotFound
