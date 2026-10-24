from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Persona per jawaban "preferred style" di style quiz: (nama, deskripsi, ikon Font Awesome)
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

# Label yang ditampilkan untuk tiap jawaban quiz (sama dengan teks di halaman style quiz)
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
        """nama, deskripsi, dan ikon persona. Belum ikut quiz: pakai Conscious Minimalist."""
        title, description, icon = PERSONAS.get(self.preferred_style, PERSONAS["Minimal"])
        return {"title": title, "description": description, "icon": icon}

    @property
    def quiz_answers(self):
        """jawaban quiz yang sudah diisi, untuk ditampilkan sebagai chip: [(judul, isi), ...]"""
        answers = [
            ("Style", STYLE_LABELS.get(self.preferred_style)),
            ("Priority", PRIORITY_LABELS.get(self.conscious_shopping_priority)),
            ("Goal", GOAL_LABELS.get(self.wardrobe_goal)),
        ]
        return [(label, value) for label, value in answers if value]
