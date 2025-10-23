from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django import forms

from .models import AddOn, Review, TimeSlot, Venue


class FilterForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Cities",
        label="Location",
    )
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Categories",
        label="Category",
    )
    price = forms.DecimalField(
        required=False,
        label="Maximum Price",
        min_value=Decimal("0.00"),
    )

    def __init__(self, *args, **kwargs) -> None:
        city_qs = kwargs.pop("cities")
        category_qs = kwargs.pop("categories")
        super().__init__(*args, **kwargs)
        self.fields["location"].queryset = city_qs
        self.fields["category"].queryset = category_qs
        self.fields["location"].widget.attrs.update({"class": "select-input"})
        self.fields["category"].widget.attrs.update({"class": "select-input"})
        self.fields["price"].widget.attrs.update({"placeholder": "Rp", "class": "number-input", "min": "0", "step": "5000"})


class ReviewForm(forms.ModelForm):
    RATING_CHOICES: Iterable[tuple[int, str]] = [
        (5, "5 - Luar biasa"),
        (4, "4 - Sangat bagus"),
        (3, "3 - Bagus"),
        (2, "2 - Cukup"),
        (1, "1 - Kurang"),
    ]

    rating = forms.ChoiceField(choices=RATING_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Bagikan pengalamanmu..."}),
        }


class SlotSelectionForm(forms.Form):
    time_slot = forms.ModelChoiceField(queryset=TimeSlot.objects.none(), empty_label=None, widget=forms.RadioSelect)
    addons = forms.ModelMultipleChoiceField(
        queryset=AddOn.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, venue: Venue, date, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        available_slots = venue.time_slots.filter(date=date, is_booked=False).order_by("start_time")
        self.fields["time_slot"].queryset = available_slots
        self.fields["time_slot"].label_from_instance = (
            lambda slot: f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        )
        self.fields["addons"].queryset = venue.addons.all()
        self.fields["addons"].label_from_instance = (
            lambda addon: f"{addon.name} — Rp {addon.price:,.0f}".replace(",", ".")
        )
        if not venue.addons.exists():
            self.fields["addons"].widget = forms.MultipleHiddenInput()


class PaymentMethodForm(forms.Form):
    payment_method = forms.ChoiceField(
        label="Payment Method",
        choices=[
            ("", "Choose a method"),
            ("qris", "QRIS"),
            ("gopay", "GoPay"),
        ],
    )
