from __future__ import annotations

import datetime
from typing import Iterable, Optional

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import AddOn, Category, Review


BOOKING_TIME_SLOTS = (
    ("06:00-08:00", "06:00 - 08:00"),
    ("08:00-10:00", "08:00 - 10:00"),
    ("10:00-12:00", "10:00 - 12:00"),
    ("12:00-14:00", "12:00 - 14:00"),
    ("14:00-16:00", "14:00 - 16:00"),
    ("16:00-18:00", "16:00 - 18:00"),
    ("18:00-20:00", "18:00 - 20:00"),
)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class VenueFilterForm(forms.Form):
    city = forms.ChoiceField(label="City", required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)
    price = forms.ChoiceField(
        label="Price",
        required=False,
        choices=(
            ("", "Any price"),
            ("low", "≤ 150K"),
            ("mid", "150K – 300K"),
            ("high", "> 300K"),
        ),
    )

    def __init__(self, *, cities: Iterable[str], categories: Iterable[Category], data: Optional[dict] = None):
        super().__init__(data=data)
        unique_cities = {(city, city.title()) for city in cities if city}
        city_choices = [("", "All cities")] + sorted(unique_cities)
        self.fields["city"].choices = city_choices
        category_list = list(categories)
        self.fields["category"].queryset = Category.objects.filter(pk__in=[c.pk for c in category_list])
        self.fields["category"].empty_label = "All categories"


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Share your experience..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_class + " input-control").strip()


class BookingScheduleForm(forms.Form):
    date = forms.DateField(widget=forms.HiddenInput())
    time_slot = forms.ChoiceField(choices=BOOKING_TIME_SLOTS)
    addons = forms.ModelMultipleChoiceField(
        queryset=AddOn.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["addons"].queryset = AddOn.objects.all()

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < datetime.date.today():
            raise forms.ValidationError("Please select an upcoming date.")
        return date


class PaymentMethodForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=(
            ("", "Select a payment method"),
            ("qris", "QRIS"),
            ("gopay", "GoPay"),
        ),
        required=True,
    )
