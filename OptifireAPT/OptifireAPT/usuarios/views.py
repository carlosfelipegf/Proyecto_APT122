from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

# Importamos formularios
from .forms import (
    AprobacionInspeccionForm, 
    SolicitudInspeccionForm,
    UsuarioAdminCreateForm, 
    UsuarioAdminUpdateForm,
    UsuarioPerfilForm, 
    PerfilForm
)

# Importamos los Modelos y las NUEVAS CLASES DE CONSTANTES
from .models import (
    Inspeccion, 
    Perfil, 
    PlantillaInspeccion,
    Roles,              # <--- Esto reemplaza a ROL_ADMINISTRADOR, etc.
    EstadoSolicitud,    # <--- Esto reemplaza a los strings 'PENDIENTE', etc.
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
    # Usamos .value para comparar con el string del nombre del grupo
    return user.is_authenticated and user.groups.filter(name=role_name).exists()

def is_cliente(user): return check_role(user, Roles.CLIENTE)
def is_administrador(user): return check_role(user, Roles.ADMINISTRADOR) or user.is_superuser
def is_tecnico(user): return check_role(user, Roles.TECNICO)

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
# 3. VISTAS ADMINISTRADOR
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
# 4. VISTAS TÉCNICO
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
                if inspeccion.solicitud:
                    inspeccion.solicitud.estado = EstadoSolicitud.COMPLETADA
                    inspeccion.solicitud.save()
                messages.success(request, "Inspección completada.")
                return redirect('dashboard_tecnico')
            else:
                if inspeccion.estado == EstadoInspeccion.ASIGNADA:
                    inspeccion.estado = EstadoInspeccion.EN_CURSO
                inspeccion.save()
                messages.success(request, "Progreso guardado.")
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
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        perfil.descripcion = request.POST.get('descripcion_profesional', '').strip()
        if request.FILES.get('foto'):
            perfil.foto = request.FILES['foto']
        perfil.save()
        messages.success(request, "Perfil actualizado.")
    
    return render(request, 'dashboards/tecnico/perfil.html', {'perfil': perfil})

# ==========================================================
# 5. VISTAS CLIENTE
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
    # Usamos el related_name 'inspeccion' definido en models.py (OneToOne)
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
        user_form = UsuarioPerfilForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)
    return render(request, 'perfil/perfil_editar.html', {'user_form': user_form, 'perfil_form': perfil_form})

@login_required
def descargar_acta(request, pk):
    # 1. Obtener la inspección
    inspeccion = get_object_or_404(Inspeccion, pk=pk)
    
    # 2. Validación de seguridad: Solo dueño, técnico o admin pueden verla
    es_autorizado = (
        request.user == inspeccion.tecnico or 
        request.user == inspeccion.solicitud.cliente or 
        is_administrador(request.user)
    )
    
    if not es_autorizado:
        messages.error(request, "No tienes permiso para ver este documento.")
        return redirect('dashboard')

    # 3. Generar el HTML en memoria usando el template que creamos
    html_string = render_to_string('pdf/acta_inspeccion.html', {
        'inspeccion': inspeccion,
        'tareas': inspeccion.tareas.all()
    })
    
    # 4. Convertir a PDF usando WeasyPrint
    response = HttpResponse(content_type='application/pdf')
    filename = f"Acta_OT_{inspeccion.id}.pdf"
    
    # 'inline' abre el PDF en el navegador. Si prefieres descarga directa, cambia a 'attachment'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    HTML(string=html_string).write_pdf(response)
    
    return response