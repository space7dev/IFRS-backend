from solo.models import SingletonModel

from django.db import models


class SiteConfiguration(SingletonModel):
    bot_name = models.CharField(
        max_length=255,
        default='Bot'
    )

    greeting_message = models.CharField(
        max_length=255,
        default="Hi, I'm here to help. What can I do for you today?"
    )

    bot_style_bg_color = models.CharField(
        max_length=255,
        default='#dbc3c3'
    )

    bot_style_text_color = models.CharField(
        max_length=255,
        default='#000000'
    )

    human_style_bg_color = models.CharField(
        max_length=255,
        default='#2590EB'
    )

    human_style_text_color = models.CharField(
        max_length=255,
        default='#ffffff'
    )

    def __str__(self):
        return "Site Configuration"

    class Meta:
        verbose_name = "Site Configuration"


def get_site_config():
    try:
        return SiteConfiguration.get_solo()
    except:
        return None
