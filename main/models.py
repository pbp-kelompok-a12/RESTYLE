from django.db import models
from django.contrib.auth.models import User

# Persona per jawaban "preferred style" di style quiz
PERSONAS = {
    "Minimal": (
        "The Conscious Minimalist",
        "Fewer, better pieces that work together in endless combinations. You keep your closet calm and your choices intentional.",
        "fa-leaf",
    ),
    "Casual": (
        "The Comfy Everyday Stylist",
        "Comfort comes first, and you know how to make easy pieces look put together. You rewear your favorites and love them longer.",
        "fa-mug-hot",
    ),
    "Vintage": (
        "The Thrift Treasure Hunter",
        "You give clothes a second life and find character in pre-loved pieces. Every outfit tells a story that fast fashion can't.",
        "fa-gem",
    ),
    "Bold": (
        "The Bold Trendsetter",
        "You love statement looks and fresh ideas. Restyling what you already own keeps your outfits exciting without the waste.",
        "fa-bolt",
    ),
}

# Label yang ditampilkan untuk tiap jawaban quiz
STYLE_LABELS = {
    "Minimal": "Minimal & Timeless",
    "Casual": "Casual & Comfy",
    "Vintage": "Thrifted & Vintage",
    "Bold": "Trendy & Bold",
}
PRIORITY_LABELS = {
    "Quality": "Long-lasting quality",
    "Versatility": "Easy to mix & match",
    "Eco": "Eco-friendly materials",
    "Ethical": "Ethical & fair trade",
}
GOAL_LABELS = {
    "Organize": "Organize my wardrobe",
    "Outfits": "Discover new outfit ideas",
    "SmartShop": "Buy less, shop smarter",
    "RefineStyle": "Refine my personal style",
}


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    style_persona = models.CharField(max_length=100, default="The Conscious Minimalist")
    preferred_style = models.CharField(max_length=50, blank=True)
    conscious_shopping_priority = models.CharField(max_length=50, blank=True)
    wardrobe_goal = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def persona(self):
        title, description, icon = PERSONAS.get(self.preferred_style, PERSONAS["Minimal"])
        return {"title": title, "description": description, "icon": icon}

    @property
    def quiz_answers(self):
        answers = [
            ("Style", STYLE_LABELS.get(self.preferred_style)),
            ("Priority", PRIORITY_LABELS.get(self.conscious_shopping_priority)),
            ("Goal", GOAL_LABELS.get(self.wardrobe_goal)),
        ]
        return [(label, value) for label, value in answers if value]


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    material = models.CharField(max_length=100, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    photo = models.ImageField(upload_to='wishlist_photos/', blank=True, null=True)
    style_tag = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"