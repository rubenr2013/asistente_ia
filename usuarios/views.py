from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from .forms import LoginForm

def login_view(request):
    """
    Muestra la página de login y maneja el inicio de sesión.
    Si ya está autenticado, lo redirige al chat principal.
    """
    if request.user.is_authenticated:
        return redirect('chat')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('chat')
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {'form': form})

def logout_view(request):
    """
    Cierra la sesión del usuario y lo redirige a la página de login.
    """
    auth_logout(request)
    return redirect('login')
