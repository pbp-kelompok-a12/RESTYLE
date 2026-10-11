from django import forms
from django.utils import timezone
from closet.models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["photo", "name", "category", "color", "material", "status", "wash_days"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].required = True
        self.fields["photo"].error_messages["required"] = "Please upload a photo of your item."

    
    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean(self):
        data = super().clean()
        if data.get("status") == "washing":
            if not data.get("wash_days"):
                self.add_error("wash_days", "Enter how many days it will take to wash.")
        else:
            data["wash_days"] = None
        return data

    def save(self, commit=True):
        item = super().save(commit=False)
        if item.status == "washing":
            changed = "status" in self.changed_data or "wash_days" in self.changed_data
            if item.wash_started_at is None or changed:
                item.wash_started_at = timezone.now()
        else:
            item.wash_started_at = None
            item.wash_days = None
        if commit:
            item.save()
        return item