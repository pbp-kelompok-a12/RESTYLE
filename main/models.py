from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    style_persona = models.CharField(max_length=100, default="The Conscious Minimalist")
    preferred_style = models.CharField(max_length=50, blank=True)
    conscious_shopping_priority = models.CharField(max_length=50, blank=True)
    wardrobe_goal = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
