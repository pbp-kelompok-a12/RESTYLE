"""Normalize user-uploaded images before they reach the configured storage."""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


MAX_IMAGE_DIMENSION = 2000
WEBP_QUALITY = 82


def optimize_image_upload(upload):
    """Resize, strip metadata, and encode an uploaded image as WebP.

    WebP supports transparency, so transparent PNG garment photos keep their
    background. The returned ContentFile is suitable for any Django storage.
    """
    upload.seek(0)
    with Image.open(upload) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

        # Keep alpha where present, otherwise use a compact 24-bit image.
        if "A" in image.getbands() or "transparency" in image.info:
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")

        output = BytesIO()
        image.save(output, format="WEBP", quality=WEBP_QUALITY, method=6)

    output.seek(0)
    return ContentFile(output.read(), name=f"{Path(upload.name).stem}.webp")
