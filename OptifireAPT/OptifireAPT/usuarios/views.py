from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import Group
from datetime import datetime # Importación necesaria para manejar la fecha

from .forms import (
    AprobacionInspeccionForm, # No usada directamente en estas vistas, pero mantenida por si acaso.
    SolicitudInspeccionForm,
    UsuarioAdminCreateForm,
    UsuarioAdminUpdateForm,
    UsuarioEditForm,
    PerfilEditForm,
    RequiredPasswordChangeForm, # No usada directamente, se usa PasswordChangeForm de Django.
    PlantillaInspeccionForm,
    TareaPlantillaForm,
)

from .models import (
    Inspeccion,
    TareaInspeccion,
    PlantillaInspeccion,
    TareaPlantilla,
    SolicitudInspeccion,
    Perfil,
    ROL_ADMINISTRADOR,
    ROL_TECNICO,
    ROL_CLIENTE
)

User = get_user_model()
ROLE_NAMES = [ROL_ADMINISTRADOR, ROL_TECNICO, ROL_CLIENTE]

# --- Funciones de Utilidad para Roles y Permisos ---

def get_user_role(user):
    """
    Determina el rol principal del usuario basado en sus grupos.
    Se apoya en la propiedad get_role() del modelo Perfil.
    """
    if user.is_anonymous:
        return None
    
    try:
        return user.perfil.get_role()
    except Perfil.DoesNotExist:
        # Esto no debería ocurrir si el signal funciona, pero es un fallback
        return ROL_CLIENTE

def is_cliente(user):
    return user.is_authenticated and get_user_role(user) == ROL_CLIENTE

def is_administrador(user):
    return user.is_authenticated and (get_user_role(user) == ROL_ADMINISTRADOR or user.is_superuser)

def is_tecnico(user):
    return user.is_authenticated and get_user_role(user) == ROL_TECNICO

def get_user_role_display(user):
    """Retorna el rol del usuario (ROL_ADMINISTRADOR, ROL_TECNICO, ROL_CLIENTE o None)"""
    return get_user_role(user)

# --- Vistas de Autenticación y Home ---

def home(request):
    return render(request, "index.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    next_param = request.GET.get('next', '')

    if request.method == 'POST':
        email_o_username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = None
        
        # 1. Intentar encontrar al usuario por CORREO ELECTRÓNICO
        try:
            target_user = User.objects.get(email__iexact=email_o_username)
            user = authenticate(request, username=target_user.username, password=password)
            
        except User.DoesNotExist:
            # 2. Si no se encuentra por email, intentamos por USERNAME (fallback)
            user = authenticate(request, username=email_o_username, password=password)
            
        if user is not None:
            login(request, user)
            
            try:
                perfil = user.perfil
            except Perfil.DoesNotExist:
                perfil, created = Perfil.objects.get_or_create(usuario=user)
            
            if perfil.cambio_contrasena_obligatorio:
                messages.info(request, "Por seguridad, debes cambiar tu contraseña inicial.")
                return redirect('change_password_required')

            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Correo Electrónico o contraseña incorrecta.")

    return render(request, "login.html", {"next": next_param})

def logout_view(request):
    logout(request)
    
    return redirect('login')

def nosotros_view(request):
    return render(request, 'nosotros.html', {})

# --- Vistas de Seguridad y Perfil ---

@login_required
def change_password_required_view(request):
    """
    Vista para manejar el cambio de contraseña obligatorio al primer inicio de sesión.
    """
    user = request.user
    
    # OBTENER EL PERFIL
    try:
        perfil = user.perfil
    except Perfil.DoesNotExist:
        perfil, created = Perfil.objects.get_or_create(usuario=user)
    
    
    # Redirige si la contraseña ya fue cambiada y no está forzado a estar aquí
    if not perfil.cambio_contrasena_obligatorio and 'required' not in request.path:
        return redirect('dashboard')
    
    
    if request.method == 'POST':
        # Usamos PasswordChangeForm para asegurar que la contraseña actual sea verificada
        form = PasswordChangeForm(user, request.POST)
        
        if form.is_valid():
            new_user = form.save()
            update_session_auth_hash(request, new_user)
            
            # Desactiva la bandera de obligatoriedad
            if perfil.cambio_contrasena_obligatorio:
                perfil.cambio_contrasena_obligatorio = False
                perfil.save()
            
            messages.success(request, "Contraseña actualizada con éxito.")
            
            # Redirección por Rol al dashboard correcto
            role = get_user_role_display(new_user)
            if role == ROL_CLIENTE:
                return redirect('dashboard_cliente')
            elif role == ROL_ADMINISTRADOR:
                return redirect('dashboard_administrador')
            elif role == ROL_TECNICO:
                return redirect('dashboard_tecnico')
            
            return redirect('home')
        
        # Si el formulario NO es válido
        messages.error(request, "Error al actualizar la contraseña. Por favor, verifica la contraseña actual y que las nuevas coincidan.")
    
    else: # GET
        form = PasswordChangeForm(user)

    return render(request, 'auth/change_password_required.html', {'form': form, 'es_obligatorio': perfil.cambio_contrasena_obligatorio})


@login_required
def dashboard(request):
    """
    Redirige al dashboard específico según el rol del usuario,
    o fuerza el cambio de contraseña si es obligatorio.
    """
    # Chequeo de la bandera usando el modelo Perfil
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)

    if perfil.cambio_contrasena_obligatorio:
        messages.warning(request, "Debes cambiar tu contraseña para continuar.")
        return redirect('change_password_required')
        
    role = get_user_role_display(request.user)
    
    if role == ROL_CLIENTE:
        return redirect('dashboard_cliente')
    elif role == ROL_ADMINISTRADOR:
        return redirect('dashboard_administrador')
    elif role == ROL_TECNICO:
        return redirect('dashboard_tecnico')
    
    messages.warning(request, "Tu cuenta no tiene un rol asignado. Contacta al administrador.")
    return redirect('home')


@login_required
def editar_perfil_view(request):
    """
    Permite a cualquier usuario autenticado editar la información básica (User)
    y la información adicional (Perfil) en una sola vista.
    """
    usuario_instance = request.user
    # Obtener la instancia de Perfil a editar (debe existir gracias al signal)
    perfil_instance, created = Perfil.objects.get_or_create(usuario=usuario_instance)
    
    # LÓGICA DE GRUPOS
    group_names = request.user.groups.values_list('name', flat=True)
    
    if request.method == 'POST':
        # Instanciar ambos formularios
        user_form = UsuarioEditForm(request.POST, instance=usuario_instance)
        perfil_form = PerfilEditForm(request.POST, request.FILES, instance=perfil_instance)
        
        if user_form.is_valid() and perfil_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    perfil_form.save()
                    
                messages.success(request, "Tu perfil ha sido actualizado con éxito.")
                return redirect('editar_perfil')
                
            except Exception as e:
                messages.error(request, f"Hubo un error al guardar: {e}. Inténtalo de nuevo.")
        else:
            messages.error(request, "Hubo un error al actualizar el perfil. Por favor, revisa los datos.")
            
    else: # GET
        user_form = UsuarioEditForm(instance=usuario_instance)
        perfil_form = PerfilEditForm(instance=perfil_instance)
        
    context = {
        'user_form': user_form,      # Para nombre, apellido, email
        'perfil_form': perfil_form,  # Para foto, descripcion, telefono
        'group_names': group_names,  # Para mostrar el rol en el template
        'rol': get_user_role_display(request.user) # Rol legible
    }
    
    return render(request, 'perfil/perfil_editar.html', context)


# ----------------------------------------------------------------------
# 🚢 Vistas de Cliente (ROL_CLIENTE)
# ----------------------------------------------------------------------

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
            
            messages.success(request, "Solicitud enviada con éxito. Esperando cotización.")
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
def aceptar_cotizacion_cliente(request, pk):
    """
    Permite al cliente ver, aceptar o rechazar la cotización enviada por el Administrador.
    Si acepta, se crea la Inspeccion (Orden de Trabajo) si hay plantilla disponible.
    """
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    
    # REGLA DE NEGOCIO: Solo se puede gestionar si está en estado 'COTIZANDO'
    if solicitud.estado != 'COTIZANDO':
        messages.info(request, "Esta solicitud no está pendiente de su aprobación o ya fue gestionada.")
        return redirect('dashboard_cliente')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'aceptar':
            try:
                # El proceso de aprobación y asignación final (Crea la Inspeccion)
                with transaction.atomic():
                   
                    # 1. Validar y obtener la plantilla por defecto (o la que se cotizó)
                    try:
                        # Asume la primera plantilla si el modelo Solicitud no tiene campo plantilla
                        plantilla = PlantillaInspeccion.objects.first() 
                        if not plantilla:
                            raise Exception("No hay plantillas disponibles para crear la inspección.")
                    except PlantillaInspeccion.DoesNotExist:
                        messages.error(request, "No se pudo crear la inspección: falta la plantilla.")
                        # No es necesario revertir el estado aquí, el rollback de 'transaction.atomic' lo hace.
                        raise 
                        
                    # 2. Actualizar estado de Solicitud
                    solicitud.estado = 'APROBADA'
                    solicitud.save()
                    
                    # 3. CREAR LA INSPECCIÓN (ORDEN DE TRABAJO FINAL)
                    tecnico = solicitud.tecnico_asignado 
                    
                    # Usa la fecha programada de la solicitud o la actual si no hay (debería existir)
                    fecha_asignacion = solicitud.fecha_programada if solicitud.fecha_programada else datetime.now().date() 

                    nueva_inspeccion = Inspeccion.objects.create(
                        solicitud=solicitud,
                        tecnico=tecnico,
                        plantilla_base=plantilla,
                        nombre_inspeccion=f"Inspección #{solicitud.id} - {solicitud.maquinaria}",
                        fecha_programada=fecha_asignacion,
                        estado='ASIGNADA' # El técnico la verá como asignada
                    )

                    # 4. DUPLICAR TAREAS DE LA PLANTILLA
                    tareas_plantilla = TareaPlantilla.objects.filter(plantilla=plantilla)
                    tareas_a_crear = [
                        TareaInspeccion(
                            inspeccion=nueva_inspeccion,
                            descripcion=tp.descripcion
                        ) for tp in tareas_plantilla
                    ]
                    TareaInspeccion.objects.bulk_create(tareas_a_crear)

                    messages.success(request, f"¡Cotización #{pk} aceptada! La orden ha sido creada y enviada al técnico {tecnico.username}.")
                    return redirect('dashboard_cliente')

            except Exception as e:
                messages.error(request, f"Error crítico al aceptar la cotización. Contácte al administrador: {e}")
                
        elif action == 'rechazar':
            motivo = request.POST.get('motivo_rechazo')
            if not motivo:
                messages.error(request, "Debe especificar un motivo de rechazo.")
                return redirect('aceptar_cotizacion_cliente', pk=pk)

            solicitud.estado = 'RECHAZADA'
            solicitud.motivo_rechazo = f"Rechazo de Cotización por Cliente: {motivo}"
            solicitud.save()
            messages.warning(request, f"La cotización #{pk} ha sido rechazada. El administrador ha sido notificado.")
            return redirect('dashboard_cliente')
        
        else:
            messages.error(request, "Acción no válida.")
            return redirect('aceptar_cotizacion_cliente', pk=pk)

    # Renderizar la página de gestión de cotización (GET)
    context = {'solicitud': solicitud}
    return render(request, 'dashboards/cliente/aceptar_cotizacion.html', context)


@login_required
@user_passes_test(is_cliente)
def eliminar_solicitud(request, pk):
    """
    Vista obsoleta. Redirige a anular_solicitud para mantener la trazabilidad.
    """
    messages.warning(request, "Usar 'anular_solicitud' para solicitudes pendientes para mantener la trazabilidad.")
    return redirect('dashboard_cliente')


@login_required
@user_passes_test(is_cliente)
def anular_solicitud(request, pk):
    """
    Permite al cliente cambiar el estado de una solicitud de 'PENDIENTE' a 'ANULADA'.
    """
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    
    # Solo permitir anular si el estado es PENDIENTE
    if solicitud.estado == 'PENDIENTE':
        if request.method == 'GET' or request.method == 'POST':
            # Nota: se usa GET/POST simple asumiendo una confirmación previa
            solicitud.estado = 'ANULADA'
            solicitud.save()
            messages.success(request, f"La Solicitud #{pk} ha sido anulada con éxito.")
            return redirect('dashboard_cliente')
        else:
            messages.error(request, "Método no permitido.")
    else:
        messages.error(request, f"La Solicitud #{pk} no puede ser anulada. Su estado actual es: {solicitud.get_estado_display()}.")
    
    return redirect('dashboard_cliente')


@login_required
@user_passes_test(is_cliente)
def detalle_orden(request, pk):
    """
    Muestra el detalle de una solicitud y, si existe, la inspección asociada.
    """
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    
    if solicitud.estado == 'COTIZANDO':
        messages.info(request, "Esta orden está pendiente de su aprobación. Por favor, revise la cotización.")
        return redirect('aceptar_cotizacion_cliente', pk=pk)

    inspeccion = None
    tareas = None
    try:
        inspeccion = Inspeccion.objects.get(solicitud=solicitud)
        tareas = TareaInspeccion.objects.filter(inspeccion=inspeccion)
    except Inspeccion.DoesNotExist:
        pass # Es normal si la solicitud está en PENDIENTE, ANULADA, o RECHAZADA

    context = {
        'solicitud': solicitud,
        'inspeccion': inspeccion,
        'tareas': tareas
    }
    
    return render(request, 'dashboards/cliente/detalle_orden.html', context)

# ----------------------------------------------------------------------
# 👑 Vistas de Administrador (ROL_ADMINISTRADOR)
# ----------------------------------------------------------------------

@login_required
@user_passes_test(is_administrador)
def dashboard_administrador(request):
    solicitudes_pendientes = SolicitudInspeccion.objects.filter(estado='PENDIENTE').order_by('-fecha_solicitud')
    solicitudes_cotizando = SolicitudInspeccion.objects.filter(estado='COTIZANDO').order_by('-fecha_solicitud')
    
    context = {
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_cotizando': solicitudes_cotizando,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
@user_passes_test(is_administrador)
def historial_solicitudes(request):
    historial = SolicitudInspeccion.objects.exclude(estado__in=['PENDIENTE', 'COTIZANDO']).order_by('-fecha_solicitud')
    return render(request, 'dashboards/admin/historial_solicitudes.html', {'historial': historial})


@login_required
@user_passes_test(is_administrador)
def gestionar_solicitud(request, pk):
    """
    Vista para gestionar solicitudes PENDIENTES: Enviar Cotización o Rechazar.
    """
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk)
    
    # Solo permite gestionar si está PENDIENTE
    if solicitud.estado != 'PENDIENTE':
        messages.info(request, f"La solicitud #{pk} ya fue gestionada. Su estado es: {solicitud.get_estado_display()}.")
        return redirect('dashboard_administrador')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enviar_cotizacion': 
            monto_cotizacion = request.POST.get('monto_cotizacion') 
            detalle_cotizacion = request.POST.get('detalle_cotizacion')
            tecnico_id = request.POST.get('tecnico') 
            fecha_programada_str = request.POST.get('fecha_programada') # Nuevo campo
        
            if not all([monto_cotizacion, tecnico_id, fecha_programada_str]):
                messages.error(request, "El Monto, la Pre-Asignación del Técnico y la Fecha Programada son obligatorios para cotizar.")
                return redirect('gestionar_solicitud', pk=pk)
            
            try:
                tecnico_pre_asignado = get_object_or_404(User, pk=tecnico_id)
                monto = int(monto_cotizacion)
                fecha_programada = datetime.strptime(fecha_programada_str, '%Y-%m-%d').date()

                with transaction.atomic():
                    # 1. ACTUALIZAR LA SOLICITUD
                    solicitud.monto_cotizacion = monto
                    solicitud.detalle_cotizacion = detalle_cotizacion
                    solicitud.tecnico_asignado = tecnico_pre_asignado
                    solicitud.fecha_programada = fecha_programada # Guardar la fecha
                    
                    solicitud.estado = 'COTIZANDO' 
                    solicitud.save()
                    
                    # 2. ENVIAR MENSAJE AL CLIENTE
                    messages.success(request, f"Cotización #{pk} enviada al cliente para su aprobación. Monto: ${monto_cotizacion}.")
                    
                    return redirect('dashboard_administrador') 

            except Exception as e:
                messages.error(request, f"Error al enviar cotización o fecha inválida: {e}")
                
        
        elif action == 'rechazar':
            motivo = request.POST.get('motivo_rechazo')
            if motivo:
                solicitud.estado = 'RECHAZADA'
                solicitud.motivo_rechazo = motivo
                solicitud.save()
                messages.warning(request, f"Solicitud #{pk} rechazada correctamente.")
                return redirect('dashboard_administrador')
            else:
                messages.error(request, "Debe proporcionar un motivo para el rechazo.")
        
        # Si se envió otra acción que no está definida
        else:
            messages.error(request, "Acción no válida.")

    
    # Asegúrate de que solo se muestren usuarios que son 'ROL_TECNICO'
    tecnicos_list = User.objects.filter(groups__name=ROL_TECNICO).order_by('username')
    plantillas_list = PlantillaInspeccion.objects.all()

    context = {
        'solicitud': solicitud,
        'tecnicos': tecnicos_list,
        'plantillas': plantillas_list, # Aunque no se usa en el post de cotización, puede ser informativo
        'hoy': datetime.now().strftime('%Y-%m-%d'), # Para el campo de fecha mínima
    }
    
    return render(request, 'dashboards/admin/gestionar_solicitud.html', context)


# --- Gestión de Usuarios (Admin) ---

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
        rol_display = get_user_role_display(usuario) or 'Sin rol'
        
        usuarios_info.append({
            'obj': usuario,
            'rol': rol_display,
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
            
            # Se asume que el form setea cambio_contrasena_obligatorio=True en el Perfil.
            
            messages.success(
                request,
                f"Usuario '{nuevo_usuario.username}' creado correctamente. Deberá cambiar la contraseña en el primer inicio de sesión.",
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
        messages.error(request, "Por favor corrige los errores señaladas.")
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
        return redirect('admin_usuarios_list') # Se agregó el return aquí.

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

# --- Gestión de Plantillas (Admin) ---

@login_required
@user_passes_test(is_administrador)
def plantilla_list(request):
    """Muestra el listado de todas las plantillas de inspección."""
    plantillas = PlantillaInspeccion.objects.all().order_by('nombre')
    return render(request, 'dashboards/admin/plantilla_list.html', {'object_list': plantillas})


@login_required
@user_passes_test(is_administrador)
def plantilla_crear(request):
    """Permite crear una nueva Plantilla de Inspección junto con sus Tareas asociadas."""
    TareaFormSet = inlineformset_factory(
        PlantillaInspeccion, TareaPlantilla, form=TareaPlantillaForm, extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = PlantillaInspeccionForm(request.POST)
        formset = TareaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    plantilla = form.save()
                    formset.instance = plantilla
                    formset.save() # Guarda todas las tareas (nuevas, modificadas y eliminadas)
                    messages.success(request, f"Plantilla '{plantilla.nombre}' creada con éxito.")
                    return redirect('plantilla_list')
            except Exception as e:
                messages.error(request, f"Error al guardar la plantilla: {e}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
            
    else: # GET
        form = PlantillaInspeccionForm()
        formset = TareaFormSet()
        
    context = {
        'form': form,
        'formset': formset,
        'es_creacion': True,
    }
    return render(request, 'dashboards/admin/plantilla_form.html', context)


@login_required
@user_passes_test(is_administrador)
def plantilla_editar(request, pk):
    """Permite editar una Plantilla de Inspección existente y sus Tareas."""
    plantilla = get_object_or_404(PlantillaInspeccion, pk=pk)
    # Define el Formset
    TareaFormSet = inlineformset_factory(
        PlantillaInspeccion, TareaPlantilla, form=TareaPlantillaForm, extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = PlantillaInspeccionForm(request.POST, instance=plantilla)
        formset = TareaFormSet(request.POST, instance=plantilla)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save() # Guarda todas las tareas
                    messages.success(request, f"Plantilla '{plantilla.nombre}' actualizada con éxito.")
                    return redirect('plantilla_list')
            except Exception as e:
                messages.error(request, f"Error al actualizar la plantilla: {e}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")

    else: # GET
        form = PlantillaInspeccionForm(instance=plantilla)
        formset = TareaFormSet(instance=plantilla)

    context = {
        'form': form,
        'formset': formset,
        'plantilla': plantilla,
        'es_creacion': False,
    }
    return render(request, 'dashboards/admin/plantilla_form.html', context)


@login_required
@user_passes_test(is_administrador)
def plantilla_eliminar(request, pk):
    """Muestra la página de confirmación y elimina una plantilla."""
    plantilla = get_object_or_404(PlantillaInspeccion, pk=pk)

    # REGLA DE NEGOCIO: No eliminar si tiene inspecciones asociadas
    if Inspeccion.objects.filter(plantilla_base=plantilla).exists():
        messages.error(request, "No se puede eliminar la plantilla porque ya tiene inspecciones asociadas.")
        return redirect('plantilla_list')
    
    if request.method == 'POST':
        nombre = plantilla.nombre
        plantilla.delete()
        messages.success(request, f"Plantilla '{nombre}' eliminada correctamente.")
        return redirect('plantilla_list')

    return render(
        request,
        'dashboards/admin/plantilla_confirm_delete.html',
        {'object': plantilla},
    )

# ----------------------------------------------------------------------
# 🔧 Vistas de Técnico (ROL_TECNICO)
# ----------------------------------------------------------------------

@login_required
@user_passes_test(is_tecnico)
def dashboard_tecnico(request):
    inspecciones_asignadas = Inspeccion.objects.filter(
        tecnico=request.user,
        estado__in=['ASIGNADA', 'EN_CURSO']
    ).order_by('fecha_programada')

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

    # Define el Formset para las tareas, permitiendo editar estado y observación
    TareaFormSet = inlineformset_factory(
        Inspeccion, TareaInspeccion, fields=('estado', 'observacion'), extra=0, can_delete=False
    )

    if request.method == 'POST':
        formset = TareaFormSet(request.POST, instance=inspeccion)
        action = request.POST.get('action') # Puede ser 'guardar' o 'terminar'

        if formset.is_valid():
            with transaction.atomic():
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
                    messages.info(request, "Progreso guardado (Inspección iniciada).")
                    
                else: # Si ya está en EN_CURSO y no se terminó
                    messages.info(request, "Progreso guardado.")

                inspeccion.save()
                return redirect('dashboard_tecnico')
        else:
            messages.error(request, "Error al guardar el formulario de tareas.")

    else: # GET
        # Si la inspección está ASIGNADA, la marca como EN_CURSO al abrirla
        if inspeccion.estado == 'ASIGNADA':
            inspeccion.estado = 'EN_CURSO'
            inspeccion.save()
            
        formset = TareaFormSet(instance=inspeccion)
        
    context = {
        'inspeccion': inspeccion,
        'formset': formset
    }
    
    return render(request, 'dashboards/tecnico/completar_inspeccion.html', context)


@login_required
def descargar_acta(request, pk):
    """
    Vista placeholder temporal para la generación y descarga del PDF.
    Debe verificar que el usuario tenga permiso para ver esta acta.
    """
    try:
        inspeccion = get_object_or_404(Inspeccion, pk=pk)
        
        # Lógica de Permisos Unificada
        permiso = (
            request.user == inspeccion.tecnico or
            is_administrador(request.user) or
            (inspeccion.solicitud and request.user == inspeccion.solicitud.cliente)
        )
        
        if not permiso:
            messages.error(request, "No tiene permisos para ver esta acta de inspección.")
            return redirect('dashboard')
            
        # Si tiene permiso, se podría renderizar el HTML del PDF para la librería de generación
        # Aquí sólo se deja la estructura de la función original y un mensaje
        
        messages.info(request, "Implementación de generación de PDF pendiente. Se muestra un placeholder.")
        return render(request, 'documentos/acta_inspeccion_pdf_placeholder.html', {'inspeccion': inspeccion})


    except Exception as e:
        messages.error(request, f"Error al intentar obtener la inspección: {e}")
        return redirect('dashboard')