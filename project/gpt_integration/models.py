from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction

from utils.models import TimeStampedMixin

User = get_user_model()


class Chat(TimeStampedMixin):
    owner = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="chats",
        related_query_name="chat",
        null=True,
        default=None
    )

    session_user_id = models.CharField(
        max_length=255,
        default=""
    )

    title = models.CharField(
        max_length=255,
        default=""
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(self.id)

    def get_first_prompt(self):
        first_msg = self.messages.first()
        return first_msg.prompt if first_msg else ""


class ChatMessage(TimeStampedMixin):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
        related_query_name="message",
        null=True,
        default=None
    )
    prompt = models.CharField(max_length=3000)
    bot_response = models.CharField(max_length=3000)

    def __str__(self):
        return f"{self.prompt[:30]}..."


class SystemPrompt(models.Model):
    prompt = models.TextField(max_length=2048)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.prompt[:30]}..."

    def save(self, *args, **kwargs):
        if not self.is_active:
            return super(SystemPrompt, self).save(*args, **kwargs)
        with transaction.atomic():
            SystemPrompt.objects.filter(is_active=True).update(is_active=False)
            return super(SystemPrompt, self).save(*args, **kwargs)
