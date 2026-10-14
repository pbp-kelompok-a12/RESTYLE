from django import forms
from closet.models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["photo", "name", "category", "color", "material"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].required = True
        self.fields["photo"].error_messages["required"] = "Please upload a photo of your item."

    
    def clean_name(self):
        return self.cleaned_data["name"].strip()