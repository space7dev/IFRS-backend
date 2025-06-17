from django.urls import include, path

from .views import (
    ChatCreateAPIView,
    ChatDeleteAPIView,
    ChatDetailAPIView,
    ChatListAPIView,
    ChatMessageCreateAPIView,
    ChatMessageCreateStreamAPIView,
    ChatUpdateAPIView,
)

api_patterns = [
    path("chats/", include([
        path("", ChatListAPIView.as_view(), name='chat_list'),
        path("create/", ChatCreateAPIView.as_view(), name='chat_create'),
        path("<int:pk>/", include([
            path("detail/", ChatDetailAPIView.as_view(), name='chat_detail'),
            path("update/", ChatUpdateAPIView.as_view(), name='chat_update'),
            path("delete/", ChatDeleteAPIView.as_view(), name='chat_delete'),
            path("create-message/", ChatMessageCreateAPIView.as_view(),
                 name='chat_message_create'),
            path("create-message/stream/", ChatMessageCreateStreamAPIView.as_view(),
                 name='chat_message_create_stream'),
        ])),
    ])),
]
