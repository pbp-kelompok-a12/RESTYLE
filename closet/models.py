from django.conf import settings
from django.db import models

STYLE_OPTIONS = ["Casual", "Formal", "Street", "Minimal", "Sporty", "Party", "Cozy", "Vintage"]
ALL_YEAR = "All year round"
SEASON_OPTIONS = ["Spring", "Summer", "Autumn", "Winter", ALL_YEAR]
WEATHER_OPTIONS = ["Hot", "Stormy", "Cool", "Moderate", "Rainy", "Drizzle", "Thunderstorm"]
MANUAL_STATUS_CATEGORIES = ("shoes", "accessories")

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

    styles = models.JSONField(default=list, blank=True)
    seasons = models.JSONField(default=list, blank=True)
    weather = models.JSONField(default=list, blank=True)

    store = models.CharField(max_length=80, blank=True)
    purchase_link = models.URLField(max_length=500, blank=True)
    date_purchased = models.DateField(null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True)

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

    def change_status(self):
        self.status = "washing" if self.status == "ready" else "ready"
        self.save(update_fields=["status"])
