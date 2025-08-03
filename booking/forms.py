from django import forms

from .models import Room


class RoomForm(forms.ModelForm):
    """Form used for creating and updating rooms."""

    class Meta:
        model = Room
        fields = ["name", "capacity", "is_active", "color"]
        widgets = {
            "color": forms.TextInput(attrs={"type": "color"}),
        }

