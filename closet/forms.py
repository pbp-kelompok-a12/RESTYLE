from django import forms
from closet.models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["photo", "name", "category", "color", "material", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].required = True
        self.fields["photo"].error_messages["required"] = "Please upload a photo of your item."