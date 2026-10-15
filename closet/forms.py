from django import forms
from django.core.exceptions import ValidationError
from closet.models import Item, ALL_YEAR, SEASON_OPTIONS, STYLE_OPTIONS, WEATHER_OPTIONS

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