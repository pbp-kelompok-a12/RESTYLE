from datetime import date

from django.utils import timezone
from rest_framework import serializers

from closet.models import ALL_YEAR, SEASON_OPTIONS, STYLE_OPTIONS, WEATHER_OPTIONS, Item
from restyle.image_processing import optimize_image_upload


class ClosetItemSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False, allow_empty_file=False)
    photo_url = serializers.SerializerMethodField()
    user = serializers.IntegerField(source="user_id", read_only=True)
    color_hex = serializers.CharField(read_only=True)

    class Meta:
        model = Item
        fields = [
            "id", "user", "photo", "photo_url", "name", "category", "color",
            "color_hex", "material", "styles", "seasons", "weather", "store",
            "purchase_link", "date_purchased", "price", "status", "created_at",
        ]
        read_only_fields = ["id", "user", "status", "created_at", "photo_url", "color_hex"]

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        try:
            return obj.photo.url
        except (ValueError, AttributeError):
            return None

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_date_purchased(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Purchase date can't be in the future.")
        return value

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Ensure this value is greater than or equal to 0.")
        return value

    def validate_styles(self, value):
        invalid = [item for item in value if item not in STYLE_OPTIONS]
        if invalid:
            raise serializers.ValidationError(f"Invalid style: {', '.join(invalid)}")
        return value

    def validate_seasons(self, value):
        invalid = [item for item in value if item not in SEASON_OPTIONS]
        if invalid:
            raise serializers.ValidationError(f"Invalid season: {', '.join(invalid)}")
        return [ALL_YEAR] if ALL_YEAR in value else value

    def validate_weather(self, value):
        invalid = [item for item in value if item not in WEATHER_OPTIONS]
        if invalid:
            raise serializers.ValidationError(f"Invalid weather: {', '.join(invalid)}")
        return value

    def validate_photo(self, photo):
        if photo.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("The photo must be 10 MB or smaller.")
        return optimize_image_upload(photo)

    def validate(self, attrs):
        if self.instance is None and not attrs.get("photo"):
            raise serializers.ValidationError({"photo": "Please upload a photo of your item."})
        return attrs
