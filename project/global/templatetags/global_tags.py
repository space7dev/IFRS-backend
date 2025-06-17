from django import template
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

register = template.Library()


@register.simple_tag
def get_setting(key):
    return getattr(settings, key, None)


@register.simple_tag
def get_logo_path(url, request):
    current_site = get_current_site(request)
    return f"{current_site.domain}static/{url}"
