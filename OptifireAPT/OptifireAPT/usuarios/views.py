# ==========================================================
# views.py - CÓDIGO COMPLETO (CORREGIDO DE U+00A0)
# ==========================================================

from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import Group

# 🔥 IMPORTACIONES CORREGIDAS (Añadir UsuarioEditForm, PerfilEditForm y PlantillaForm) 🔥
from .forms import (
    AprobacionInspeccionForm,
    SolicitudInspeccionForm,
    UsuarioAdminCreateForm,
    UsuarioAdminUpdateForm,
    UsuarioEditForm,
    PerfilEditForm,
    RequiredPasswordChangeForm,
    PlantillaInspeccionForm,
    TareaPlantillaForm,
)

# 🔥 ACTUALIZADO: Importaciones de modelos
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

# ==========================================================
# 1. FUNCIONES DE PERMISOS
# ==========================================================
def get_user_role(user):
    """
    Determina el rol principal del usuario basado en sus grupos.
    Se apoya en la propiedad get_role() del modelo Perfil.
    """
    if user.is_anonymous:
        return None
    
    # 🔥 USAR LA PROPIEDAD DEL MODELO PERFIL 🔥
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
            
            # 🔥 Lógica de la bandera usando el modelo Perfil 🔥
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

# ==========================================================
# CÓDIGO PARA EL CAMBIO DE CONTRASEÑA OBLIGATORIO
# ==========================================================

@login_required
def change_password_required_view(request):
    """
    Vista para manejar el cambio de contraseña obligatorio.
    """
    user = request.user
    
    # 🔥 OBTENER EL PERFIL UNIFICADO 🔥
    try:
        perfil = user.perfil
    except Perfil.DoesNotExist:
        perfil, created = Perfil.objects.get_or_create(usuario=user)
    
    
    # Si la contraseña ya fue cambiada Y no se accedió directamente a la URL 'change_password_required'
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
            
            # Redirección por Rol
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
    
    else:
        # Se podría usar RequiredPasswordChangeForm aquí para ocultar el campo de contraseña actual
        # si se implementa, pero PasswordChangeForm es el estándar de Django para cambiar.
        form = PasswordChangeForm(user)

    return render(request, 'auth/change_password_required.html', {'form': form, 'es_obligatorio': perfil.cambio_contrasena_obligatorio})


# ==========================================================
# 2. DASHBOARD PRINCIPAL (Redirige por Rol)
# ==========================================================
@login_required
def dashboard(request):
    # 🔥 Chequeo de la bandera usando el modelo Perfil 🔥
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


# ==========================================================
# 🔥 2.1. VISTA UNIFICADA PARA EDITAR EL PERFIL (CORREGIDA) 🔥
# ==========================================================
@login_required
def editar_perfil_view(request):
    """
    Permite a cualquier usuario autenticado editar la información básica (User)
    y la información adicional (Perfil) en una sola vista.
    """
    usuario_instance = request.user
    # Obtener la instancia de Perfil a editar (debe existir gracias al signal)
    perfil_instance, created = Perfil.objects.get_or_create(usuario=usuario_instance)
    
    # 🔥 LÓGICA DE GRUPOS MOVIDA A PYTHON (para el template) 🔥
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
        'user_form': user_form,       # Para nombre, apellido, email
        'perfil_form': perfil_form,   # Para foto, descripcion, telefono
        'group_names': group_names,   # Para mostrar el rol en el template
        'rol': get_user_role_display(request.user) # Rol legible
    }
    
    # CORRECCIÓN APLICADA: Asegura la ruta de la plantilla si está en un subdirectorio.
    return render(request, 'perfil/perfil_editar.html', context)


# ==========================================================
# 3. VISTAS DEL CLIENTE
# ==========================================================
@login_required
@user_passes_test(is_cliente)
def dashboard_cliente(request):
    # Se asume que 'solicitud.estado' puede ser 'ANULADA'
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
    # La función eliminar_solicitud ya no es necesaria si usamos 'anular_solicitud',
    # pero la dejo si tienes código que todavía la usa para solicitudes que no son PENDIENTE.
    # **NOTA:** En la plantilla del cliente anterior, se usaba 'eliminar_solicitud' para PENDIENTE.
    # Es más claro usar 'anular_solicitud' para mantener la trazabilidad.
    messages.warning(request, "Usar 'anular_solicitud' para solicitudes pendientes para mantener la trazabilidad.")
    return redirect('dashboard_cliente')


@login_required
@user_passes_test(is_cliente)
def anular_solicitud(request, pk):
    """
    Permite al cliente cambiar el estado de una solicitud de 'PENDIENTE' a 'ANULADA'.
    Esto reemplaza la lógica de 'eliminar' para mantener un registro histórico.
    """
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    
    # Solo permitir anular si el estado es PENDIENTE
    if solicitud.estado == 'PENDIENTE':
        if request.method == 'GET' or request.method == 'POST':
            # 💡 NOTA: Por seguridad, en producción deberías usar un formulario POST con CSRF.
            # Aquí se acepta GET dado que la confirmación se hace en el JS de la plantilla.
            solicitud.estado = 'ANULADA'
            # Se podría añadir un campo de motivo de anulación al modelo si es necesario.
            solicitud.save()
            messages.success(request, f"La Orden de Trabajo #{pk} ha sido anulada con éxito.")
            return redirect('dashboard_cliente')
        else:
            messages.error(request, "Método no permitido.")
    else:
        messages.error(request, f"La Orden de Trabajo #{pk} no puede ser anulada. Su estado actual es: {solicitud.get_estado_display()}.")
    
    return redirect('dashboard_cliente')


@login_required
@user_passes_test(is_cliente)
def detalle_orden(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
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
        
        # Obtener el rol real del modelo Perfil para mostrar en la lista
        rol_display = 'Sin rol'
        try:
            rol_display = usuario.perfil.get_role()
        except Perfil.DoesNotExist:
            pass # Usará 'Sin rol'
        
        usuarios_info.append({
            'obj': usuario,
            # Usamos el rol de perfil si está disponible, sino el del grupo.
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
            # Crear el usuario (el signal creará el Perfil)
            nuevo_usuario = form.save()
            
            # El signal crea el Perfil automáticamente con cambio_contrasena_obligatorio=True.
            
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
# 4.1. VISTAS DE GESTIÓN DE PLANTILLAS (ADMIN)
# ==========================================================
@login_required
@user_passes_test(is_administrador)
def plantilla_list(request):
    """Muestra el listado de todas las plantillas de inspección."""
    plantillas = PlantillaInspeccion.objects.all().order_by('nombre')
    # Se pasa 'object_list' para ser compatible con el template genérico
    return render(request, 'dashboards/admin/plantilla_list.html', {'object_list': plantillas})


@login_required
@user_passes_test(is_administrador)
def plantilla_crear(request):
    """Permite crear una nueva Plantilla de Inspección junto con sus Tareas asociadas."""
    # Define el Formset para las tareas de la plantilla
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
    # Define el Formset (igual que en crear)
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
                    formset.save() # Guarda todas las tareas (nuevas, modificadas y eliminadas)
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

    # 🛑 Validación de integridad referencial
    if Inspeccion.objects.filter(plantilla_base=plantilla).exists():
        messages.error(request, "No se puede eliminar la plantilla porque ya tiene inspecciones asociadas. Si necesita ocultarla, puede añadir un campo 'activo' en el modelo.")
        return redirect('plantilla_list')
    
    if request.method == 'POST':
        nombre = plantilla.nombre
        plantilla.delete()
        messages.success(request, f"Plantilla '{nombre}' eliminada correctamente.")
        return redirect('plantilla_list')

    return render(
        request,
        'dashboards/admin/plantilla_confirm_delete.html',
        {'object': plantilla}, # Usar 'object' o 'plantilla' es común en Django
    )


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

    # Se usa 'fields=('estado', 'observacion')' para permitir al técnico llenar los datos.
    TareaFormSet = inlineformset_factory(
        Inspeccion, TareaInspeccion, fields=('estado', 'observacion'), extra=0, can_delete=False
    )

    if request.method == 'POST':
        formset = TareaFormSet(request.POST, instance=inspeccion)
        action = request.POST.get('action')

        if formset.is_valid():
            # Iniciar transacción para asegurar atomicidad
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
                    # Si es la primera vez que guarda y está "ASIGNADA", pasa a "EN_CURSO"
                    inspeccion.estado = 'EN_CURSO'
                    messages.info(request, "Progreso guardado (Inspección iniciada).")
                    
                else: # Si ya está en EN_CURSO y no se terminó
                    messages.info(request, "Progreso guardado.")

                inspeccion.save()
                return redirect('dashboard_tecnico')
        else:
            messages.error(request, "Error al guardar el formulario de tareas.")

    else: # GET
        # Al iniciar, si está ASIGNADA, la ponemos en EN_CURSO
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
    """
    try:
        inspeccion = Inspeccion.objects.get(pk=pk)
        
        # Permisos mejorados: Técnico asignado, Admin, o Cliente solicitante
        permiso = (
            request.user == inspeccion.tecnico or
            is_administrador(request.user) or
            (inspeccion.solicitud and request.user == inspeccion.solicitud.cliente)
        )
        
        if not permiso:
            messages.error(request, "No tiene permisos para descargar este acta.")
            return redirect('dashboard')
            
        # TODO: Implementar lógica de generación de PDF aquí (usando ReportLab, xhtml2pdf, etc.).
        messages.info(request, f"Función para descargar el Acta de Inspección #{pk} aún no implementada. Redirigiendo a detalle.")
        
        # Redirigir al detalle de la orden hasta que la funcionalidad esté lista
        if inspeccion.solicitud:
            return redirect('detalle_orden', pk=inspeccion.solicitud.pk)
        else:
            # Fallback si la inspección no tiene una solicitud de origen (caso raro)
            return redirect('dashboard')
    
    except Inspeccion.DoesNotExist:
        messages.error(request, "Inspección no encontrada.")
        return redirect('dashboard')