from django.db import models
# Importante: Usar get_user_model() para referenciar al modelo de usuario, 
# aunque en tu caso usas 'User' directamente (lo mantendremos).
from django.contrib.auth.models import User
from django.utils import timezone

# ==========================================================
# 0. MODELO PERFIL (Para técnico - Requerido en tu flujo)
# ==========================================================

class PerfilTecnico(models.Model):
    """Modelo para la información adicional del técnico (foto, descripción)."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_tecnico')
    foto = models.ImageField(upload_to='perfiles/fotos/', blank=True, null=True, verbose_name="Foto de Perfil")
    descripcion_profesional = models.TextField(blank=True, null=True, verbose_name="Descripción Profesional")

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


# ==========================================================
# 1. MODELOS DE PLANTILLA (Creados y gestionados por el Administrador)
# ==========================================================

class PlantillaInspeccion(models.Model):
    """Modelo para las plantillas maestras de inspección."""
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre de la Plantilla")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción General")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class PlantillaTarea(models.Model):
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
# 2. MODELO DE SOLICITUD (Iniciado por el Cliente, gestionado por Admin)
# ==========================================================

ESTADOS_SOLICITUD = [
    ('PENDIENTE', 'Pendiente de Aprobación'),
    ('APROBADA', 'Aprobada (Inspección Creada)'),
    ('RECHAZADA', 'Rechazada'),
    ('COMPLETADA', 'Inspección Finalizada'), # Estado final para el cliente
]

class SolicitudInspeccion(models.Model):
    """Modelo para la solicitud inicial de inspección hecha por un Cliente."""
    
    cliente = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='solicitudes_cliente',
        verbose_name="Cliente Solicitante"
    )
    
    # Datos de la Solicitud
    nombre_cliente = models.CharField(max_length=100, verbose_name="Nombre de Contacto")
    direccion = models.CharField(max_length=255, verbose_name="Dirección de la Inspección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono de Contacto")
    maquinaria = models.TextField(verbose_name="Maquinaria / Servicio Requerido")
    
    # Gestión del Administrador
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_SOLICITUD, 
        default='PENDIENTE',
        verbose_name="Estado de la Solicitud"
    )
    motivo_rechazo = models.TextField(blank=True, null=True, verbose_name="Motivo del Rechazo (Admin)")

    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Solicitud #{self.id} de {self.nombre_cliente} ({self.get_estado_display()})"


# ==========================================================
# 3. MODELOS DE INSPECCIÓN (Generados por Admin, Completados por Técnico)
# ==========================================================

ESTADOS_INSPECCION = [
    ('ASIGNADA', 'Asignada a Técnico'), # El estado inicial una vez aprobada la solicitud
    ('EN_PROGRESO', 'En Progreso (Borrador Guardado)'), 
    ('TERMINADA', 'Inspección Terminada'), # Nuevo estado final de la inspección
]

class Inspeccion(models.Model):
    """Modelo para la instancia de inspección asignada a un técnico."""
    
    # Enlace a la solicitud que generó esta inspección (OneToOne para que 1 solicitud solo genere 1 inspección)
    solicitud = models.OneToOneField(
        SolicitudInspeccion,
        on_delete=models.CASCADE,
        related_name='inspeccion_creada',
        verbose_name="Solicitud de Origen",
        null=True, # <--- AÑADIR ESTO
        blank=True # <--- AÑADIR ESTO
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
    comentarios_generales = models.TextField(blank=True, null=True, verbose_name="Comentarios Finales")
    
    estado = models.CharField(
        max_length=50, 
        default='ASIGNADA', # El estado inicial es ASIGNADA, no PENDIENTE
        choices=ESTADOS_INSPECCION,
        verbose_name="Estado de la Inspección"
    )
    fecha_termino = models.DateTimeField(null=True, blank=True)

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
    
    # El campo 'plantilla_tarea' nos permite saber de qué tarea base proviene, si es necesario
    plantilla_tarea = models.ForeignKey(PlantillaTarea, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tarea Base")

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