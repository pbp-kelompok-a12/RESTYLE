from rest_framework import serializers

from closet.models import Item, STYLE_OPTIONS
from .models import Outfit, SLOTS, SLOT_CATEGORIES


class OutfitSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.ChoiceField(
            choices=STYLE_OPTIONS
        ),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Outfit
        fields = [
            "id",
            "name",
            "notes",
            "tags",
            "top",
            "bottom",
            "shoes",
            "accessories",
            "outerwear",
            "dresses",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        items = Item.objects.none()

        if request and request.user.is_authenticated:
            items = Item.objects.filter(user=request.user)

        for slot in SLOTS:
            queryset = items.filter(
                category__in=SLOT_CATEGORIES[slot]
            )

            if slot == "accessories":
                fields[slot].child_relation.queryset = queryset
            else:
                fields[slot].queryset = queryset

        return fields

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Give your outfit a name."
            )

        return value

    def validate(self, attrs):
        for slot in SLOTS:
            if slot in attrs:
                value = attrs[slot]
            elif self.instance is not None:
                value = getattr(self.instance, slot)

                if slot == "accessories":
                    value = value.all()
            else:
                value = None

            if value:
                return attrs

        raise serializers.ValidationError(
            "Pick at least one piece from your closet."
        )