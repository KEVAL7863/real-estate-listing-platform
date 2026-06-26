from django import forms

from .models import Property


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "title", "description", "property_type", "listing_type",
            "price", "area_sqft", "bedrooms", "bathrooms",
            "address", "city", "state", "pincode",
            "has_parking", "is_furnished",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "property_type": forms.Select(attrs={"class": "form-select"}),
            "listing_type": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "area_sqft": forms.NumberInput(attrs={"class": "form-control"}),
            "bedrooms": forms.NumberInput(attrs={"class": "form-control"}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "pincode": forms.TextInput(attrs={"class": "form-control"}),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ImageUploadForm(forms.Form):
    images = forms.FileField(
        widget=MultipleFileInput(attrs={"class": "form-control", "multiple": True}),
        required=False,
        label="Upload property images",
    )
