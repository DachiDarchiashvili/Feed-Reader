from django import forms
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.models import User


class LogInForm(forms.Form):
    username = forms.CharField(max_length=60)
    password = forms.CharField(max_length=60)
    next = forms.CharField(max_length=120, required=False)


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'date_joined',
        ]
        field_classes = {'username': UsernameField}
