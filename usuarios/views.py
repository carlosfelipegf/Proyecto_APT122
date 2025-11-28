from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML

# --- Seguridad (Reset clave + token) ---
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode 

# --- Importación de formularios ---
from .forms import (
    AprobacionInspeccionForm, 
    SolicitudInspeccionForm,
    UsuarioAdminCreateForm, 
    UsuarioAdminUpdateForm,
    UsuarioPerfilForm, 
    TecnicoPerfilForm, 
    ClientePerfilForm,
    CambioClaveObligatorioForm,     # Seguridad
    PasswordResetRequestForm        # Seguridad
)

# --- Importación de modelos ---
from .models import (
    Notificacion,
    Inspeccion, 
    Perfil, 
    PlantillaInspeccion,
    Roles,
    EstadoSolicitud, 
    EstadoInspeccion, 
    EstadoTarea,
    SolicitudInspeccion, 
    TareaInspeccion, 
    TareaPlantilla
)

User = get_user_model()

# ==========================================================
# 1. LOGICA DE PERMISOS (Centralizada)
# ==========================================================

def check_role(user, role_name):
    return user.is_authenticated and user.groups.filter(name=role_name).exists()

def is_cliente(user): return check_role(user, Roles.CLIENTE)
def is_administrador(user): return check_role(user, Roles.ADMINISTRADOR) or user.is_superuser
def is_tecnico(user): return check_role(user, Roles.TECNICO)

# ==========================================================
# 2. AUTENTICACIÓN Y REDIRECCIÓN
# ==========================================================

def login_view(request):
    if request.user.is_authenticated:

        # 🔒 Redirección si NO ha cambiado la clave obligatoria
        if hasattr(request.user, "perfil") and not request.user.perfil.cambio_clave_inicial_completado:
            return redirect('cambiar_clave_obligatorio') 

        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)

            # 🔒 Chequeo cambio de clave obligatorio
            if hasattr(user, "perfil") and not user.perfil.cambio_clave_inicial_completado:
                return redirect('cambiar_clave_obligatorio')

            return redirect('dashboard')
        else:
            messages.error(request, "Usuario o contraseña incorrecta.")
    
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
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
    return render(request, 'nosotros.html')


# ==========================================================
# 3. SEGURIDAD: CAMBIO DE CLAVE OBLIGATORIO
# ==========================================================

@login_required
def cambiar_clave_obligatorio(request):

    user = request.user
    perfil = user.perfil

    if perfil.cambio_clave_inicial_completado:
        return redirect("dashboard")

    if request.method == 'POST':
        form = CambioClaveObligatorioForm(user, request.POST)
        if form.is_valid():
            form.save()

            perfil.cambio_clave_inicial_completado = True
            perfil.save()

            messages.success(request, "Contraseña actualizada correctamente.")
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Error: revisa los requisitos de seguridad.")
    else:
        form = CambioClaveObligatorioForm(user)

    return render(request, 'seguridad/cambio_clave_obligatorio.html', {
        'form': form
    })


# ==========================================================
# 4. SEGURIDAD: RESET DE CONTRASEÑA (TOKEN + EMAIL)
# ==========================================================

def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                user = None

            if user:
                current_site = get_current_site(request)
                subject = "Recuperación de Contraseña Optifire"

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                reset_url = reverse('password_reset_confirm', kwargs={
                    'uidb64': uid, 'token': token
                })

                full_url = f"http://{current_site.domain}{reset_url}"

                html_content = render_to_string(
                    'seguridad/password_reset_email.html', 
                    { 'user': user, 'reset_url': full_url }
                )

                email_message = EmailMultiAlternatives(
                    subject, html_content, to=[user.email]
                )
                email_message.attach_alternative(html_content, "text/html")
                email_message.send()

            messages.info(request, "Si el correo está registrado recibirás instrucciones.")
            return redirect('login')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'seguridad/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, uidb64, token):

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):

        if request.method == 'POST':
            form = CambioClaveObligatorioForm(user, request.POST)

            if form.is_valid():
                form.save()

                if hasattr(user, 'perfil'):
                    user.perfil.cambio_clave_inicial_completado = True
                    user.perfil.save()

                messages.success(request, "Contraseña restablecida. Puedes iniciar sesión.")
                return redirect('login')

        else:
            form = CambioClaveObligatorioForm(user)

        return render(request, 'seguridad/password_reset_confirm.html', {
            'form': form,
            'uidb64': uidb64,
            'token': token
        })
    
    messages.error(request, "El enlace es inválido o expiró.")
    return redirect('login')


# ==========================================================
# 5. VISTAS ADMINISTRADOR
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
    historial = SolicitudInspeccion.objects.exclude(
        estado=EstadoSolicitud.PENDIENTE
    ).order_by('-fecha_solicitud')

    return render(request, 'dashboards/admin/historial_solicitudes.html', {
        'historial': historial
    })


@login_required
@user_passes_test(is_administrador)
def admin_usuarios_list(request):
    usuarios = User.objects.all().order_by('username').prefetch_related('groups')

    usuarios_info = []
    for usuario in usuarios:
        grupo = usuario.groups.filter(name__in=[r.value for r in Roles]).first()
        usuarios_info.append({
            'obj': usuario,
            'rol': grupo.name if grupo else 'Sin rol'
        })

    return render(request, 'dashboards/admin/usuarios_list.html', {
        'usuarios_info': usuarios_info
    })


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

    return render(request, 'dashboards/admin/usuario_form.html', {
        'form': form,
        'es_creacion': True
    })


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

    return render(request, 'dashboards/admin/usuario_form.html', {
        'form': form,
        'es_creacion': False,
        'usuario_objetivo': usuario
    })


@login_required
@user_passes_test(is_administrador)
def admin_usuario_eliminar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, "Usuario eliminado.")
        return redirect('admin_usuarios_list')

    return render(request, 'dashboards/admin/usuario_confirm_delete.html', {
        'usuario_objetivo': usuario
    })


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
                            )
                            for tp in tareas_plantilla
                        ]
                        TareaInspeccion.objects.bulk_create(tareas_a_crear)

                        solicitud.estado = EstadoSolicitud.APROBADA
                        solicitud.save()

                        messages.success(request, f"Inspección asignada a {tecnico.username}")
                        return redirect('dashboard_administrador')

                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
            else:
                messages.error(request, "Faltan datos obligatorios.")

        elif action == 'rechazar':
            motivo = request.POST.get('motivo_rechazo')
            if motivo:
                solicitud.estado = EstadoSolicitud.RECHAZADA
                solicitud.motivo_rechazo = motivo
                solicitud.save()
                messages.warning(request, "Solicitud rechazada.")
                return redirect('dashboard_administrador')
            else:
                messages.error(request, "Indica un motivo de rechazo.")

    context = {
        'solicitud': solicitud,
        'tecnicos': User.objects.filter(groups__name=Roles.TECNICO),
        'plantillas': PlantillaInspeccion.objects.all()
    }
    return render(request, 'dashboards/admin/gestionar_solicitud.html', context)


# ==========================================================
# 6. VISTAS TÉCNICO
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
        fields=('estado', 'observacion', 'imagen_evidencia'),
        extra=0, can_delete=False
    )

    if request.method == 'POST':
        formset = TareaFormSet(request.POST, request.FILES, instance=inspeccion)

        if formset.is_valid():
            formset.save()

            inspeccion.comentarios_generales = request.POST.get('comentarios_generales')
            action = request.POST.get('action')

            if action == 'terminar':
                inspeccion.estado = EstadoInspeccion.COMPLETADA
                inspeccion.fecha_finalizacion = timezone.now()
                inspeccion.save()

                if inspeccion.solicitud:
                    inspeccion.solicitud.estado = EstadoSolicitud.COMPLETADA
                    inspeccion.solicitud.save()

                messages.success(request, "Inspección completada.")
                return redirect('dashboard_tecnico')

            else:
                if inspeccion.estado == EstadoInspeccion.ASIGNADA:
                    inspeccion.estado = EstadoInspeccion.EN_CURSO

                inspeccion.save()
                messages.success(request, "Progreso guardado (con fotos).")
                return redirect('dashboard_tecnico') 

    else:
        formset = TareaFormSet(instance=inspeccion)

    return render(request, 'dashboards/tecnico/completar_inspeccion.html', {
        'inspeccion': inspeccion,
        'formset': formset
    })


@login_required
@user_passes_test(is_tecnico)
def perfil_tecnico(request):
    usuario = request.user
    perfil, _ = Perfil.objects.get_or_create(usuario=usuario)

    if request.method == 'POST':
        user_form = UsuarioPerfilForm(request.POST, instance=usuario)
        perfil_form = TecnicoPerfilForm(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Perfil profesional actualizado correctamente.")
            return redirect('perfil_tecnico')
    else:
        user_form = UsuarioPerfilForm(instance=usuario)
        perfil_form = TecnicoPerfilForm(instance=perfil)

    return render(request, 'dashboards/tecnico/perfil.html', {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'perfil': perfil
    })


# ==========================================================
# 7. VISTAS CLIENTE
# ==========================================================

@login_required
@user_passes_test(is_cliente)
def dashboard_cliente(request):
    solicitudes = SolicitudInspeccion.objects.filter(
        cliente=request.user
    ).order_by('-fecha_solicitud')

    return render(request, 'dashboards/cliente_dashboard.html', {
        'solicitudes': solicitudes
    })


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
            messages.success(request, "Solicitud enviada.")
            return redirect('dashboard_cliente')

    else:
        form = SolicitudInspeccionForm()

    return render(request, 'dashboards/cliente/solicitar_inspeccion.html', {
        'form': form,
        'solicitudes': SolicitudInspeccion.objects.filter(cliente=request.user)
    })


@login_required
@user_passes_test(is_cliente)
def detalle_orden(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)

    try:
        inspeccion = solicitud.inspeccion
        tareas = inspeccion.tareas.all()
    except:
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
        solicitud.estado = EstadoSolicitud.ANULADA
        solicitud.save()
        messages.success(request, "Solicitud anulada.")
    else:
        messages.error(request, "No se puede anular esta solicitud.")

    return redirect('dashboard_cliente')


# ==========================================================
# 8. PERFIL GENERAL (CLIENTE)
# ==========================================================

@login_required
def editar_perfil(request):

    usuario = request.user
    perfil, _ = Perfil.objects.get_or_create(usuario=usuario)

    if request.method == 'POST':
        user_form = UsuarioPerfilForm(request.POST, instance=usuario)
        perfil_form = ClientePerfilForm(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()

            messages.success(request, "Perfil actualizado.")
            return redirect('editar_perfil')

    else:
        user_form = UsuarioPerfilForm(instance=usuario)
        perfil_form = ClientePerfilForm(instance=perfil)

    return render(request, 'perfil/perfil_editar.html', {
        'user_form': user_form,
        'perfil_form': perfil_form
    })


# ==========================================================
# 9. GENERAR ACTA PDF
# ==========================================================

@login_required
def descargar_acta(request, pk):

    inspeccion = get_object_or_404(Inspeccion, pk=pk)

    es_autorizado = (
        request.user == inspeccion.tecnico or
        request.user == inspeccion.solicitud.cliente or
        is_administrador(request.user)
    )

    if not es_autorizado:
        messages.error(request, "No tienes permiso para ver este documento.")
        return redirect('dashboard')

    html_string = render_to_string('pdf/acta_inspeccion.html', {
        'inspeccion': inspeccion,
        'tareas': inspeccion.tareas.all()
    })
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"Acta_OT_{inspeccion.id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    HTML(string=html_string).write_pdf(response)
    
    return response


# ==========================================================
# 10. NOTIFICACIONES
# ==========================================================

@login_required
def marcar_notificacion_leida(request, pk):

    if request.method == 'GET':
        notif = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
        notif.leido = True
        notif.save()
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=400)
