from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, "index.html")

def login_view(request):
    error_message = None
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        import re
        user_pattern = re.compile(r'^[A-Za-z0-9]{4,}$')
        pass_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

        if not user_pattern.match(username):
            error_message = "Usuario inválido. Debe tener al menos 4 caracteres y solo letras o números."
        elif not pass_pattern.match(password):
            error_message = "Contraseña inválida. Debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial."
        else:
            from django.contrib.auth import authenticate, login
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return render(request, "dashboard.html")  # O redirige a donde corresponda
            else:
                error_message = "Usuario o contraseña incorrectos."
    return render(request, "login.html", {"error_message": error_message})

def dashboard(request):
    # puedes requerir login antes
    return render(request, "dashboard.html")
def nosotros_view(request):
    """Muestra la página 'Nosotros'."""
    # Asegúrate de que tu plantilla se llame 'nosotros.html'
    return render(request, 'nosotros.html', {})