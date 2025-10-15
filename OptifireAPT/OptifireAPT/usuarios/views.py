from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.http import Http404

# --- Importación de Modelos ---
from .models import (
    Inspeccion, 
    TareaInspeccion, 
    PlantillaInspeccion, 
    PlantillaTarea, 
    SolicitudInspeccion, 
    PerfilTecnico
)

User = get_user_model()

# ==========================================================
# 0. VISTAS PÚBLICAS Y DE AUTENTICACIÓN
# ==========================================================

def home(request):
  return render(request, "index.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    next_param = request.GET.get('next', '') 

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Usuario o contraseña incorrecta")

    return render(request, "login.html", {"next": next_param})

def logout_view(request):
    logout(request)
    return redirect('login')

def nosotros_view(request):
    return render(request, 'nosotros.html', {})

# ==========================================================
# 1. FUNCIONES DE PERMISOS (Restricción de Acceso)
# ==========================================================

def is_cliente(user):
    return user.groups.filter(name='Clientes').exists()

def is_administrador(user):
    return user.is_staff or user.groups.filter(name='Administradores').exists()

def is_tecnico(user):
    return user.groups.filter(name='Técnicos').exists()

def get_user_role(user):
    if is_administrador(user):
        return 'Administrador'
    elif is_tecnico(user):
        return 'Técnico'
    elif is_cliente(user):
        return 'Cliente'
    return None

# ==========================================================
# 2. DASHBOARD PRINCIPAL (Redirige por Rol)
# ==========================================================

@login_required
def dashboard(request):
    """Vista de redirección que envía al usuario a su dashboard específico."""
    role = get_user_role(request.user)
    
    if role == 'Cliente':
        return redirect('dashboard_cliente')
    elif role == 'Administrador':
        return redirect('dashboard_administrador')
    elif role == 'Técnico':
        return redirect('dashboard_tecnico')
    
    messages.warning(request, "Tu cuenta no tiene un rol asignado. Contacta al administrador.")
    return redirect('home') # O a una página de error/perfil

# ==========================================================
# 3. VISTAS DEL CLIENTE
# ==========================================================

@login_required
@user_passes_test(is_cliente)
def dashboard_cliente(request):
    solicitudes = SolicitudInspeccion.objects.filter(cliente=request.user).order_by('-fecha_solicitud')
    context = {'solicitudes': solicitudes}
    return render(request, 'dashboards/cliente_dashboard.html', context)

@login_required
@user_passes_test(is_cliente)
def solicitar_inspeccion(request):
    # NOTA: En producción, usarías un ModelForm aquí
    if request.method == 'POST':
        nombre = request.POST.get('nombre_cliente') # Asegúrate de usar el nombre correcto del campo HTML
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        maquinaria = request.POST.get('maquinaria')
        
        if nombre and direccion and telefono and maquinaria:
            SolicitudInspeccion.objects.create(
                cliente=request.user,
                nombre_cliente=nombre,
                direccion=direccion,
                telefono=telefono,
                maquinaria=maquinaria,
                estado='PENDIENTE'
            )
            messages.success(request, "Solicitud enviada con éxito. Esperando aprobación.")
            return redirect('dashboard_cliente')
        else:
            messages.error(request, "Por favor, completa todos los campos de la solicitud.")
            
    return render(request, 'cliente/solicitar_inspeccion.html') 

@login_required
@user_passes_test(is_cliente)
def eliminar_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    
    if solicitud.estado == 'PENDIENTE':
        solicitud.delete()
        messages.success(request, "Solicitud eliminada con éxito.")
    else:
        # Si tu modelo tiene choices en 'estado', esto está bien. Si no, usa solicitud.estado directamente.
        messages.error(request, f"La solicitud no se puede eliminar. Estado actual: {getattr(solicitud, 'get_estado_display', lambda: solicitud.estado)()}")
        
    return redirect('dashboard_cliente')


# ==========================================================
# 4. VISTAS DEL ADMINISTRADOR
# ==========================================================

@login_required
@user_passes_test(is_administrador)
def dashboard_administrador(request):
    solicitudes_pendientes = SolicitudInspeccion.objects.filter(estado='PENDIENTE').order_by('-fecha_solicitud')
    context = {'solicitudes_pendientes': solicitudes_pendientes}
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
@user_passes_test(is_administrador)
def historial_solicitudes(request):
    historial = SolicitudInspeccion.objects.exclude(estado='PENDIENTE').order_by('-fecha_solicitud')
    return render(request, 'admin/historial_solicitudes.html', {'historial': historial})


@login_required
@user_passes_test(is_administrador)
def gestionar_solicitud(request, pk):
    # Solo permite gestionar solicitudes PENDIENTES
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, estado='PENDIENTE')
    
    tecnicos = User.objects.filter(groups__name='Técnicos')
    plantillas = PlantillaInspeccion.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'rechazar':
            motivo = request.POST.get('motivo_rechazo')
            solicitud.estado = 'RECHAZADA'
            solicitud.motivo_rechazo = motivo
            solicitud.save()
            messages.warning(request, 'Solicitud RECHAZADA.')
            
        elif action == 'aprobar':
            tecnico_id = request.POST.get('tecnico')
            plantilla_id = request.POST.get('plantilla')
            nombre_inspeccion = request.POST.get('nombre_inspeccion', f"Inspección {solicitud.id}")

            try:
                tecnico = User.objects.get(pk=tecnico_id)
                plantilla = PlantillaInspeccion.objects.get(pk=plantilla_id)
                
                # 1. CREAR LA INSPECCIÓN
                inspeccion = Inspeccion.objects.create(
                    solicitud=solicitud,
                    tecnico=tecnico,
                    plantilla_base=plantilla,
                    nombre_inspeccion=nombre_inspeccion,
                    estado='ASIGNADA'
                )
                
                # 2. CREAR LAS TAREAS A PARTIR DE LA PLANTILLA
                tareas_base = PlantillaTarea.objects.filter(plantilla=plantilla)
                for tarea_base in tareas_base:
                    TareaInspeccion.objects.create(
                        inspeccion=inspeccion,
                        plantilla_tarea=tarea_base,
                        descripcion=tarea_base.descripcion,
                        estado='PENDIENTE'
                    )

                # 3. ACTUALIZAR ESTADO DE LA SOLICITUD
                solicitud.estado = 'APROBADA'
                solicitud.save()
                messages.success(request, f'Inspección creada y asignada a {tecnico.username}.')
                
            except (User.DoesNotExist, PlantillaInspeccion.DoesNotExist):
                 messages.error(request, 'Error: Técnico o Plantilla no encontrados o inválidos.')
                 return redirect('gestionar_solicitud', pk=pk)

        return redirect('dashboard_administrador')

    context = {
        'solicitud': solicitud,
        'tecnicos': tecnicos,
        'plantillas': plantillas,
    }
    return render(request, 'admin/gestionar_solicitud.html', context)


# ==========================================================
# 5. VISTAS DEL TÉCNICO
# ==========================================================

@login_required
@user_passes_test(is_tecnico)
def dashboard_tecnico(request):
    # Inspecciones que están ASIGNADAS o EN_PROGRESO
    inspecciones_pendientes = Inspeccion.objects.filter(
        tecnico=request.user
    ).exclude(estado='TERMINADA').order_by('estado', 'fecha_creacion')
    
    context = {'inspecciones_pendientes': inspecciones_pendientes}
    return render(request, 'dashboards/tecnico_dashboard.html', context)


@login_required
@user_passes_test(is_tecnico)
def completar_inspeccion(request, pk):
    inspeccion = get_object_or_404(Inspeccion, pk=pk, tecnico=request.user)
    
    # Restricción: No se puede editar una inspección terminada
    if inspeccion.estado == 'TERMINADA':
        messages.error(request, "Esta inspección ya ha sido finalizada y no puede modificarse.")
        return redirect('dashboard_tecnico')

    TareaFormSet = inlineformset_factory(
        Inspeccion, 
        TareaInspeccion, 
        fields=('estado', 'observacion'), 
        extra=0,
        can_delete=False
    )

    if request.method == 'POST':
        formset = TareaFormSet(request.POST, instance=inspeccion)
        action = request.POST.get('action') # 'guardar' o 'terminar'

        if formset.is_valid():
            formset.save()

            inspeccion.comentarios_generales = request.POST.get('comentarios_generales')
            
            if action == 'terminar':
                inspeccion.estado = 'TERMINADA'
                inspeccion.fecha_termino = timezone.now()
                messages.success(request, f'Inspección "{inspeccion.nombre_inspeccion}" finalizada.')
                
                # Actualizar estado de solicitud para el cliente
                if inspeccion.solicitud:
                    inspeccion.solicitud.estado = 'COMPLETADA'
                    inspeccion.solicitud.save()

            elif inspeccion.estado == 'ASIGNADA':
                # Si el técnico guarda algo, cambia el estado de ASIGNADA a EN_PROGRESO
                inspeccion.estado = 'EN_PROGRESO' 
                messages.info(request, "Progreso guardado.")
                
            inspeccion.save()
            return redirect('dashboard_tecnico')
        else:
            messages.error(request, "Error al guardar el formulario de tareas.")

    else: # GET
        # Si la inspección está ASIGNADA, la marcamos como EN_PROGRESO al abrirla
        if inspeccion.estado == 'ASIGNADA':
            inspeccion.estado = 'EN_PROGRESO'
            inspeccion.save()
            
        formset = TareaFormSet(instance=inspeccion)
        
    context = {
        'inspeccion': inspeccion,
        'formset': formset
    }
    return render(request, 'tecnico/completar_inspeccion.html', context)


@login_required
@user_passes_test(is_tecnico)
def perfil_tecnico(request):
    perfil, created = PerfilTecnico.objects.get_or_create(usuario=request.user)
    
    # NOTA: En producción, usarías un ModelForm (PerfilTecnicoForm)
    if request.method == 'POST':
        # Simulación de manejo de formulario manual:
        perfil.descripcion_profesional = request.POST.get('descripcion_profesional')
        if request.FILES.get('foto'):
            perfil.foto = request.FILES['foto']
            
        perfil.save()
        messages.success(request, "Perfil profesional actualizado.")
        return redirect('dashboard_tecnico')

    context = {'perfil': perfil}
    return render(request, 'tecnico/perfil.html', context)