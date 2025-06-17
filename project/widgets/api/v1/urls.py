from django.urls import include, path

from .views import (
    AnonymousChatCreateAPIView,
    AnonymousChatDeleteAPIView,
    AnonymousChatDetailAPIView,
    AnonymousChatListAPIView,
    AnonymousChatMessageCreateAPIView,
    AnonymousChatUpdateAPIView,
)

api_patterns = [
    path("chats/", include([
        path("", AnonymousChatListAPIView.as_view(), name='chat_list'),
        path("create/", AnonymousChatCreateAPIView.as_view(), name='chat_create'),
        path("<int:pk>/", include([
            path("detail/", AnonymousChatDetailAPIView.as_view(), name='chat_detail'),
            path("update/", AnonymousChatUpdateAPIView.as_view(), name='chat_update'),
            path("delete/", AnonymousChatDeleteAPIView.as_view(), name='chat_delete'),
            path("create-message/", AnonymousChatMessageCreateAPIView.as_view(),
                 name='chat_message_create'),
        ])),
    ])),
]
