from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404    
from django.forms import inlineformset_factory
from .models import Inspeccion, TareaInspeccion

def home(request):
    return render(request, "index.html")


def login_view(request):
    # Si ya está autenticado lo mando al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    # next param (cuando se redirige a login por @login_required)
    next_param = request.GET.get('next', '') 

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Prioriza next enviado por POST o GET
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Usuario o contraseña incorrecta")

    return render(request, "login.html", {"next": next_param})


@login_required
def dashboard(request):
    # Obtener todas las inspecciones del usuario
    inspecciones = Inspeccion.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    
    context = {
        'inspecciones': inspecciones,
        'nombre_usuario': request.user.username  # Para el "Bienvenido, usuario2"
    }
    return render(request, 'dashboard.html', context)


# --- Lógica para Crear y Guardar Inspecciones ---

# Definir el Formset que manejará múltiples TareaInspeccion en el formulario
TareaInspeccionFormSet = inlineformset_factory(
    Inspeccion, 
    TareaInspeccion, 
    fields=('descripcion', 'estado', 'observacion'), 
    extra=5,  # Muestra 5 campos vacíos por defecto
    can_delete=False
)

# 2. Vista para Crear una Nueva Inspección (Ruta: /dashboard/nueva_inspeccion/)
@login_required
def nueva_inspeccion(request):
    if request.method == 'POST':
        # Instanciar el formulario de Inspeccion con los datos POST
        inspeccion_form = Inspeccion(usuario=request.user)
        
        # Instanciar el formset de Tareas
        formset = TareaInspeccionFormSet(request.POST, request.FILES, instance=inspeccion_form)
        
        if formset.is_valid():
            # 1. Guardar la Inspeccion principal primero
            inspeccion = Inspeccion.objects.create(
                usuario=request.user,
                nombre_inspeccion=request.POST.get('nombre_inspeccion'), # Capturamos el nombre
                completada=('terminar_inspeccion' in request.POST) # Marcar como True si se presiona el botón "Terminar"
            )
            
            # 2. Guardar el formset de Tareas, asociándolo a la Inspeccion recién creada
            for form in formset:
                # Solo guardar si el campo 'descripcion' tiene texto
                if form.cleaned_data and form.cleaned_data.get('descripcion'):
                    TareaInspeccion.objects.create(
                        inspeccion=inspeccion,
                        descripcion=form.cleaned_data['descripcion'],
                        estado=form.cleaned_data['estado'],
                        observacion=form.cleaned_data.get('observacion', '')
                    )

            # Redirigir al dashboard después de guardar
            return redirect('dashboard')
        
    else:
        # En una petición GET, inicializamos formularios vacíos
        inspeccion_form = Inspeccion() # No necesitamos un form normal, solo el nombre
        formset = TareaInspeccionFormSet(instance=Inspeccion())

    return render(request, 'nueva_inspeccion.html', {'formset': formset})

def logout_view(request):
    logout(request)
    return redirect('login')

def nosotros_view(request):
    """Muestra la página 'Nosotros'."""
    # Asegúrate de que tu plantilla se llame 'nosotros.html'
    return render(request, 'nosotros.html', {})