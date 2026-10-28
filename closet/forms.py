from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from closet.models import Item, ALL_YEAR, SEASON_OPTIONS, STYLE_OPTIONS, WEATHER_OPTIONS
from restyle.image_processing import optimize_image_upload

class ItemForm(forms.ModelForm):
    styles = forms.MultipleChoiceField(choices=[(s,s) for s in STYLE_OPTIONS], required=False, widget=forms.CheckboxSelectMultiple)
    seasons = forms.MultipleChoiceField(choices=[(s,s) for s in SEASON_OPTIONS], required=False, widget=forms.CheckboxSelectMultiple)
    weather = forms.MultipleChoiceField(choices=[(w,w) for w in WEATHER_OPTIONS], required=False, widget=forms.CheckboxSelectMultiple)
    price = forms.CharField(required=False)

    class Meta:
        model = Item
        fields = [
            "photo", "name", "category", "color", "material",
            "styles", "seasons", "weather",
            "store", "purchase_link", "date_purchased", "price",
        ]
        widgets = {
            "date_purchased": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].required = True
        self.fields["photo"].error_messages["required"] = "Please upload a photo of your item."

    
    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_date_purchased(self):
        bought = self.cleaned_data.get("date_purchased")
        if bought and bought > timezone.localdate():
            raise ValidationError("Purchase date can't be in the future.")
        return bought
    
    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo or not self.files.get(self.add_prefix("photo")):
            return photo
        if photo.size > 10 * 1024 * 1024:
            raise ValidationError("The photo must be 10 MB or smaller.")
        return optimize_image_upload(photo)

    def clean_seasons(self):
        seasons = self.cleaned_data["seasons"]
        return [ALL_YEAR] if ALL_YEAR in seasons else seasons

    def clean_price(self):
        raw = (self.cleaned_data.get("price") or "").replace(".", "").strip()
        if not raw:
            return None
        if not raw.isdigit():
            raise ValidationError("Enter a valid price.")
        return int(raw)
