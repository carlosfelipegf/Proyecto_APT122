from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction

from .forms import (
    AprobacionInspeccionForm,
    SolicitudInspeccionForm,
    UsuarioAdminCreateForm,
    UsuarioAdminUpdateForm,
    UsuarioPerfilForm,
    PerfilForm,
)
from django.contrib.auth.models import Group 

from .models import (
    Inspeccion,
    Perfil,
    PlantillaInspeccion,
    ROL_ADMINISTRADOR,
    ROL_CLIENTE,
    ROL_TECNICO,
    SolicitudInspeccion,
    TareaInspeccion,
    TareaPlantilla,
)

User = get_user_model() 
ROLE_NAMES = [ROL_ADMINISTRADOR, ROL_TECNICO, ROL_CLIENTE]

# ==========================================================
# 1. FUNCIONES DE PERMISOS
# ==========================================================
def get_user_role(user):
    if user.is_anonymous:
        return None
    
    if user.groups.filter(name=ROL_ADMINISTRADOR).exists() or user.is_superuser:
        return ROL_ADMINISTRADOR
    elif user.groups.filter(name=ROL_TECNICO).exists():
        return ROL_TECNICO
    elif user.groups.filter(name=ROL_CLIENTE).exists():
        return ROL_CLIENTE
    
    return ROL_CLIENTE 

def is_cliente(user):
    return user.is_authenticated and get_user_role(user) == ROL_CLIENTE

def is_administrador(user):
    return user.is_authenticated and get_user_role(user) == ROL_ADMINISTRADOR

def is_tecnico(user):
    return user.is_authenticated and get_user_role(user) == ROL_TECNICO

def get_user_role_display(user):
    return get_user_role(user)

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
# 2. DASHBOARD PRINCIPAL (Redirige por Rol)
# ==========================================================
@login_required
def dashboard(request):
    role = get_user_role_display(request.user)
    
    if role == ROL_CLIENTE:
        return redirect('dashboard_cliente')
    elif role == ROL_ADMINISTRADOR:
        return redirect('dashboard_administrador')
    elif role == ROL_TECNICO:
        return redirect('dashboard_tecnico')
    
    messages.warning(request, "Tu cuenta no tiene un rol asignado. Contacta al administrador.")
    return redirect('home')

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
    if request.method == 'POST':
        form = SolicitudInspeccionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False) 
            solicitud.cliente = request.user 
            solicitud.estado = 'PENDIENTE' 
            solicitud.save()
            
            messages.success(request, "Solicitud enviada con éxito. Esperando aprobación.")
            return redirect('dashboard_cliente') 
    else:
        form = SolicitudInspeccionForm() 

    context = {
        'form': form,
        'solicitudes': SolicitudInspeccion.objects.filter(cliente=request.user) 
    }
    return render(request, 'dashboards/cliente/solicitar_inspeccion.html', context)

@login_required
@user_passes_test(is_cliente)
def eliminar_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    if solicitud.estado == 'PENDIENTE':
        solicitud.delete()
        messages.success(request, "Solicitud eliminada con éxito.")
    else:
        messages.error(request, f"La solicitud no se puede eliminar. Estado actual: {solicitud.get_estado_display()}.")
    return redirect('dashboard_cliente')

@login_required
@user_passes_test(is_cliente)
def detalle_orden(request, pk):
    # 1. Obtener la solicitud del cliente
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)

    # 2. Intentar obtener la Inspección asociada
    try:
        inspeccion = Inspeccion.objects.get(solicitud=solicitud)
        tareas = TareaInspeccion.objects.filter(inspeccion=inspeccion)
    except Inspeccion.DoesNotExist:
        inspeccion = None
        tareas = None

    context = {
        'solicitud': solicitud,
        'inspeccion': inspeccion,
        'tareas': tareas
    }
    
    return render(request, 'dashboards/cliente/detalle_orden.html', context)


# ==========================================================
# 4. VISTAS DEL ADMINISTRADOR
# ==========================================================

@login_required
@user_passes_test(is_administrador)
def dashboard_administrador(request):
    solicitudes_pendientes = SolicitudInspeccion.objects.filter(estado='PENDIENTE').order_by('-fecha_solicitud')
    
    context = {
        'solicitudes_pendientes': solicitudes_pendientes,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
@user_passes_test(is_administrador)
def historial_solicitudes(request):
    historial = SolicitudInspeccion.objects.exclude(estado='PENDIENTE').order_by('-fecha_solicitud')
    return render(request, 'dashboards/admin/historial_solicitudes.html', {'historial': historial})


@login_required
@user_passes_test(is_administrador)
def admin_usuarios_list(request):
    usuarios = (
        User.objects.all()
        .order_by('username')
        .prefetch_related('groups')
    )
    usuarios_info = []
    for usuario in usuarios:
        grupo = usuario.groups.filter(name__in=ROLE_NAMES).first()
        usuarios_info.append({
            'obj': usuario,
            'rol': grupo.name if grupo else 'Sin rol',
        })

    context = {
        'usuarios_info': usuarios_info,
    }
    return render(request, 'dashboards/admin/usuarios_list.html', context)


@login_required
@user_passes_test(is_administrador)
def admin_usuario_crear(request):
    if request.method == 'POST':
        form = UsuarioAdminCreateForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save()
            messages.success(
                request,
                f"Usuario '{nuevo_usuario.username}' creado correctamente.",
            )
            return redirect('admin_usuarios_list')
        messages.error(request, "Por favor corrige los errores señalados.")
    else:
        form = UsuarioAdminCreateForm()

    return render(
        request,
        'dashboards/admin/usuario_form.html',
        {
            'form': form,
            'es_creacion': True,
        },
    )


@login_required
@user_passes_test(is_administrador)
def admin_usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para modificar este usuario.")
        return redirect('admin_usuarios_list')

    if request.method == 'POST':
        form = UsuarioAdminUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('admin_usuarios_list')
        messages.error(request, "Por favor corrige los errores señalados.")
    else:
        form = UsuarioAdminUpdateForm(instance=usuario)

    return render(
        request,
        'dashboards/admin/usuario_form.html',
        {
            'form': form,
            'es_creacion': False,
            'usuario_objetivo': usuario,
        },
    )


@login_required
@user_passes_test(is_administrador)
def admin_usuario_eliminar(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    if usuario == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect('admin_usuarios_list')

    if usuario.is_superuser:
        messages.error(request, "No es posible eliminar esta cuenta.")
        return redirect('admin_usuarios_list')

    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f"Usuario '{username}' eliminado correctamente.")
        return redirect('admin_usuarios_list')

    return render(
        request,
        'dashboards/admin/usuario_confirm_delete.html',
        {
            'usuario_objetivo': usuario,
        },
    )


@login_required
@user_passes_test(is_administrador)
def aprobar_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action') 
        
        if action == 'aprobar':
            tecnico_id = request.POST.get('tecnico')
            plantilla_id = request.POST.get('plantilla')
            nombre_inspeccion = request.POST.get('nombre_inspeccion')
            
            if not all([tecnico_id, plantilla_id, nombre_inspeccion]):
                messages.error(request, "Debe seleccionar un técnico, una plantilla y dar un nombre a la inspección.")
            else:
                try:
                    tecnico = get_object_or_404(User, pk=tecnico_id)
                    plantilla = get_object_or_404(PlantillaInspeccion, pk=plantilla_id)
                    
                    with transaction.atomic():
                        nueva_inspeccion = Inspeccion.objects.create(
                            solicitud=solicitud,
                            tecnico=tecnico,
                            plantilla_base=plantilla,
                            nombre_inspeccion=nombre_inspeccion,
                            estado='ASIGNADA'
                        )

                        tareas_plantilla = TareaPlantilla.objects.filter(plantilla=plantilla)
                        
                        tareas_a_crear = [
                            TareaInspeccion(
                                inspeccion=nueva_inspeccion,
                                descripcion=tp.descripcion 
                            ) for tp in tareas_plantilla
                        ]
                        TareaInspeccion.objects.bulk_create(tareas_a_crear)

                        solicitud.estado = 'APROBADA'
                        solicitud.save()
                        
                        messages.success(request, f"Inspección '{nombre_inspeccion}' creada y asignada a {tecnico.username}.")
                        return redirect('dashboard_administrador')

                except Exception as e:
                    messages.error(request, f"Error al procesar la aprobación: {e}")

        elif action == 'rechazar':
            motivo = request.POST.get('motivo_rechazo')
            if motivo:
                solicitud.estado = 'RECHAZADA'
                solicitud.motivo_rechazo = motivo
                solicitud.save()
                messages.warning(request, "Solicitud rechazada correctamente.")
                return redirect('dashboard_administrador')
            else:
                messages.error(request, "Debe proporcionar un motivo para el rechazo.")
    
    tecnicos_list = User.objects.filter(groups__name=ROL_TECNICO).order_by('username')
    plantillas_list = PlantillaInspeccion.objects.all()

    context = {
        'solicitud': solicitud,
        'tecnicos': tecnicos_list,
        'plantillas': plantillas_list,
    }
    
    return render(request, 'dashboards/admin/gestionar_solicitud.html', context)


# ==========================================================
# 5. VISTAS DEL TÉCNICO
# ==========================================================
@login_required
@user_passes_test(is_tecnico)
def dashboard_tecnico(request):
    inspecciones_asignadas = Inspeccion.objects.filter(
        tecnico=request.user,
        estado__in=['ASIGNADA', 'EN_CURSO'] 
    ).order_by('fecha_creacion')

    context = {
        'inspecciones_asignadas': inspecciones_asignadas,
    }
    
    return render(request, 'dashboards/tecnico_dashboard.html', context)


@login_required
@user_passes_test(is_tecnico)
def completar_inspeccion(request, pk):
    inspeccion = get_object_or_404(Inspeccion, pk=pk, tecnico=request.user)
    
    if inspeccion.estado == 'COMPLETADA':
        messages.error(request, "Esta inspección ya ha sido finalizada y no puede modificarse.")
        return redirect('dashboard_tecnico')

    TareaFormSet = inlineformset_factory(
        Inspeccion, TareaInspeccion, fields=('estado', 'observacion'), extra=0, can_delete=False
    )

    if request.method == 'POST':
        formset = TareaFormSet(request.POST, instance=inspeccion)
        action = request.POST.get('action')

        if formset.is_valid():
            formset.save()

            inspeccion.comentarios_generales = request.POST.get('comentarios_generales')
            
            if action == 'terminar':
                inspeccion.estado = 'COMPLETADA' 
                inspeccion.fecha_finalizacion = timezone.now()
                messages.success(request, f'Inspección "{inspeccion.nombre_inspeccion}" finalizada.')
                
                if inspeccion.solicitud:
                    inspeccion.solicitud.estado = 'COMPLETADA'
                    inspeccion.solicitud.save()

            elif inspeccion.estado == 'ASIGNADA':
                inspeccion.estado = 'EN_CURSO' 
                messages.info(request, "Progreso guardado.")
                
            inspeccion.save()
            return redirect('dashboard_tecnico')
        else:
            messages.error(request, "Error al guardar el formulario de tareas.")

    else: # GET
        if inspeccion.estado == 'ASIGNADA':
            inspeccion.estado = 'EN_CURSO'
            inspeccion.save()
            
        formset = TareaFormSet(instance=inspeccion)
        
    context = {
        'inspeccion': inspeccion,
        'formset': formset
    }
    
    # 🚨 LÍNEA CORREGIDA PARA LA RUTA DEL TEMPLATE 🚨
    return render(request, 'dashboards/tecnico/completar_inspeccion.html', context)


@login_required
@user_passes_test(is_tecnico)
def perfil_tecnico(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        perfil.descripcion = request.POST.get('descripcion_profesional', '').strip()
        if request.FILES.get('foto'):
            perfil.foto = request.FILES['foto']

        perfil.save()
        messages.success(request, "Perfil profesional actualizado.")
        return redirect('perfil_tecnico')

    # Compatibilidad con la plantilla existente
    perfil.descripcion_profesional = perfil.descripcion

    context = {'perfil': perfil}
    return render(request, 'dashboards/tecnico/perfil.html', context)

@login_required
def editar_perfil(request):
    usuario = request.user
    perfil, created = Perfil.objects.get_or_create(usuario=usuario)

    if request.method == 'POST':
        user_form = UsuarioPerfilForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('editar_perfil')
    else:
        user_form = UsuarioPerfilForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)

    return render(request, 'perfil/perfil_editar.html', {
        'user_form': user_form,
        'perfil_form': perfil_form
    })

@login_required
def descargar_acta(request, pk):
    """
    Vista placeholder temporal para la generación y descarga del PDF.
    """
    # TODO: Implementar lógica de generación de PDF aquí.
    messages.info(request, f"Función para descargar el Acta de Inspección #{pk} aún no implementada.")
    # Redirigir al detalle de la orden hasta que la funcionalidad esté lista
    return redirect('detalle_orden', pk=Inspeccion.objects.get(pk=pk).solicitud.pk)