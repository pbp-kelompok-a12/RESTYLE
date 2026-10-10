from django import forms
from closet.models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name", "category", "color", "material", "status"]