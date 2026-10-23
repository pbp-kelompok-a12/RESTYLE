from django.contrib import admin

from mixmatch.models import Outfit

@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    list_filter = ("user",)
    search_fields = ("name", "user__username")