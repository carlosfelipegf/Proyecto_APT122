from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# ==========================================================
# 1. CONSTANTES Y ENUMERACIONES (La Fuente de la Verdad)
# ==========================================================

class Roles(models.TextChoices):
    ADMINISTRADOR = 'Administrador', _('Administrador')
    TECNICO = 'Técnico', _('Técnico')
    CLIENTE = 'Cliente', _('Cliente')

class EstadoSolicitud(models.TextChoices):
    PENDIENTE = 'PENDIENTE', _('Pendiente de Revisión (Admin)')
    COTIZANDO = 'COTIZANDO', _('Pendiente de Aprobación (Cliente)')
    APROBADA = 'APROBADA', _('Aprobada (Orden Creada)')
    COMPLETADA = 'COMPLETADA', _('Finalizada')
    RECHAZADA = 'RECHAZADA', _('Rechazada')
    ANULADA = 'ANULADA', _('Anulada por Cliente')

class EstadoInspeccion(models.TextChoices):
    ASIGNADA = 'ASIGNADA', _('Asignada a Técnico')
    EN_CURSO = 'EN_CURSO', _('En Curso')
    COMPLETADA = 'COMPLETADA', _('Terminada')

class EstadoTarea(models.TextChoices):
    BUENO = 'B', _('Bueno (Cumple)')
    MALO = 'M', _('Malo (No Cumple)')
    NO_APLICA = 'N/A', _('No Aplica')
    PENDIENTE = 'PENDIENTE', _('Pendiente')

# ==========================================================
# 2. PERFIL DE USUARIO
# ==========================================================

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='perfiles/fotos/', blank=True, null=True)
    descripcion = models.TextField(max_length=500, blank=True, null=True)
    
    # 🔑 CAMPO NUEVO CLAVE: True si el usuario ya ha cambiado su contraseña inicial 🔑
    password_changed = models.BooleanField(default=False) 

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    def get_role(self):
        # NOTA: Esta lógica se usa para determinar el rol en las vistas de notificaciones.
        if self.usuario.is_superuser: return Roles.ADMINISTRADOR
        if self.usuario.groups.filter(name=Roles.ADMINISTRADOR).exists(): return Roles.ADMINISTRADOR
        if self.usuario.groups.filter(name=Roles.TECNICO).exists(): return Roles.TECNICO
        if self.usuario.groups.filter(name=Roles.CLIENTE).exists(): return Roles.CLIENTE
        return 'Sin Rol'

# --- Señal para asegurar la creación del Perfil y el flag inicial ---

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Crea el perfil. El flag password_changed será False por defecto.
        Perfil.objects.create(usuario=instance)
    else:
        # Asegura que el perfil exista para usuarios pre-existentes o actualizaciones
        try:
            instance.perfil.save()
        except Perfil.DoesNotExist:
            Perfil.objects.create(usuario=instance)

# ==========================================================
# 3. PLANTILLAS (Configuración)
# ==========================================================

class PlantillaInspeccion(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class TareaPlantilla(models.Model): 
    plantilla = models.ForeignKey(PlantillaInspeccion, related_name='tareas_base', on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255)
    orden = models.IntegerField(default=1)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.plantilla.nombre}: {self.descripcion}"

# ==========================================================
# 4. SOLICITUD DE INSPECCIÓN
# ==========================================================

class SolicitudInspeccion(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    
    # Datos de Contacto
    nombre_cliente = models.CharField(max_length=100)
    apellido_cliente = models.CharField(max_length=100, blank=True, null=True) 
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    
    # Datos Técnicos
    maquinaria = models.TextField(verbose_name="Maquinaria / Servicio") 
    observaciones_cliente = models.TextField(blank=True, null=True)

    # Datos Administrativos
    monto_cotizacion = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    detalle_cotizacion = models.TextField(blank=True, null=True)
    
    fecha_programada = models.DateField(null=True, blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    estado = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices, 
        default=EstadoSolicitud.PENDIENTE
    )
    motivo_rechazo = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Solicitud #{self.id} - {self.get_estado_display()}"

# ==========================================================
# 5. INSPECCIÓN (Orden de Trabajo)
# ==========================================================

class Inspeccion(models.Model):
    solicitud = models.OneToOneField(
        SolicitudInspeccion,
        on_delete=models.CASCADE,
        related_name='inspeccion',
        null=True, blank=True
    )
    
    tecnico = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='inspecciones_asignadas',
        limit_choices_to={'groups__name': Roles.TECNICO} 
    )
    
    plantilla_base = models.ForeignKey(PlantillaInspeccion, on_delete=models.SET_NULL, null=True, blank=True)
    
    nombre_inspeccion = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_programada = models.DateField(null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    
    comentarios_generales = models.TextField(blank=True, null=True)
    
    estado = models.CharField(
        max_length=20, 
        default=EstadoInspeccion.ASIGNADA,
        choices=EstadoInspeccion.choices
    )

    class Meta:
        indexes = [
            models.Index(fields=['tecnico', 'estado']),
        ]

    def __str__(self):
        return f"OT #{self.id} - {self.nombre_inspeccion}"

class TareaInspeccion(models.Model):
    inspeccion = models.ForeignKey(Inspeccion, on_delete=models.CASCADE, related_name='tareas')
    plantilla_tarea = models.ForeignKey(TareaPlantilla, on_delete=models.SET_NULL, null=True, blank=True)
    
    descripcion = models.CharField(max_length=255)
    observacion = models.TextField(blank=True, null=True)
    
    estado = models.CharField(
        max_length=10, 
        choices=EstadoTarea.choices, 
        default=EstadoTarea.PENDIENTE
    )

    def __str__(self):
        return f"{self.descripcion} ({self.get_estado_display()})"
        
# ==========================================================
# 6. MODELO DE NOTIFICACIONES (¡NUEVO!)
# ==========================================================

class Notification(models.Model):
    """
    Modelo para almacenar notificaciones destinadas a usuarios específicos.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Usuario Destino")
    
    message = models.TextField(verbose_name="Mensaje de Notificación")
    is_read = models.BooleanField(default=False, verbose_name="Leída")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    # Campo para un enlace de acción (e.g., /dashboard/solicitud/5/)
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name="Enlace de Acción")
    
    # Campo para identificar el objeto origen (ej: Solicitud, Inspeccion). Útil para borrar y filtrar.
    # Puede ser 'SOLICITUD', 'INSPECCION', 'SISTEMA', etc.
    type = models.CharField(max_length=50, default='SISTEMA')

    # Llave genérica opcional para vincular a cualquier modelo (ej: Inspeccion.id)
    object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        # Agregamos un índice para acelerar la consulta de notificaciones no leídas de un usuario
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]


    def __str__(self):
        return f"Notificación para {self.user.username}: {self.message[:40]}..."