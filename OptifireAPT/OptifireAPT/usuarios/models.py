from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

# Importar post_save y receiver para crear/guardar el perfil automáticamente
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg, Count # Importar para cálculos

# Obtenemos el modelo User estándar (auth.User)
User = get_user_model()

# -------------------------------------------------------------------
# CONSTANTES DE ROL
# -------------------------------------------------------------------
ROL_ADMINISTRADOR = 'Administrador'
ROL_TECNICO = 'Técnico'
ROL_CLIENTE = 'Cliente'

# -------------------------------------------------------------------
# 🔥 MODELO PERFIL UNIFICADO (Reemplaza ProfileBase y PerfilTecnico) 🔥
# -------------------------------------------------------------------
class Perfil(models.Model):
    """
    Modelo de perfil unificado para todos los usuarios (Admin, Técnico, Cliente).
    Contiene la bandera de primer logeo, foto, descripción, y campos de estadísticas.
    """
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil' # Cambiado a 'perfil' para fácil acceso: user.perfil
    )
    
    # Campo de seguridad (de la anterior ProfileBase)
    cambio_contrasena_obligatorio = models.BooleanField(
        default=True,
        verbose_name="Cambio de Contraseña Obligatorio"
    )
    
    # Campos Comunes (de la anterior PerfilTecnico)
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

    # Campos Específicos (para uso futuro, aunque la lógica es por código)
    # Ejemplo: calificacion_tecnico, calificacion_cliente, etc.
    # Por ahora, los dejaremos simples ya que se calcularán en la vista si es necesario.
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    # ---------------------------------------------
    # Propiedad para obtener el rol del usuario de forma fácil
    # ---------------------------------------------
    def get_role(self):
        """Retorna el rol principal del usuario."""
        if self.usuario.groups.filter(name=ROL_ADMINISTRADOR).exists():
            return ROL_ADMINISTRADOR
        if self.usuario.groups.filter(name=ROL_TECNICO).exists():
            return ROL_TECNICO
        if self.usuario.groups.filter(name=ROL_CLIENTE).exists():
            return ROL_CLIENTE
        return 'Sin Rol'
    
    # ---------------------------------------------
    # Propiedad para obtener estadísticas del cliente (Calculadas)
    # ---------------------------------------------
    @property
    def total_ordenes_solicitadas(self):
        """Retorna el número de solicitudes (órdenes) creadas por este usuario cliente."""
        return self.usuario.solicitudes_enviadas.count()
    
    # Propiedad de ejemplo si tuvieras un modelo de calificación del cliente
    @property
    def calificacion_como_cliente(self):
        """Retorna la calificación promedio recibida por el cliente (Requiere modelo de Calificación)."""
        # SUPLIDO: Retorna un valor fijo o nulo si no tienes un modelo de calificación de cliente
        return 4.5 # Valor de ejemplo. Cámbialo por tu lógica real.

# -------------------------------------------------------------------
# SIGNAL: Crear y Guardar Perfil automáticamente al crear un Usuario
# -------------------------------------------------------------------
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Crea un Perfil al crear el usuario o lo guarda si ya existe."""
    if created:
        Perfil.objects.create(usuario=instance)
    # Asegura que el perfil se guarde cuando se guarda el usuario (útil para la bandera)
    try:
        instance.perfil.save()
    except Perfil.DoesNotExist:
        Perfil.objects.create(usuario=instance)


# ==========================================================
# 2. MODELOS DE PLANTILLA (SIN CAMBIOS)
# ==========================================================

class PlantillaInspeccion(models.Model):
    """Modelo para las plantillas maestras de inspección."""
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre de la Plantilla")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción General")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class TareaPlantilla(models.Model): 
    """Tareas predefinidas que componen una PlantillaInspeccion."""
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
# 3. MODELO DE SOLICITUD (CON CAMBIOS)
# ==========================================================

ESTADOS_SOLICITUD = [
    ('PENDIENTE', 'Pendiente de Aprobación'),
    ('APROBADA', 'Aprobada (Inspección Creada)'),
    ('RECHAZADA', 'Rechazada'),
    ('COMPLETADA', 'Inspección Finalizada'),
    # 🔥 NUEVOS ESTADOS 🔥
    ('ANULACION_SOLICITADA', 'Anulación Solicitada'),
    ('ANULADA', 'Anulada'),
]

class SolicitudInspeccion(models.Model):
    # Campo vital para la lógica de roles y vistas
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

    estado = models.CharField(
        max_length=25, # Aumentado el max_length para el nuevo estado
        choices=ESTADOS_SOLICITUD, 
        default='PENDIENTE',
        verbose_name="Estado de la Solicitud"
    )
    motivo_rechazo = models.TextField(blank=True, null=True, verbose_name="Motivo del Rechazo (Admin)")
    # 🔥 Nuevo campo para el motivo de anulación del cliente 🔥
    motivo_anulacion = models.TextField(blank=True, null=True, verbose_name="Motivo de Solicitud de Anulación (Cliente)")

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
    """Modelo para la instancia de inspección asignada a un técnico."""
    
    solicitud = models.OneToOneField(
        SolicitudInspeccion,
        on_delete=models.CASCADE,
        related_name='inspeccion_creada',
        verbose_name="Solicitud de Origen",
        null=True, 
        blank=True 
    )
    
    tecnico = models.ForeignKey(
        User, # Referencia al auth.User
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

# Opciones de estado para cada tarea individual
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