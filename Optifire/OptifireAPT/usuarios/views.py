from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# La vista de prueba original, que modificaremos
# def home_page(request):
#     return HttpResponse("Página de inicio de la aplicación Usuarios de OptiFire.")

# --- NUEVA VISTA PARA USUARIOS NORMALES ---
@login_required # Esto asegura que solo usuarios logueados puedan acceder
def dashboard_inspector(request):
    # Lógica para mostrar las inspecciones o tareas del Inspector.
    
    # Para simplificar, devolvemos un mensaje basado en el usuario logueado.
    user_rol = request.user.perfil.get_rol_display() if hasattr(request.user, 'perfil') else 'sin rol asignado'
    
    context = {
        'username': request.user.username,
        'rol': user_rol,
        'email': request.user.email
    }
    
    # En un proyecto real, esto devolvería render(request, 'usuarios/dashboard.html', context)
    return HttpResponse(f"""
        <h1>Bienvenido al Sistema OptiFire, {request.user.first_name if request.user.first_name else request.user.username}!</h1>
        <p>Tu rol es: <strong>{user_rol}</strong>.</p>
        <p>Esta es tu área de trabajo donde podrás gestionar tus tareas de inspección.</p>
        <p>🎉 ¡Login exitoso! 🎉</p>
    """)