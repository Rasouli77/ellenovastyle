from django import forms
from custom_login.models import Profile
from django.forms import ModelForm


class Edit(ModelForm):
    class Meta:
        model = Profile
        fields = ["province", "city", "name", "address"]
