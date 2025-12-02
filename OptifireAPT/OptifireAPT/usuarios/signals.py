from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

# 🚨 IMPORTACIONES CORREGIDAS: Están todos los modelos necesarios
from .models import (
    SolicitudInspeccion, 
    EstadoSolicitud, 
    Notificacion,     # Para el Pop-up
    TareaInspeccion   # Para detectar las fotos
)

# =========================================================================
# 1. LOGICA DE CORREOS (CAMBIO DE ESTADO SOLICITUD)
# =========================================================================

@receiver(pre_save, sender=SolicitudInspeccion)
def cache_old_status(sender, instance, **kwargs):
    if instance.pk: 
        try:
            old_instance = SolicitudInspeccion.objects.get(pk=instance.pk)
            instance._original_estado = old_instance.estado
        except SolicitudInspeccion.DoesNotExist:
            instance._original_estado = None

@receiver(post_save, sender=SolicitudInspeccion)
def notificar_cambio_estado(sender, instance, created, **kwargs):
    if created:
        return

    estado_anterior = getattr(instance, '_original_estado', None)
    nuevo_estado = instance.estado

    if estado_anterior == nuevo_estado or estado_anterior is None:
        return
    
    # Preparar datos para el correo
    context = {'solicitud': instance, 'base_url': 'http://127.0.0.1:8000/usuarios/'}
    asunto = ""
    html_template = None
    text_template = None
    

    if nuevo_estado == EstadoSolicitud.COTIZANDO:
        asunto = f"Cotización disponible para su solicitud N°{instance.pk}"
        html_template = 'email/solicitud_cotizando.html'
        text_template = 'email/solicitud_cotizando_text.txt'
        # Notificación interna
        Notificacion.objects.create(
            usuario=instance.cliente,
            mensaje=f"Tienes una cotización pendiente para la solicitud #{instance.pk}",
            enlace=f"/usuarios/solicitud/aceptar-cotizacion/{instance.pk}/"
        )
    elif nuevo_estado == EstadoSolicitud.APROBADA:
        asunto = f"Solicitud N°{instance.pk} Aprobada y Asignada"
        context['tecnico_nombre'] = instance.inspeccion.tecnico.get_full_name() or instance.inspeccion.tecnico.username
        html_template = 'email/solicitud_aprobada.html'
        text_template = 'email/solicitud_aprobada_text.txt'
    elif nuevo_estado == EstadoSolicitud.RECHAZADA:
        asunto = f"Solicitud N°{instance.pk} Rechazada"
        html_template = 'email/solicitud_rechazada.html'
        text_template = 'email/solicitud_rechazada_text.txt'
    elif nuevo_estado == EstadoSolicitud.COMPLETADA:
        asunto = f"Inspección N°{instance.inspeccion.pk} Finalizada"
        html_template = 'email/inspeccion_completada.html'
        text_template = 'email/inspeccion_completada_text.txt'
    else:
        return

    # Enviar correo
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
            print(f"📧 CORREO ENVIADO A {destinatario} (Estado: {nuevo_estado})")
            
        except Exception as e:
            print(f"ERROR AL ENVIAR CORREO: {e}")


# =========================================================================
# 2. LOGICA DE NOTIFICACIONES INTERNAS (FOTOS DE EVIDENCIA)
# =========================================================================

@receiver(pre_save, sender=TareaInspeccion)
def cache_tarea_foto(sender, instance, **kwargs):
    """Guarda la foto anterior para saber si cambió."""
    if instance.pk:
        try:
            old_instance = TareaInspeccion.objects.get(pk=instance.pk)
            instance._original_imagen = old_instance.imagen_evidencia
        except TareaInspeccion.DoesNotExist:
            instance._original_imagen = None
    else:
        instance._original_imagen = None

@receiver(post_save, sender=TareaInspeccion)
def crear_notificacion_evidencia(sender, instance, created, **kwargs):
    """Crea un Pop-up (Notificacion) cuando se sube una foto nueva."""
    
    # Si no hay imagen, o es la misma de antes, no hacemos nada
    if not instance.imagen_evidencia:
        return
    if instance.imagen_evidencia == getattr(instance, '_original_imagen', None):
        return

    try:
        # Navegamos hacia arriba para encontrar al dueño
        inspeccion = instance.inspeccion
        solicitud = inspeccion.solicitud
        cliente = solicitud.cliente
        
        # Enlace para que el cliente vaya directo a ver la foto
        url_orden = f"/usuarios/solicitud/detalle/{solicitud.pk}/"

        # Creamos la notificación en la Base de Datos
        Notificacion.objects.create(
            usuario=cliente,
            mensaje=f"📸 Nueva evidencia cargada: {instance.descripcion}",
            enlace=url_orden
        )
        
        print(f"🔔 NOTIFICACIÓN CREADA PARA {cliente.username}: Nueva foto subida.")

    except Exception as e:
        print(f"ERROR AL CREAR NOTIFICACIÓN: {e}")