from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Review, AddOn


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"placeholder": "johndoe", "class": "auth-input"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••", "class": "auth-input"}),
    )


class RegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "auth-input"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "auth-input"}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "auth-input"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "auth-input"}))

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.Select(attrs={"class": "review-input"}),
        label="Rating",
    )
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Bagikan pengalamanmu bermain di venue ini...",
                "class": "review-input",
            }
        )
    )

    class Meta:
        model = Review
        fields = ("rating", "comment")


class AddOnSelectionForm(forms.Form):
    addons = forms.ModelMultipleChoiceField(
        queryset=AddOn.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "addon-checkbox"}),
    )

    def __init__(self, *args, **kwargs):
        venue = kwargs.pop("venue", None)
        super().__init__(*args, **kwargs)
        if venue is not None:
            self.fields["addons"].queryset = venue.addons.all()
