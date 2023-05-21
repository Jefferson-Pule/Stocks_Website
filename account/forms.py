"""
Definition of forms.
"""

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from django import forms

from django.forms.widgets import PasswordInput, TextInput

# Registration Form

class CreateUserForm(UserCreationForm):
    class Meta:

        model = User
        fields = ['username', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget = TextInput())
    password = forms.CharField(widget = PasswordInput())

#
#from django.utils.translation import gettext_lazy as _

#from django import forms

#class BootstrapAuthenticationForm(AuthenticationForm):
#    """Authentication form which uses boostrap CSS."""
#    username = forms.CharField(max_length=254,
#                               widget=forms.TextInput({
#                                   'class': 'form-control',
#                                   'placeholder': 'User name'}))
#    password = forms.CharField(label=_("Password"),
#                               widget=forms.PasswordInput({
#                                   'class': 'form-control',
#                                   'placeholder':'Password'}))
