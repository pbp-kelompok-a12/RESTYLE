from django import forms

from closet.models import Item, STYLE_OPTIONS
from mixmatch.models import Outfit, SLOTS, SLOT_CATEGORIES


class OutfitForm(forms.ModelForm):
    tags = forms.MultipleChoiceField(
        choices=[(s, s) for s in STYLE_OPTIONS],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Outfit
        fields = ["name", "notes", "tags", "top", "bottom", "shoes", "accessories", "outerwear", "dresses"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        mine = Item.objects.filter(user=user)
        for slot in SLOTS:
            self.fields[slot].queryset = mine.filter(category__in=SLOT_CATEGORIES[slot])
            self.fields[slot].required = False

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Give your outfit a name.")
        return name

    def clean(self):
        cleaned = super().clean()
        if not any(cleaned.get(slot) for slot in SLOTS):
            raise forms.ValidationError("Pick at least one piece from your closet.")
        return cleaned