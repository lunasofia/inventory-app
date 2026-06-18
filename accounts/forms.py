from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    """Sign-up form keyed on email (no username)."""

    class Meta:
        model = User
        fields = ('email', 'display_name')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('display_name',)
