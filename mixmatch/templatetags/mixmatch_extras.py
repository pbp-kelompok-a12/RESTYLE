import os
import re

from django import template

register = template.Library()

CLOUDINARY_UPLOAD = re.compile(r"^(https?://res\.cloudinary\.com/[^/]+/image/upload/)(.+)$")
IMAGE_EXTENSION = re.compile(r"\.(jpe?g|png|webp|gif|avif|heic)$", re.IGNORECASE)

def cutout_enabled():
    return os.environ.get("MIXMATCH_AUTO_CUTOUT", "").strip().lower() in ("1", "true", "yes")


@register.filter
def cutout(url):
    if not url or not cutout_enabled():
        return url
    match = CLOUDINARY_UPLOAD.match(url)
    if not match or "e_background_removal" in url:
        return url
    prefix, rest = match.groups()
    rest = IMAGE_EXTENSION.sub("", rest) + ".png"
    return f"{prefix}e_background_removal/{rest}"