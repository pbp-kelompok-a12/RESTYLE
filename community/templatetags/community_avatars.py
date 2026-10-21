from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def avatar(user):
    """isi lingkaran avatar: foto profil kalau ada, kalau tidak huruf pertama username."""
    profile = getattr(user, "community_profile", None)
    if profile and profile.photo:
        return format_html('<img class="avatar-photo" src="{}" alt="">', profile.photo.url)
    return (user.username[:1] or "?").upper()