from django.conf import settings
from django.db import models

class Item(models.Model):
    CATEGORY_CHOICES = [
        ("top", "Top"),
        ("bottom", "Bottom"),
        ("shoes", "Shoes"),
        ("accessories", "Accessories"),
        ("outerwear", "Outerwear"),
        ("dresses", "Dresses")
    ]

    COLOR_CHOICES = [
        ("white", "White"),
        ("black","Black"),
        ("gray","Gray"),
        ("beige","Beige"),
        ("brown","Brown"),
        ("red","Red"),
        ("orange","Orange"),
        ("yellow","Yellow"),
        ("pink","Pink"),
        ("green","Green"),
        ("blue","Blue"),
        ("purple","Purple"),   
    ]

    COLOR_HEX = {
        "white": "#FFFFFF", "black": "#111111", "gray": "#9AA0A6", "beige": "#D9C3A0",
        "brown": "#944E18", "red": "#A6231B", "orange": "#E8893A", "yellow": "#F2D45C",
        "pink": "#E88AC0", "green": "#9CC24B", "blue": "#3375B5", "purple": "#9567DB",
    }

    MATERIAL_CHOICES = [
        ("cotton", "Cotton"),
        ("denim","Denim"),
        ("linen","Linen"),
        ("polyester","Polyester"),
        ("wool","Wool"),
        ("rayon","Rayon"),
        ("viscose","Viscose"),
        ("silk","Silk"),
        ("satin","Satin"),
        ("knit","Knit"),
        ("chiffon","Chiffon"),
        ("leather","Leather"),
    ]

    STATUS_CHOICES = [
        ("ready", "Ready to Wear"),
        ("washing", "In the Wash"),
    ]

    @property
    def color_hex(self):
        return self.COLOR_HEX.get(self.color, "#CCCCCC")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="closet_items",
    )

    photo = models.ImageField(upload_to="closet/items/", blank=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ready")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"
    