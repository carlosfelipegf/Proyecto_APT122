from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime

User = get_user_model()

# -------------------------------------------------------------------
# CONSTANTES DE ROL
# -------------------------------------------------------------------
ROL_ADMINISTRADOR = 'Administrador'
ROL_TECNICO = 'Técnico'
ROL_CLIENTE = 'Cliente'

# -------------------------------------------------------------------
# MODELO PERFIL UNIFICADO (SIN CAMBIOS)
# -------------------------------------------------------------------
class Perfil(models.Model):
    """
    Modelo de perfil unificado para todos los usuarios.
    """
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    cambio_contrasena_obligatorio = models.BooleanField(
        default=True,
        verbose_name="Cambio de Contraseña Obligatorio"
    )
    foto = models.ImageField(
        upload_to='perfiles/fotos/', 
        blank=True, 
        null=True, 
        verbose_name="Foto de Perfil"
    )
    descripcion = models.TextField(
        max_length=500, 
        blank=True, 
        null=True, 
        verbose_name="Descripción Personal/Profesional"
    )
    # Otros campos...
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    def get_role(self):
        """Retorna el rol principal del usuario."""
        if self.usuario.is_superuser:
            return ROL_ADMINISTRADOR
        if self.usuario.groups.filter(name=ROL_ADMINISTRADOR).exists():
            return ROL_ADMINISTRADOR
        if self.usuario.groups.filter(name=ROL_TECNICO).exists():
            return ROL_TECNICO
        if self.usuario.groups.filter(name=ROL_CLIENTE).exists():
            return ROL_CLIENTE
        return 'Sin Rol'
    
    @property
    def total_ordenes_solicitadas(self):
        return self.usuario.solicitudes_enviadas.count()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)
    try:
        instance.perfil.save()
    except Perfil.DoesNotExist:
        Perfil.objects.create(usuario=instance)


# ==========================================================
# 2. MODELOS DE PLANTILLA (SIN CAMBIOS)
# ==========================================================

class PlantillaInspeccion(models.Model):
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre de la Plantilla")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción General")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class TareaPlantilla(models.Model): 
    plantilla = models.ForeignKey(
        PlantillaInspeccion, 
        related_name='tareas_base', 
        on_delete=models.CASCADE, 
        verbose_name="Plantilla Maestra"
    )
    descripcion = models.CharField(max_length=255, verbose_name="Descripción de la Tarea")
    orden = models.IntegerField(default=1, verbose_name="Orden de Aparición")

    class Meta:
        ordering = ['orden']
        verbose_name = "Tarea de Plantilla"
        verbose_name_plural = "Tareas de Plantilla"

    def __str__(self):
        return f"{self.plantilla.nombre}: {self.descripcion}"


# ==========================================================
# 3. MODELO DE SOLICITUD (CORRECCIÓN DE CONSTANTES DE ESTADO)
# ==========================================================

# 🔥 CORRECCIÓN CRUCIAL: Renombrar 'PENDIENTE_ADMIN' a 'PENDIENTE' para coincidir con las vistas
# Y 'APROBADA_CLIENTE' a 'APROBADA' para simplificar la creación de la Inspección
ESTADOS_SOLICITUD = [
    # Paso 1: Cliente solicita
    ('PENDIENTE', 'Pendiente de Revisión (Admin)'), 
    # Paso 2: Admin envía cotización (esperando el cliente)
    ('COTIZANDO', 'Pendiente de Aprobación (Cliente)'), 
    # Paso 3: Cliente aprueba. Se crea la Inspección y pasa a ser ASIGNADA para el técnico
    ('APROBADA', 'Aprobada por Cliente (Orden de Trabajo Creada)'), 
    # Paso 4: Técnico termina el trabajo
    ('COMPLETADA', 'Inspección Finalizada'),
    # Estados de cierre
    ('RECHAZADA', 'Rechazada por Admin/Cliente'),
    ('ANULADA', 'Anulada por Cliente'),
]

class SolicitudInspeccion(models.Model):
    cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='solicitudes_enviadas',
        verbose_name="Cliente Solicitante"
    )
    
    nombre_cliente = models.CharField(max_length=100, verbose_name="Nombre de Contacto")
    apellido_cliente = models.CharField(max_length=100, verbose_name="Apellido de Contacto", blank=True, null=True) 
    direccion = models.CharField(max_length=255, verbose_name="Dirección de la Inspección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono de Contacto")
    maquinaria = models.TextField(verbose_name="Maquinaria / Servicio Requerido") 
    observaciones_cliente = models.TextField(blank=True, null=True, verbose_name="Observaciones o Requerimientos Adicionales")

    monto_cotizacion = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        null=True, 
        blank=True, 
        verbose_name="Monto Cotizado (CLP)"
    )
    
    detalle_cotizacion = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Detalle de la Cotización / Observaciones del Admin"
    )
    
    tecnico_asignado = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'groups__name': ROL_TECNICO}, # Sugerencia para Admin
        related_name='ordenes_asignadas',
        verbose_name="Técnico Pre-Asignado"
    )
    
    fecha_programada = models.DateField(verbose_name="Fecha Programada (Sugerida)", null=True, blank=True)
    
    estado = models.CharField(
        max_length=25,
        choices=ESTADOS_SOLICITUD, 
        default='PENDIENTE', # Ajustado el default
        verbose_name="Estado de la Solicitud"
    )
    motivo_rechazo = models.TextField(blank=True, null=True, verbose_name="Motivo del Rechazo")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Solicitud #{self.id} de {self.nombre_cliente} ({self.get_estado_display()})"


# ==========================================================
# 4. MODELOS DE INSPECCIÓN (SIN CAMBIOS)
# ==========================================================

ESTADOS_INSPECCION = [
    ('ASIGNADA', 'Asignada a Técnico'),
    ('EN_CURSO', 'En Curso (Borrador Guardado)'),
    ('COMPLETADA', 'Inspección Terminada'),
]

class Inspeccion(models.Model):
    """Modelo para la instancia de inspección asignada a un técnico (Orden de Trabajo)."""
    
    solicitud = models.OneToOneField(
        SolicitudInspeccion,
        on_delete=models.CASCADE,
        related_name='inspeccion_creada',
        verbose_name="Solicitud de Origen",
        null=True, 
        blank=True 
    )
    
    tecnico = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='inspecciones_asignadas',
        verbose_name="Técnico Asignado"
    )
    
    plantilla_base = models.ForeignKey(
        PlantillaInspeccion, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Plantilla de Origen"
    )
    
    nombre_inspeccion = models.CharField(max_length=200, verbose_name="Título de la Inspección")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_programada = models.DateField(verbose_name="Fecha Programada", null=True, blank=True)
    
    comentarios_generales = models.TextField(blank=True, null=True, verbose_name="Comentarios Finales")
    
    estado = models.CharField(
        max_length=50, 
        default='ASIGNADA',
        choices=ESTADOS_INSPECCION,
        verbose_name="Estado de la Inspección"
    )
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Inspección {self.id} - {self.nombre_inspeccion} ({self.tecnico.username})"

CHOICES_ESTADO_TAREA = [
    ('B', 'Bueno (Cumple)'),
    ('M', 'Malo (No Cumple)'),
    ('N/A', 'No Aplica'),
    ('PENDIENTE', 'Pendiente'),
]

class TareaInspeccion(models.Model):
    """Modelo para cada tarea/punto de control dentro de una Inspeccion."""
    
    inspeccion = models.ForeignKey(
        Inspeccion, 
        on_delete=models.CASCADE, 
        related_name='tareas',
        verbose_name="Inspección Perteneciente"
    )
    
    plantilla_tarea = models.ForeignKey(TareaPlantilla, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tarea Base")

    descripcion = models.CharField(max_length=255, verbose_name="Punto de Control")
    
    estado = models.CharField(
        max_length=10, 
        choices=CHOICES_ESTADO_TAREA, 
        default='PENDIENTE',
        verbose_name="Resultado del Punto"
    )
    observacion = models.TextField(blank=True, null=True, verbose_name="Observación del Técnico")

    def __str__(self):
        return f"{self.descripcion} ({self.get_estado_display()})"