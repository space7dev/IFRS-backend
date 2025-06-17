from django.contrib import admin

from .models import Chat, ChatMessage, SystemPrompt

admin.site.register(
    [Chat, ChatMessage]
)


@admin.register(SystemPrompt)
class SystemPromptAdmin(admin.ModelAdmin):
    list_display = ["prompt", "is_active"]
