from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions, generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse

from gpt_integration.helpers import build_messages
from gpt_integration.integration import GptIntegration
from gpt_integration.models import Chat, ChatMessage

from .renderers import ServerSentEventRenderer
from .serializers import (
    ChatListSerializer,
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ChatSerializer,
)

User = get_user_model()


class ChatBaseAPIView(generics.GenericAPIView):
    queryset = Chat.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # fixes swagger warns
            return Chat.objects.none()
        qs = super().get_queryset()
        qs = qs.filter(owner=self.request.user)
        return qs


class ChatListAPIView(ChatBaseAPIView, generics.ListAPIView):
    serializer_class = ChatListSerializer


class ChatUpdateAPIView(ChatBaseAPIView, generics.UpdateAPIView):
    pass


class ChatDetailAPIView(ChatBaseAPIView, generics.RetrieveAPIView):
    pass


class ChatDeleteAPIView(ChatBaseAPIView, generics.DestroyAPIView):
    pass


class ChatCreateAPIView(ChatBaseAPIView, generics.CreateAPIView):
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ChatMessageCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Chat.objects.get(owner=self.request.user, pk=pk)
        except Chat.DoesNotExist:
            raise exceptions.NotFound

    @swagger_auto_schema(
        request_body=ChatMessageCreateSerializer,
        responses={200: ChatMessageSerializer}
    )
    def post(self, request, pk, format=None):
        chat = self.get_object(pk)
        serializer = ChatMessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data.get("prompt")
            messages = build_messages(chat, prompt)
            gpt = GptIntegration()
            bot_response = gpt.get_chat_completion(messages)
            new_message = ChatMessage.objects.create(
                chat=chat,
                prompt=prompt,
                bot_response=bot_response
            )
            message_serializer = ChatMessageSerializer(new_message)
            return Response(message_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatMessageCreateStreamAPIView(ChatMessageCreateAPIView):
    """
    View that returns Streaming HTTP Response
    """

    @swagger_auto_schema(
        request_body=ChatMessageCreateSerializer,
        responses={200: ""}
    )
    def post(self, request, pk, format=None):
        chat = self.get_object(pk)
        serializer = ChatMessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data.get("prompt")
            messages = build_messages(chat, prompt)
            gpt = GptIntegration()
            response = StreamingHttpResponse(gpt.get_chat_completion_stream(
                chat, prompt, messages), content_type="text/event-stream")
            # Set SSE Renderer only for our stream response
            self.renderer_classes = [ServerSentEventRenderer]
            response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
            # Ensure clients don't cache the data
            response['Cache-Control'] = 'no-cache'
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
