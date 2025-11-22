from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
# Importaciones para la API de Notificaciones
from django.http import JsonResponse 
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods 
from django.views.decorators.http import require_POST
import json # Necesario para parsear el JSON de peticiones POST

# 🔑 Importaciones necesarias para la vista basada en clase de cambio de contraseña 🔑
from django.contrib.auth.views import PasswordChangeView 

# Importamos formularios
from .forms import (
    AprobacionInspeccionForm, 
    SolicitudInspeccionForm,
    UsuarioAdminCreateForm, 
    UsuarioAdminUpdateForm,
    UsuarioPerfilForm, 
    PerfilForm,
    SpanishPasswordChangeForm 
)

# Importamos los Modelos y las NUEVAS CLASES DE CONSTANTES
from .models import (
    Inspeccion, 
    Perfil, 
    PlantillaInspeccion,
    Roles,           
    EstadoSolicitud,   
    EstadoInspeccion, 
    EstadoTarea,
    SolicitudInspeccion, 
    TareaInspeccion, 
    TareaPlantilla,
    Notification # <--- NUEVA IMPORTACIÓN
)

User = get_user_model()

# ==========================================================
# 1. LOGICA DE PERMISOS (Centralizada)
# ==========================================================
def check_role(user, role_name):
    """Verifica si el usuario pertenece al grupo cuyo nombre es 'role_name'."""
    return user.is_authenticated and user.groups.filter(name=role_name).exists()

# Usamos .value para asegurarnos de que la comparación sea con el string del nombre del Grupo
def is_cliente(user): return check_role(user, Roles.CLIENTE.value) 
def is_administrador(user): return check_role(user, Roles.ADMINISTRADOR.value) or user.is_superuser 
def is_tecnico(user): return check_role(user, Roles.TECNICO.value) 

# ==========================================================
# 2. AUTENTICACIÓN Y REDIRECCIÓN
# ==========================================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Usuario o contraseña incorrecta")
    
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # 🔑 LÓGICA CLAVE: Forzar cambio de contraseña si se ha hecho 🔑
    try:
        # Si el campo password_changed es False, redirigimos
        if not request.user.perfil.password_changed:
            messages.warning(request, "Debes cambiar tu contraseña inicial por seguridad.")
            return redirect('password_change_obligatorio') # Asegúrate que esta URL está en urls.py
    except Perfil.DoesNotExist:
        messages.error(request, "Error: No se encontró el perfil de usuario. Contacte a un administrador.")
        logout(request)
        return redirect('login')
    
    # Lógica de redirección por Rol (EXISTENTE)
    if is_administrador(request.user):
        return redirect('dashboard_administrador')
    elif is_tecnico(request.user):
        return redirect('dashboard_tecnico')
    elif is_cliente(request.user):
        return redirect('dashboard_cliente')
    
    messages.warning(request, "Tu usuario no tiene un rol asignado.")
    return redirect('home')

def home(request):
    return render(request, "index.html")

def nosotros_view(request):
    return render(request, 'nosotros.html', {})

# ==========================================================
# 3. 🔑 VISTA PARA EL CAMBIO DE CONTRASEÑA OBLIGATORIO 🔑
# ==========================================================
class PasswordChangeObligatorioView(PasswordChangeView):
    """
    Clase que maneja el cambio de contraseña forzado.
    """
    form_class = SpanishPasswordChangeForm 
    template_name = 'perfil/password_change_form.html' 
    success_url = 'password_changed_done' 

    def dispatch(self, request, *args, **kwargs):
        # Evitar que el usuario acceda si ya cambió su contraseña
        if request.user.perfil.password_changed:
            messages.info(request, "Tu contraseña ya fue cambiada.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

# Convertir la vista basada en clase a una función para usarla en urls.py
password_change_obligatorio_view = login_required(PasswordChangeObligatorioView.as_view())


@login_required
@require_http_methods(["GET"]) # Solo permite método GET
def password_changed_done_view(request):
    """
    Vista de destino después del cambio de contraseña exitoso. 
    Aquí es donde marcamos el flag en el modelo Perfil.
    """
    try:
        # 🚨 Marcamos el flag en el modelo Perfil 🚨
        request.user.perfil.password_changed = True
        request.user.perfil.save()
        messages.success(request, "Contraseña cambiada exitosamente. Bienvenido al sistema.")
        return redirect('dashboard') # Redirige al dashboard, que ahora permitirá el acceso normal
    except Perfil.DoesNotExist:
        messages.error(request, "Error interno al actualizar el perfil. Por favor, vuelve a iniciar sesión.")
        logout(request)
        return redirect('login')

# ==========================================================
# 4. VISTAS ADMINISTRADOR (EXISTENTES)
# ==========================================================
@login_required
@user_passes_test(is_administrador)
def dashboard_administrador(request):
    solicitudes_pendientes = SolicitudInspeccion.objects.filter(
        estado=EstadoSolicitud.PENDIENTE
    ).order_by('-fecha_solicitud')
    
    return render(request, 'dashboards/admin_dashboard.html', {
        'solicitudes_pendientes': solicitudes_pendientes
    })

@login_required
@user_passes_test(is_administrador)
def historial_solicitudes(request):
    historial = SolicitudInspeccion.objects.exclude(estado=EstadoSolicitud.PENDIENTE).order_by('-fecha_solicitud')
    return render(request, 'dashboards/admin/historial_solicitudes.html', {'historial': historial})

@login_required
@user_passes_test(is_administrador)
def admin_usuarios_list(request):
    usuarios = User.objects.all().order_by('username').prefetch_related('groups')
    usuarios_info = []
    for usuario in usuarios:
        # Buscamos si el usuario pertenece a alguno de nuestros roles definidos
        grupo = usuario.groups.filter(name__in=[r.value for r in Roles]).first()
        usuarios_info.append({
            'obj': usuario,
            'rol': grupo.name if grupo else 'Sin rol',
        })
    return render(request, 'dashboards/admin/usuarios_list.html', {'usuarios_info': usuarios_info})

@login_required
@user_passes_test(is_administrador)
def admin_usuario_crear(request):
    if request.method == 'POST':
        form = UsuarioAdminCreateForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save()
            messages.success(request, f"Usuario '{nuevo_usuario.username}' creado.")
            return redirect('admin_usuarios_list')
    else:
        form = UsuarioAdminCreateForm()
    return render(request, 'dashboards/admin/usuario_form.html', {'form': form, 'es_creacion': True})

@login_required
@user_passes_test(is_administrador)
def admin_usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UsuarioAdminUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado.")
            return redirect('admin_usuarios_list')
    else:
        form = UsuarioAdminUpdateForm(instance=usuario)
    return render(request, 'dashboards/admin/usuario_form.html', {'form': form, 'es_creacion': False, 'usuario_objetivo': usuario})

@login_required
@user_passes_test(is_administrador)
def admin_usuario_eliminar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, "Usuario eliminado.")
        return redirect('admin_usuarios_list')
    return render(request, 'dashboards/admin/usuario_confirm_delete.html', {'usuario_objetivo': usuario})

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
            fecha_programada = request.POST.get('fecha_programada') 

            if all([tecnico_id, plantilla_id, nombre_inspeccion]):
                try:
                    with transaction.atomic(): 
                        tecnico = User.objects.get(pk=tecnico_id)
                        plantilla = PlantillaInspeccion.objects.get(pk=plantilla_id)
                        
                        nueva_inspeccion = Inspeccion.objects.create(
                            solicitud=solicitud,
                            tecnico=tecnico,
                            plantilla_base=plantilla,
                            nombre_inspeccion=nombre_inspeccion,
                            fecha_programada=fecha_programada if fecha_programada else None,
                            estado=EstadoInspeccion.ASIGNADA
                        )

                        tareas_plantilla = TareaPlantilla.objects.filter(plantilla=plantilla)
                        tareas_a_crear = [
                            TareaInspeccion(
                                inspeccion=nueva_inspeccion,
                                plantilla_tarea=tp,
                                descripcion=tp.descripcion,
                                estado=EstadoTarea.PENDIENTE
                            ) for tp in tareas_plantilla
                        ]
                        TareaInspeccion.objects.bulk_create(tareas_a_crear)

                        solicitud.estado = EstadoSolicitud.APROBADA
                        solicitud.save()
                        
                        # CREAR NOTIFICACIONES TRAS APROBACIÓN
                        # 1. Notificar al Cliente (Aprobada)
                        Notification.objects.create(
                            user=solicitud.cliente,
                            message=f"Tu solicitud #{solicitud.id} ha sido APROBADA y se ha creado una Orden de Trabajo.",
                            link=reverse('detalle_orden', args=[solicitud.id]), # Asume que tienes esta URL
                            type='SOLICITUD',
                            object_id=solicitud.id
                        )
                        # 2. Notificar al Técnico (Asignada)
                        Notification.objects.create(
                            user=tecnico,
                            message=f"Se te ha ASIGNADO la Orden de Trabajo OT #{nueva_inspeccion.id}.",
                            link=reverse('completar_inspeccion', args=[nueva_inspeccion.id]), # Asume que tienes esta URL
                            type='INSPECCION',
                            object_id=nueva_inspeccion.id
                        )

                        messages.success(request, f"Inspección asignada a {tecnico.username}")
                        return redirect('dashboard_administrador')

                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
            else:
                messages.error(request, "Faltan datos obligatorios.")

        elif action == 'rechazar':
            motivo = request.POST.get('motivo_rechazo')
            if motivo:
                with transaction.atomic():
                    solicitud.estado = EstadoSolicitud.RECHAZADA
                    solicitud.motivo_rechazo = motivo
                    solicitud.save()
                    
                    # CREAR NOTIFICACIÓN TRAS RECHAZO
                    Notification.objects.create(
                        user=solicitud.cliente,
                        message=f"Tu solicitud #{solicitud.id} ha sido RECHAZADA. Motivo: {motivo[:100]}",
                        link=reverse('detalle_orden', args=[solicitud.id]), # Asume que tienes esta URL
                        type='SOLICITUD',
                        object_id=solicitud.id
                    )

                    messages.warning(request, "Solicitud rechazada.")
                    return redirect('dashboard_administrador')
            else:
                messages.error(request, "Indica un motivo de rechazo.")

    context = {
        'solicitud': solicitud,
        'tecnicos': User.objects.filter(groups__name=Roles.TECNICO.value), 
        'plantillas': PlantillaInspeccion.objects.all()
    }
    return render(request, 'dashboards/admin/gestionar_solicitud.html', context)

# ==========================================================
# 5. VISTAS TÉCNICO (EXISTENTES)
# ==========================================================
@login_required
@user_passes_test(is_tecnico)
def dashboard_tecnico(request):
    estados_activos = [EstadoInspeccion.ASIGNADA, EstadoInspeccion.EN_CURSO]
    inspecciones = Inspeccion.objects.filter(
        tecnico=request.user,
        estado__in=estados_activos
    ).select_related('solicitud').order_by('fecha_programada')

    return render(request, 'dashboards/tecnico/tecnico_dashboard.html', {
        'inspecciones_asignadas': inspecciones
    })

@login_required
@user_passes_test(is_tecnico)
def completar_inspeccion(request, pk):
    inspeccion = get_object_or_404(Inspeccion, pk=pk, tecnico=request.user)

    if inspeccion.estado == EstadoInspeccion.COMPLETADA:
        messages.info(request, "Esta inspección ya está finalizada.")
        return redirect('dashboard_tecnico')

    TareaFormSet = inlineformset_factory(
        Inspeccion, TareaInspeccion,
        fields=('estado', 'observacion'),
        extra=0, can_delete=False
    )

    if request.method == 'POST':
        formset = TareaFormSet(request.POST, instance=inspeccion)
        if formset.is_valid():
            formset.save()
            inspeccion.comentarios_generales = request.POST.get('comentarios_generales')
            action = request.POST.get('action')
            
            if action == 'terminar':
                inspeccion.estado = EstadoInspeccion.COMPLETADA
                inspeccion.fecha_finalizacion = timezone.now()
                inspeccion.save()
                
                # CREAR NOTIFICACIÓN TRAS COMPLETAR
                if inspeccion.solicitud:
                    inspeccion.solicitud.estado = EstadoSolicitud.COMPLETADA
                    inspeccion.solicitud.save()
                    
                    # Notificar al Cliente (Completada)
                    Notification.objects.create(
                        user=inspeccion.solicitud.cliente,
                        message=f"La Orden de Trabajo OT #{inspeccion.id} ha sido FINALIZADA.",
                        link=reverse('detalle_orden', args=[inspeccion.solicitud.id]),
                        type='INSPECCION',
                        object_id=inspeccion.id
                    )

                messages.success(request, "Inspección completada.")
                return redirect('dashboard_tecnico')
            else:
                if inspeccion.estado == EstadoInspeccion.ASIGNADA:
                    inspeccion.estado = EstadoInspeccion.EN_CURSO
                inspeccion.save()
                messages.success(request, "Progreso guardado.")
                return redirect('dashboard_tecnico')
        else:
            messages.error(request, "Error al guardar el formulario de tareas.")
    else:
        formset = TareaFormSet(instance=inspeccion)
        # Si la inspección está asignada y se está accediendo por primera vez, cámbiala a EN_CURSO
        if inspeccion.estado == EstadoInspeccion.ASIGNADA:
             inspeccion.estado = EstadoInspeccion.EN_CURSO
             inspeccion.save()


    return render(request, 'dashboards/tecnico/completar_inspeccion.html', {
        'inspeccion': inspeccion,
        'formset': formset
    })

@login_required
@user_passes_test(is_tecnico)
def perfil_tecnico(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        # Nota: aquí estás mezclando ModelForm y acceso directo a POST. Es mejor usar PerfilForm.
        perfil.descripcion = request.POST.get('descripcion_profesional', '').strip()
        if request.FILES.get('foto'):
            perfil.foto = request.FILES['foto']
        perfil.save()
        messages.success(request, "Perfil actualizado.")
    
    return render(request, 'dashboards/tecnico/perfil.html', {'perfil': perfil})

# ==========================================================
# 6. VISTAS CLIENTE (EXISTENTES)
# ==========================================================
@login_required
@user_passes_test(is_cliente)
def dashboard_cliente(request):
    solicitudes = SolicitudInspeccion.objects.filter(cliente=request.user).order_by('-fecha_solicitud')
    return render(request, 'dashboards/cliente_dashboard.html', {'solicitudes': solicitudes})

@login_required
@user_passes_test(is_cliente)
def solicitar_inspeccion(request):
    if request.method == 'POST':
        form = SolicitudInspeccionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.cliente = request.user
            solicitud.estado = EstadoSolicitud.PENDIENTE
            solicitud.save()
            
            # CREAR NOTIFICACIÓN PARA ADMINISTRADORES
            # Necesitas notificar a todos los administradores (usamos is_administrador para el filtro)
            admins = User.objects.filter(groups__name=Roles.ADMINISTRADOR.value)
            
            # Si usas superusers como admins, también deberías incluirlos:
            admins = admins | User.objects.filter(is_superuser=True)
            
            # Creamos notificaciones masivas para optimizar
            notifications_to_create = [
                Notification(
                    user=admin,
                    message=f"Nueva Solicitud de Inspección #{solicitud.id} enviada por {request.user.username}.",
                    link=reverse('aprobar_solicitud', args=[solicitud.id]), # Asume que tienes esta URL
                    type='SOLICITUD',
                    object_id=solicitud.id
                ) for admin in admins
            ]
            Notification.objects.bulk_create(notifications_to_create)

            messages.success(request, "Solicitud enviada.")
            return redirect('dashboard_cliente')
    else:
        # Pre-llenamos datos si el usuario tiene perfil con info (opcional)
        initial_data = {}
        # Puedes añadir lógica aquí para pre-llenar nombre, apellido, etc.

        form = SolicitudInspeccionForm(initial=initial_data)
        
    return render(request, 'dashboards/cliente/solicitar_inspeccion.html', {
        'form': form, 
        'solicitudes': SolicitudInspeccion.objects.filter(cliente=request.user)
    })

@login_required
@user_passes_test(is_cliente)
def detalle_orden(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    # Usamos el related_name 'inspeccion' definido en models.py (OneToOne)
    try:
        inspeccion = solicitud.inspeccion 
        tareas = inspeccion.tareas.all()
    except Inspeccion.DoesNotExist: # Mejor manejo de la excepción OneToOne
        inspeccion = None
        tareas = None

    return render(request, 'dashboards/cliente/detalle_orden.html', {
        'solicitud': solicitud,
        'inspeccion': inspeccion,
        'tareas': tareas
    })

@login_required
@user_passes_test(is_cliente)
def anular_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    if solicitud.estado == EstadoSolicitud.PENDIENTE:
        with transaction.atomic():
            solicitud.estado = EstadoSolicitud.ANULADA
            solicitud.save()
            
            # CREAR NOTIFICACIÓN PARA ADMINISTRADORES
            admins = User.objects.filter(groups__name=Roles.ADMINISTRADOR.value) | User.objects.filter(is_superuser=True)
            
            notifications_to_create = [
                Notification(
                    user=admin,
                    message=f"La Solicitud de Inspección #{solicitud.id} ha sido ANULADA por el cliente.",
                    link=reverse('historial_solicitudes'),
                    type='SOLICITUD',
                    object_id=solicitud.id
                ) for admin in admins
            ]
            Notification.objects.bulk_create(notifications_to_create)
            
            messages.success(request, "Solicitud anulada.")
    else:
        messages.error(request, "No se puede anular esta solicitud, ya está en proceso.")
    return redirect('dashboard_cliente')

@login_required
def editar_perfil(request):
    usuario = request.user
    perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
    if request.method == 'POST':
        user_form = UsuarioPerfilForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect('editar_perfil')
        else:
            messages.error(request, "Error al actualizar el perfil. Revise los datos.")
    else:
        user_form = UsuarioPerfilForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)
        
    # Extraemos el rol para mostrarlo en el template
    grupo = usuario.groups.filter(name__in=[r.value for r in Roles]).first()
    rol_actual = grupo.name if grupo else 'Sin rol'
    
    return render(request, 'perfil/perfil_editar.html', {
        'user_form': user_form, 
        'perfil_form': perfil_form,
        'rol_actual': rol_actual
    })
    
# ==========================================================
# 7. VISTAS API DE NOTIFICACIONES (¡NUEVO!)
# ==========================================================

@login_required
def get_notifications(request):
    """
    Retorna las notificaciones no leídas para el usuario actual,
    filtradas según su rol.
    """
    user = request.user
    role = user.perfil.get_role()
    
    # Base query: Notificaciones no leídas y ordenadas por fecha
    notifications_queryset = Notification.objects.filter(
        user=user, 
        is_read=False
    ).select_related('user')
    
    # Lógica de filtrado (Actualizamos el queryset base si es necesario, 
    # aunque ya se filtra por `user=user`)
    
    # 1. Administrador: Ve todas las que le han sido enviadas. (OK con el filtro base)
    if role == Roles.ADMINISTRADOR:
        pass # No se requiere filtrado adicional al 'user=user'

    # 2. Técnico: Ve las notificaciones de órdenes de trabajo o inspección que le lleguen.
    # El modelo Notification ya solo guarda notificaciones para el técnico específico (user=user), 
    # por lo que el filtro es correcto.

    # 3. Cliente: Solo notificaciones de órdenes aprobadas o rechazadas.
    # Dado que las notificaciones para el cliente solo se crean en 'aprobar_solicitud' 
    # (APROBADA o RECHAZADA) o en 'completar_inspeccion', el filtro base es suficiente.

    notifications = notifications_queryset[:10] # Limitar a 10 notificaciones para el dropdown
    
    data = [{
        'id': n.id,
        'message': n.message,
        'link': n.link or '#', # Aseguramos que haya un link
        'timestamp': n.created_at.strftime("%d/%m/%Y %H:%M"), # Formato de fecha
        'is_read': n.is_read
    } for n in notifications]
    
    unread_count = notifications_queryset.count()
    
    return JsonResponse({
        'notifications': data,
        'unread_count': unread_count
    })


@csrf_exempt # Desactiva CSRF temporalmente para la API POST (mejor usar métodos seguros, pero para simplificar)
@require_POST
@login_required
def mark_as_read(request):
    """
    Marca una o todas las notificaciones como leídas.
    """
    try:
        data = json.loads(request.body)
        notification_ids = data.get('ids', []) # Lista de IDs a marcar como leídas
        mark_all = data.get('mark_all', False) # Flag para marcar todas
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    notifications_to_update = Notification.objects.filter(user=request.user, is_read=False)
    
    if mark_all:
        notifications_to_update.update(is_read=True)
        return JsonResponse({'status': 'ok', 'message': 'Todas las notificaciones marcadas como leídas'})
    
    if notification_ids:
        notifications_to_update.filter(id__in=notification_ids).update(is_read=True)
        return JsonResponse({'status': 'ok', 'message': f'{len(notification_ids)} notificaciones marcadas como leídas'})
        
    return JsonResponse({'status': 'error', 'message': 'No se proporcionó ningún ID o acción'}, status=400)