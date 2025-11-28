from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

# 🚨 MODELOS CORRECTOS
from .models import (
    SolicitudInspeccion, 
    EstadoSolicitud, 
    Notificacion,
    TareaInspeccion,
    Inspeccion,
    Roles
)

User = get_user_model()

# =========================================================================
# 1. CACHE ESTADO ANTERIOR (SolicitudInspeccion)
# =========================================================================
@receiver(pre_save, sender=SolicitudInspeccion)
def cache_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = SolicitudInspeccion.objects.get(pk=instance.pk)
            instance._original_estado = old_instance.estado
        except SolicitudInspeccion.DoesNotExist:
            instance._original_estado = None
    else:
        instance._original_estado = None


# =========================================================================
# 2. NOTIFICACIONES + CORREO (SolicitudInspeccion)
# =========================================================================
@receiver(post_save, sender=SolicitudInspeccion)
def notificar_cambio_estado(sender, instance, created, **kwargs):

    # -----------------------------
    # 2.1 CLIENTE CREA ORDEN (CORREGIDO)
    # -----------------------------
    if created:
        admins = User.objects.filter(groups__name=Roles.ADMINISTRADOR)
        
        # 🚨 CORRECCIÓN: Usamos 'detalle_orden' que SÍ existe y toma PK (o fallback seguro).
        try:
            # Esta URL lleva al detalle de la solicitud, que el Admin usa para gestionar.
            url_gestion = reverse('detalle_orden', kwargs={'pk': instance.pk}) 
        except:
            # Fallback a la URL principal del Admin
            url_gestion = reverse('dashboard_administrador') 

        for admin in admins:
            Notificacion.objects.create(
                usuario=admin,
                mensaje=f"🔔 Nueva Solicitud (OT#{instance.pk}) de {instance.cliente.username} pendiente de revisión.",
                enlace=url_gestion
            )
        return

    # -----------------------------
    # 2.2 CAMBIO DE ESTADO
    # -----------------------------
    estado_anterior = getattr(instance, '_original_estado', None)
    nuevo_estado = instance.estado

    if estado_anterior == nuevo_estado or estado_anterior is None:
        return

    # Enlace para el cliente (Detalle de la orden)
    try:
        url_detalle = reverse('detalle_orden', kwargs={'pk': instance.pk})
    except:
        url_detalle = reverse('dashboard_cliente') # Fallback

    # --------------------------------------------------
    # Aprobada (notificación interna)
    # --------------------------------------------------
    if nuevo_estado == EstadoSolicitud.APROBADA:
        Notificacion.objects.create(
            usuario=instance.cliente,
            mensaje=f"✅ Su Solicitud (OT#{instance.pk}) ha sido APROBADA y está en proceso de asignación.",
            enlace=url_detalle
        )

    # --------------------------------------------------
    # Rechazada
    # --------------------------------------------------
    elif nuevo_estado == EstadoSolicitud.RECHAZADA:
        Notificacion.objects.create(
            usuario=instance.cliente,
            mensaje=f"❌ Su Solicitud (OT#{instance.pk}) ha sido RECHAZADA.",
            enlace=url_detalle
        )

    # --------------------------------------------------
    # Anulada por el cliente (CORREGIDO)
    # --------------------------------------------------
    elif nuevo_estado == EstadoSolicitud.ANULADA:
        admins = User.objects.filter(groups__name=Roles.ADMINISTRADOR)
        
        # 🚨 CORRECCIÓN: Usamos 'detalle_orden' que sí existe.
        try:
            url_gestion = reverse('detalle_orden', kwargs={'pk': instance.pk}) 
        except:
            url_gestion = reverse('dashboard_administrador') 

        for admin in admins:
            Notificacion.objects.create(
                usuario=admin,
                mensaje=f"⛔ Solicitud (OT#{instance.pk}) ANULADA por el cliente {instance.cliente.username}.",
                enlace=url_gestion
            )

    # =========================================================================
    # 2.3 CORREOS
    # =========================================================================
    context = {'solicitud': instance, 'base_url': 'http://127.0.0.1:8000/usuarios/'}
    asunto = ""
    html_template = None
    text_template = None

    if nuevo_estado == EstadoSolicitud.APROBADA:
        asunto = f"Solicitud N°{instance.pk} Aprobada y Asignada"
        # 🚨 CORRECCIÓN CLAVE: Asegurarse de que 'inspeccion' exista antes de acceder a ella
        try:
            context['tecnico_nombre'] = instance.inspeccion.tecnico.get_full_name()
        except Inspeccion.DoesNotExist:
            # Si no hay inspección (porque la vista aún no la ha creado), usar un fallback
            context['tecnico_nombre'] = "Un técnico asignado" 
            
        html_template = 'email/solicitud_aprobada.html'
        text_template = 'email/solicitud_aprobada_text.txt'

    elif nuevo_estado == EstadoSolicitud.RECHAZADA:
        asunto = f"Solicitud N°{instance.pk} Rechazada"
        html_template = 'email/solicitud_rechazada.html'
        text_template = 'email/solicitud_rechazada_text.txt'

    elif nuevo_estado == EstadoSolicitud.COMPLETADA:
        # 🚨 CORRECCIÓN CLAVE: Si se completa la Solicitud, es porque la Inspeccion se completó
        # Verificamos que la Inspeccion exista antes de acceder a su PK
        try:
            asunto = f"Inspección N°{instance.inspeccion.pk} Finalizada"
        except:
            asunto = f"Inspección Finalizada (OT#{instance.pk})"
            
        html_template = 'email/inspeccion_completada.html'
        text_template = 'email/inspeccion_completada_text.txt'

    else:
        return 

    # Envío de correo
    destinatario = instance.cliente.email
    if destinatario:
        try:
            msg_plain = render_to_string(text_template, context)
            msg_html = render_to_string(html_template, context)

            msg = EmailMultiAlternatives(
                subject=asunto,
                body=msg_plain,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destinatario],
            )
            msg.attach_alternative(msg_html, "text/html")
            msg.send()

            print(f"📧 CORREO ENVIADO A {destinatario}")

        except Exception as e:
            print(f"ERROR AL ENVIAR CORREO: {e}")


# =========================================================================
# 3. NOTIFICACIONES INSPECCIÓN (Asignación y Finalización)
# =========================================================================
@receiver(post_save, sender=Inspeccion)
def notificar_inspeccion_creada_o_completada(sender, instance, created, **kwargs):

    estado_anterior = None
    if not created:
        try:
            old_instance = Inspeccion.objects.get(pk=instance.pk)
            estado_anterior = old_instance.estado
        except Inspeccion.DoesNotExist:
            pass

    # ---------------------------------------------
    # 3.1 ASIGNADA AL TÉCNICO
    # ---------------------------------------------
    # Asignada al crearla o al cambiar su estado a ASIGNADA
    if created or (estado_anterior != instance.estado and instance.estado == instance.ASIGNADA):
        url_tecnico = reverse('completar_inspeccion', kwargs={'pk': instance.pk})

        Notificacion.objects.create(
            usuario=instance.tecnico,
            mensaje=f"🛠️ ¡Nueva Orden Asignada! (OT#{instance.solicitud.pk}): {instance.nombre_inspeccion}.",
            enlace=url_tecnico
        )

    # ---------------------------------------------
    # 3.2 COMPLETADA
    # ---------------------------------------------
    if instance.estado == instance.COMPLETADA and estado_anterior != instance.COMPLETADA:

        solicitud = instance.solicitud
        url_acta = reverse('descargar_acta', kwargs={'pk': instance.pk})

        # Cliente
        Notificacion.objects.create(
            usuario=solicitud.cliente,
            mensaje=f"🎉 ¡Orden de Trabajo (OT#{solicitud.pk}) TERMINADA! Descarga el acta.",
            enlace=url_acta
        )

        # Administradores
        admins = User.objects.filter(groups__name=Roles.ADMINISTRADOR)
        for admin in admins:
            Notificacion.objects.create(
                usuario=admin,
                mensaje=f"✅ OT#{solicitud.pk} completada por {instance.tecnico.username}.",
                enlace=url_acta
            )


# =========================================================================
# 4. NOTIFICACIÓN POR EVIDENCIA (Foto subida)
# =========================================================================
@receiver(pre_save, sender=TareaInspeccion)
def cache_tarea_foto(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = TareaInspeccion.objects.get(pk=instance.pk)
            instance._original_imagen = old.imagen_evidencia
        except TareaInspeccion.DoesNotExist:
            instance._original_imagen = None
    else:
        instance._original_imagen = None


@receiver(post_save, sender=TareaInspeccion)
def crear_notificacion_evidencia(sender, instance, created, **kwargs):

    if not instance.imagen_evidencia:
        return
    if instance.imagen_evidencia == getattr(instance, '_original_imagen', None):
        return

    try:
        inspeccion = instance.inspeccion
        solicitud = inspeccion.solicitud
        cliente = solicitud.cliente
        
        # Usamos reverse para generar la URL si es posible
        try:
            url_orden = reverse('detalle_orden', kwargs={'pk': solicitud.pk})
        except:
            # Fallback manual por si la URL no existe
            url_orden = f"/usuarios/solicitud/detalle/{solicitud.pk}/" 

        Notificacion.objects.create(
            usuario=cliente,
            mensaje=f"📸 Nueva evidencia cargada: {instance.descripcion}",
            enlace=url_orden
        )

        print(f"🔔 NOTIFICACIÓN CREADA PARA {cliente.username}: Foto nueva.")

    except Exception as e:
        print(f"ERROR AL CREAR NOTIFICACIÓN: {e}")