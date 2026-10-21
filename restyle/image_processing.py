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
        # Closet uploads may already have been compressed in the browser to
        # fit production request limits. Avoid decoding and encoding them again.
        if source.format == "WEBP" and max(source.size) <= MAX_IMAGE_DIMENSION:
            upload.seek(0)
            return upload

        image = ImageOps.exif_transpose(source)
        # reducing_gap lets Pillow shrink very large phone photos in fewer
        # passes before the final high-quality resampling step.
        image.thumbnail(
            (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION),
            Image.Resampling.LANCZOS,
            reducing_gap=3.0,
        )

        # Keep alpha where present, otherwise use a compact 24-bit image.
        if "A" in image.getbands() or "transparency" in image.info:
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")

        output = BytesIO()
        # method=6 squeezes out a little more size at a much higher CPU cost.
        # method=4 is a better fit for synchronous web uploads.
        image.save(output, format="WEBP", quality=WEBP_QUALITY, method=4)

    output.seek(0)
    return ContentFile(output.read(), name=f"{Path(upload.name).stem}.webp")
