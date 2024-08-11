from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='replace_media_path')
def replace_media_path(value):
    """Replace the MEDIA_ROOT with MEDIA_URL in the image path."""
    if value.startswith(settings.MEDIA_ROOT):
        return value.replace(settings.MEDIA_ROOT, settings.MEDIA_URL, 1)
    return value

from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(str(key), 0)
