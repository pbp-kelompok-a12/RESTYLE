from django import template
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from community.mentions import MENTION_RE, mentioned_users

register = template.Library()


@register.filter
def mentions(text):
    """ubah @username di tulisan jadi link ke profilnya (hanya untuk username yang ada).
    Tulisan di-escape dulu, jadi aman dipakai sebelum filter lain seperti linebreaks."""
    safe_text = escape(text or "")
    existing = {user.username for user in mentioned_users(text)}
    if not existing:
        return mark_safe(safe_text)

    def to_link(match):
        name = match.group(1).rstrip(".")
        trailing = match.group(1)[len(name):]  # titik di akhir kalimat tetap jadi teks biasa
        if name not in existing:
            return match.group(0)
        url = reverse("community:show_user_profile", args=[name])
        return format_html('<a class="cm-mention" href="{}">@{}</a>{}', url, name, trailing)

    return mark_safe(MENTION_RE.sub(to_link, safe_text))
