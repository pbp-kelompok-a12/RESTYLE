from django.conf import settings
from django.db import models

SLOTS = ("top", "bottom", "shoes", "accessories", "outerwear", "dresses")
SLOT_LABELS = {
    "top": "Top",
    "bottom": "Bottom",
    "shoes": "Shoes",
    "accessories": "Accessories",
    "outerwear": "Outerwear",
    "dresses": "Dresses",
}

SLOT_CATEGORIES = {slot: [slot] for slot in SLOTS}

def slot_for_category(category):
    for slot, categories in SLOT_CATEGORIES.items():
        if category in categories:
            return slot
    return ""

class Outfit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="outfits",
    )

    name = models.CharField(max_length=100)
    notes = models.TextField(max_length=500, blank=True)
    tags = models.JSONField(default=list, blank=True)  # sama kayak Item.styles

    top = models.ForeignKey("closet.Item", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    bottom = models.ForeignKey("closet.Item", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    shoes = models.ForeignKey("closet.Item", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    accessories = models.ManyToManyField("closet.Item", blank=True, related_name="outfits_with_accessory")
    outerwear = models.ForeignKey("closet.Item", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    dresses = models.ForeignKey("closet.Item", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def pieces(self):
        pieces = []

        for slot in SLOTS:
            value = getattr(self, slot)

            if slot == "accessories":
                pieces.extend(value.all())
            elif value is not None:
                pieces.append(value)

        return pieces


    @property
    def slot_pieces(self):
        result = []

        for slot in SLOTS:
            value = getattr(self, slot)

            if slot == "accessories":
                result.extend(
                    (slot, item)
                    for item in value.all()
                )
            elif value is not None:
                result.append((slot, value))

        return result