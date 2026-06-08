from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    """
    Formulario personalizado de login para que coincida con el
    diseño premium oscuro y ámbar de ARIA.
    """
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'aria-input w-full focus:outline-none',
                'placeholder': 'Nombre de usuario',
                'id': 'login-username'
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'aria-input w-full focus:outline-none',
                'placeholder': 'Contraseña',
                'id': 'login-password'
            }
        )
    )
