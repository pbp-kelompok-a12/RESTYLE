"""Menemukan @username di tulisan post / reply.
Dipakai untuk notifikasi (views.py) dan untuk mengubah @username jadi link (templatetags)."""

import re

from django.contrib.auth import get_user_model

# @ yang tidak didahului huruf/angka (supaya alamat email seperti a@b.com tidak ikut),
# lalu karakter username Django selain @: huruf, angka, dan . + - _
MENTION_RE = re.compile(r"(?<![\w@])@([\w.+-]+)")


def mentioned_names(text):
    """semua username yang disebut, tanpa titik di akhir (misalnya '@alsa.' di akhir kalimat)."""
    return {name.rstrip(".") for name in MENTION_RE.findall(text or "") if name.rstrip(".")}


def mentioned_users(text):
    """user yang benar-benar ada untuk setiap @username di tulisan."""
    names = mentioned_names(text)
    if not names:
        return get_user_model().objects.none()
    return get_user_model().objects.filter(username__in=names)
