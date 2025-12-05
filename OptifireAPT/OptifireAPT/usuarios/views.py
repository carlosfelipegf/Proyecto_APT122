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
from django.http import JsonResponse
from .models import Notificacion 
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Count, Q # <--- IMPORTANTE: Q es necesario
import datetime

# Importamos formularios
from .forms import (
    AprobacionInspeccionForm, 
    SolicitudInspeccionForm,
    UsuarioAdminCreateForm, 
    UsuarioAdminUpdateForm,
    UsuarioPerfilForm, 
    TecnicoPerfilForm, 
    ClientePerfilForm,
    AdminPerfilForm, # <--- CORRECTO: Formulario para el perfil admin
)

# Importamos los Modelos
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
# 2. AUTENTICACIÓN Y REDIRECCIÓN (CON DIAGNÓSTICO)
# ==========================================================
def login_view(request):
    """
    Login Robusto con Diagnóstico en Consola.
    """
    if request.user.is_authenticated:
        if hasattr(request.user, 'perfil') and request.user.perfil.obligar_cambio_contrasena:
            return redirect('cambiar_password_forzado')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # 1. Obtener datos (Soporta 'username' del HTML aunque el usuario escriba email)
        user_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # --- INICIO DIAGNÓSTICO ---
        print("\n" + "="*40)
        print("🔍 INTENTO DE LOGIN - DEBUG")
        print(f"   Input Usuario: '{user_input}'")
        
        if not user_input or not password:
            messages.error(request, "Ingrese credenciales válidas.")
            return render(request, "login.html")

        # 2. BÚSQUEDA HÍBRIDA (Username O Email)
        # Busca coincidencias ignorando mayúsculas/minúsculas
        posibles_usuarios = User.objects.filter(
            Q(username__iexact=user_input) | Q(email__iexact=user_input)
        )
        
        print(f"   Usuarios encontrados en DB: {posibles_usuarios.count()}")

        user = None
        
        # 3. ITERACIÓN DE SEGURIDAD (Manejo de duplicados)
        if posibles_usuarios.exists():
            for usuario_db in posibles_usuarios:
                print(f"   -> Probando con usuario: '{usuario_db.username}' (ID: {usuario_db.pk})")
                
                # Intentar autenticar
                auth_user = authenticate(request, username=usuario_db.username, password=password)
                
                if auth_user is not None:
                    print("   -> ✅ AUTHENTICATE EXITOSO")
                    user = auth_user
                    break # Éxito, salir del bucle
                else:
                    # Diagnóstico extra: ¿Por qué falló?
                    pass_manual = usuario_db.check_password(password)
                    if pass_manual:
                        print("   -> ⚠️ CONTRASEÑA CORRECTA pero usuario INACTIVO o bloqueado.")
                    else:
                        print("   -> ❌ CONTRASEÑA INCORRECTA")
        else:
            print("   -> ❌ NO EXISTE EL USUARIO EN BD")

        print("="*40 + "\n")
        # --- FIN DIAGNÓSTICO ---

        if user is not None:
            login(request, user)
            # Validación cambio password forzado
            if hasattr(user, 'perfil') and user.perfil.obligar_cambio_contrasena:
                messages.info(request, "Por seguridad, debes cambiar tu contraseña.")
                return redirect('cambiar_password_forzado')
            return redirect('dashboard')
        else:
            messages.error(request, "Credenciales incorrectas. Verifique usuario/correo y contraseña.")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Validación de seguridad extra
    if hasattr(request.user, "perfil") and request.user.perfil.obligar_cambio_contrasena:
        messages.warning(request, "Debe cambiar su contraseña obligatoriamente para acceder al sistema.")
        return redirect("cambiar_password_forzado")

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

# --- INICIO AGREGADO: PERFIL ADMINISTRATIVO ---
@login_required
@user_passes_test(is_administrador)
def perfil_administrador(request):
    """Vista para que el Admin edite su propio perfil."""
    # Obtener o crear el perfil
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        # Pasamos request.FILES para poder subir la imagen
        form = AdminPerfilForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Tu perfil administrativo ha sido actualizado!')
            return redirect('perfil_administrador')
    else:
        form = AdminPerfilForm(instance=perfil, user=request.user)

    # Renderizamos pasando AMBOS: el formulario y el objeto perfil para asegurar que el HTML tenga datos
    return render(request, 'usuarios/perfil_administrador.html', {
        'form': form,
        'perfil': perfil 
    })
# --- FIN AGREGADO ---

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
    usuario_a_eliminar = get_object_or_404(User, pk=pk)

    if usuario_a_eliminar == request.user:
        messages.error(request, "No puedes eliminar tu propia cuenta de administrador mientras la usas.")
        return redirect('admin_usuarios_list')

    if request.method == 'POST':
        nombre = usuario_a_eliminar.username
        usuario_a_eliminar.delete()
        messages.success(request, f"El usuario administrador '{nombre}' ha sido eliminado correctamente.")
        return redirect('admin_usuarios_list')

    return render(request, 'dashboards/admin/usuario_confirm_delete.html', {
        'usuario_objetivo': usuario_a_eliminar
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
            monto_cotizacion = request.POST.get('monto_cotizacion')

            if all([tecnico_id, plantilla_id, nombre_inspeccion, monto_cotizacion]):
                try:
                    with transaction.atomic():
                        tecnico = User.objects.get(pk=tecnico_id)
                        plantilla = PlantillaInspeccion.objects.get(pk=plantilla_id)

                        solicitud.monto_cotizacion = monto_cotizacion
                        solicitud.detalle_cotizacion = f"Cotización generada por el administrador."
                        solicitud.tecnico_preasignado = tecnico
                        solicitud.plantilla_preasignada = plantilla
                        solicitud.nombre_inspeccion_preasignado = nombre_inspeccion
                        solicitud.fecha_programada_preasignada = fecha_programada if fecha_programada else None
                        solicitud.estado = EstadoSolicitud.COTIZANDO
                        solicitud.save()

                        messages.success(request, "Cotización enviada al cliente para su aprobación.")
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
def registro_trabajos(request):
    inspecciones = Inspeccion.objects.filter(
        tecnico=request.user,
        estado=EstadoInspeccion.COMPLETADA
    ).select_related('solicitud').order_by('-fecha_finalizacion')

    return render(request, 'dashboards/tecnico/registro_trabajos.html', {
        'inspecciones_completadas': inspecciones
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
# 5. VISTAS CLIENTE
# ==========================================================

@login_required
@user_passes_test(is_cliente)
def dashboard_cliente(request):
    solicitudes = SolicitudInspeccion.objects.filter(cliente=request.user).order_by('-fecha_solicitud')
    return render(request, 'dashboards/cliente_dashboard.html', {'solicitudes': solicitudes})


@login_required
@user_passes_test(is_cliente)
def aceptar_cotizacion_cliente(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk, cliente=request.user)
    if solicitud.estado != EstadoSolicitud.COTIZANDO:
        messages.error(request, "Esta solicitud no está pendiente de cotización.")
        return redirect('dashboard_cliente')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'aceptar':
            tecnico = solicitud.tecnico_preasignado
            plantilla = solicitud.plantilla_preasignada
            nombre_inspeccion = solicitud.nombre_inspeccion_preasignado
            fecha_programada = solicitud.fecha_programada_preasignada
            if all([tecnico, plantilla, nombre_inspeccion]):
                try:
                    with transaction.atomic():
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
                        solicitud.tecnico_preasignado = None
                        solicitud.plantilla_preasignada = None
                        solicitud.nombre_inspeccion_preasignado = None
                        solicitud.fecha_programada_preasignada = None
                        solicitud.save()
                        
                        for admin in User.objects.filter(groups__name=Roles.ADMINISTRADOR):
                            Notificacion.objects.create(
                                usuario=admin,
                                mensaje=f"El cliente {solicitud.cliente.username} aceptó la cotización de la solicitud #{solicitud.pk}.",
                                enlace=f"/usuarios/solicitud/detalle/{solicitud.pk}/"
                            )
                        Notificacion.objects.create(
                            usuario=tecnico,
                            mensaje=f"Te han asignado una nueva inspección por aceptación de cotización (solicitud #{solicitud.pk}).",
                            enlace=f"/usuarios/inspeccion/completar/{nueva_inspeccion.pk}/"
                        )
                        messages.success(request, "Cotización aceptada. Inspección asignada al técnico.")
                        return redirect('dashboard_cliente')
                except Exception as e:
                    messages.error(request, f"Error al crear inspección: {str(e)}")
            else:
                messages.error(request, "Faltan datos de preasignación. Contacte al administrador.")
        elif action == 'rechazar':
            solicitud.estado = EstadoSolicitud.RECHAZADA
            solicitud.save()
            
            for admin in User.objects.filter(groups__name=Roles.ADMINISTRADOR):
                Notificacion.objects.create(
                    usuario=admin,
                    mensaje=f"El cliente {solicitud.cliente.username} rechazó la cotización de la solicitud #{solicitud.pk}.",
                    enlace=f"/usuarios/solicitud/detalle/{solicitud.pk}/"
                )
            messages.warning(request, "Has rechazado la cotización. La solicitud ha sido cancelada.")
            return redirect('dashboard_cliente')

    return render(request, 'dashboards/cliente/aceptar_cotizacion.html', {'solicitud': solicitud})

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
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('editar_perfil')
    else:
        user_form = UsuarioPerfilForm(instance=usuario)
        perfil_form = ClientePerfilForm(instance=perfil)
        
    return render(request, 'perfil/perfil_editar.html', {
        'user_form': user_form, 
        'perfil_form': perfil_form
    })

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

@login_required
def marcar_notificacion_leida(request, pk):
    if request.method == 'GET':
        notif = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
        notif.leido = True
        notif.save()
        return JsonResponse({'status': 'ok', 'mensaje': 'Notificación marcada como leída'})
    
    return JsonResponse({'status': 'error'}, status=400)

class CambioContrasenaForzadoView(PasswordChangeView):
    template_name = 'registration/password_change_force.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        
        perfil = self.request.user.perfil
        perfil.obligar_cambio_contrasena = False
        perfil.save()
        
        update_session_auth_hash(self.request, self.request.user)
        
        messages.success(self.request, "Tu contraseña ha sido actualizada. ¡Bienvenido!")
        return response

@login_required
@user_passes_test(is_administrador)
def enviar_orden_facturacion(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk)
    
    if not solicitud.monto_cotizacion:
        messages.error(request, "Error: Esta solicitud no tiene un monto cotizado asignado.")
        return redirect('dashboard_administrador')

    monto_neto = int(solicitud.monto_cotizacion)
    monto_iva = int(monto_neto * getattr(settings, 'IVA_CHILE', 0.19))
    monto_total = monto_neto + monto_iva

    context = {
        'solicitud': solicitud,
        'monto_neto': monto_neto,
        'monto_iva': monto_iva,
        'monto_total': monto_total,
    }

    html_string = render_to_string('pdf/orden_facturacion.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    asunto = f"Orden de Facturación - OT #{solicitud.id} - {solicitud.nombre_cliente}"
    mensaje = f"""
    Estimado equipo de Cobranzas,

    Adjunto encontrará la orden de facturación para el servicio realizado.

    Cliente: {solicitud.nombre_cliente}
    Monto Neto: ${monto_neto}
    OT: #{solicitud.id}

    Favor proceder con la emisión del DTE (Factura).
    """
    
    email_destino = getattr(settings, 'EMAIL_COBRANZA_DESTINO', 'admin@localhost')

    try:
        email = EmailMessage(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email_destino],
        )
        email.attach(f'Orden_Facturacion_{solicitud.id}.pdf', pdf_file, 'application/pdf')
        email.send()
        
        messages.success(request, f"Orden de facturación enviada correctamente a {email_destino}")
        
    except Exception as e:
        messages.error(request, f"Error al enviar correo: {e}")

    return redirect('dashboard_administrador')

@login_required
def estadisticas_view(request):
    user = request.user
    role = None
    context = {}

    if is_administrador(user):
        role = 'admin'
    elif is_tecnico(user):
        role = 'tecnico'
    elif is_cliente(user):
        role = 'cliente'

    if role == 'admin':
        hoy = timezone.now()
        hace_una_semana = hoy - datetime.timedelta(days=7)
        ots_semanales = SolicitudInspeccion.objects.filter(
            fecha_solicitud__gte=hace_una_semana
        ).extra(select={'day': 'date(fecha_solicitud)'}).values('day').annotate(count=Count('id')).order_by('day')

        tecnicos_carga = User.objects.filter(groups__name='Técnico').annotate(
            carga_trabajo=Count('inspecciones_asignadas', filter=Q(inspecciones_asignadas__estado__in=['ASIGNADA', 'EN_CURSO']))
        ).order_by('carga_trabajo')

        estados_globales = SolicitudInspeccion.objects.values('estado').annotate(total=Count('estado'))

        context = {
            'role': 'admin',
            'labels_semana': [entry['day'] for entry in ots_semanales],
            'data_semana': [entry['count'] for entry in ots_semanales],
            'labels_tecnicos': [t.username for t in tecnicos_carga],
            'data_carga': [t.carga_trabajo for t in tecnicos_carga],
            'labels_estados': [e['estado'] for e in estados_globales],
            'data_estados': [e['total'] for e in estados_globales],
        }

    elif role == 'tecnico':
        mis_inspecciones = Inspeccion.objects.filter(tecnico=user)
        resumen = mis_inspecciones.values('estado').annotate(total=Count('estado'))
        context = {
            'role': 'tecnico',
            'labels_estado': [item['estado'] for item in resumen],
            'data_estado': [item['total'] for item in resumen],
            'total_completadas': mis_inspecciones.filter(estado='COMPLETADA').count()
        }

    elif role == 'cliente':
        mis_solicitudes = SolicitudInspeccion.objects.filter(cliente=user)
        resumen = mis_solicitudes.values('estado').annotate(total=Count('estado'))
        context = {
            'role': 'cliente',
            'labels_solicitudes': [item['estado'] for item in resumen],
            'data_solicitudes': [item['total'] for item in resumen],
        }

    return render(request, 'dashboards/estadisticas.html', context)

def api_disponibilidad_tecnico(request, tecnico_id):
    ocupadas = Inspeccion.objects.filter(
        tecnico_id=tecnico_id,
        estado__in=[EstadoInspeccion.ASIGNADA, EstadoInspeccion.EN_CURSO],
        fecha_programada__isnull=False
    ).values_list('fecha_programada', flat=True)
    return JsonResponse({'fechas_ocupadas': [f.strftime('%Y-%m-%d') for f in ocupadas]})

@login_required
@user_passes_test(is_administrador)
def ver_detalle_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudInspeccion, pk=pk)
    inspeccion = Inspeccion.objects.filter(solicitud=solicitud).first()
    
    context = {
        'solicitud': solicitud,
        'inspeccion': inspeccion
    }
    
    return render(request, 'dashboards/detalle_solicitud_admin.html', context)