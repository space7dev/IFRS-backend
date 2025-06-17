from rest_framework import serializers

from gpt_integration.models import Chat, ChatMessage


class ChatSerializer(serializers.ModelSerializer):
    first_prompt = serializers.CharField(
        source='get_first_prompt', read_only=True)

    class Meta:
        model = Chat
        fields = [
            'id',
            'owner',
            'session_user_id',
            'title',
            'first_prompt',
            'messages',
            'created_on',
            'modified_on',
        ]
        depth = 1
        read_only = ["id", "owner", "session_user_id", "first_prompt",
                     "messages", "created_on", "modified_on"]


class ChatListSerializer(serializers.ModelSerializer):
    first_prompt = serializers.CharField(
        source='get_first_prompt', read_only=True)

    class Meta:
        model = Chat
        fields = [
            'id',
            'owner',
            'session_user_id',
            'title',
            'first_prompt',
            'created_on',
            'modified_on',
        ]


class ChatMessageCreateSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'chat',
            'prompt',
            'bot_response',
            'created_on',
            'modified_on',
        ]
