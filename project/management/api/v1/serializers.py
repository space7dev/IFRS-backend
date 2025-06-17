from management.models import SiteConfiguration
from rest_framework import serializers

from gpt_integration.models import SystemPrompt


class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPrompt
        fields = ['id', 'prompt', 'is_active']


class SiteConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfiguration
        fields = [
            'bot_name',
            'greeting_message',
            'bot_style_bg_color',
            'bot_style_text_color',
            'human_style_bg_color',
            'human_style_text_color',
        ]
