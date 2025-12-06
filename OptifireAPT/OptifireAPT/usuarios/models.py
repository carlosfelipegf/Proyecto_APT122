from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# ==========================================================
# 1. CONSTANTES Y ENUMERACIONES
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
# 2. PERFIL DE USUARIO (UNIFICADO)
# ==========================================================

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')

    # --- CAMPOS COMUNES ---
    foto = models.ImageField(upload_to='perfiles/fotos/', blank=True, null=True, verbose_name="Foto de Perfil")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(max_length=500, blank=True, null=True, verbose_name="Descripción / Bio")
    rut = models.CharField(max_length=12, blank=True, null=True, unique=True, verbose_name="RUT")

    # Ubicación
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Región")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")

    # --- CAMPOS CLIENTE ---
    rut_empresa = models.CharField(max_length=20, blank=True, null=True)
    rubro = models.CharField(max_length=100, blank=True, null=True)

    # --- CAMPOS TÉCNICO ---
    fecha_contratacion = models.DateField(blank=True, null=True, verbose_name="Fecha de Contratación")

    # --- CAMPOS ADMINISTRADOR (del primer código) ---
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo Administrativo")
    edad = models.PositiveIntegerField(blank=True, null=True, verbose_name="Edad")

    # Control de primer inicio
    obligar_cambio_contrasena = models.BooleanField(default=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    def get_role(self):
        if self.usuario.is_superuser:
            return Roles.ADMINISTRADOR
        if self.usuario.groups.filter(name=Roles.ADMINISTRADOR).exists():
            return Roles.ADMINISTRADOR
        if self.usuario.groups.filter(name=Roles.TECNICO).exists():
            return Roles.TECNICO
        if self.usuario.groups.filter(name=Roles.CLIENTE).exists():
            return Roles.CLIENTE
        return 'Sin Rol'


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)
    else:
        Perfil.objects.get_or_create(usuario=instance)


# ==========================================================
# 3. PLANTILLAS
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

    # Datos de contacto
    nombre_cliente = models.CharField(max_length=100)
    apellido_cliente = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)

    # Datos técnicos
    maquinaria = models.TextField(verbose_name="Maquinaria / Servicio")
    observaciones_cliente = models.TextField(blank=True, null=True)

    # Datos administrativos
    monto_cotizacion = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    detalle_cotizacion = models.TextField(blank=True, null=True)

    # Preasignación
    tecnico_preasignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_preasignadas',
        limit_choices_to={'groups__name': Roles.TECNICO}
    )
    plantilla_preasignada = models.ForeignKey(
        PlantillaInspeccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_preasignadas'
    )
    nombre_inspeccion_preasignado = models.CharField(max_length=200, blank=True, null=True)
    fecha_programada_preasignada = models.DateField(null=True, blank=True)

    fecha_programada = models.DateField(null=True, blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(max_length=20, choices=EstadoSolicitud.choices, default=EstadoSolicitud.PENDIENTE)
    motivo_rechazo = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Solicitud #{self.id} - {self.get_estado_display()}"


# ==========================================================
# 5. INSPECCIÓN
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
        choices=EstadoInspeccion.choices,
        default=EstadoInspeccion.ASIGNADA
    )

    class Meta:
        indexes = [models.Index(fields=['tecnico', 'estado'])]

    def __str__(self):
        return f"OT #{self.id} - {self.nombre_inspeccion}"


class TareaInspeccion(models.Model):
    inspeccion = models.ForeignKey(Inspeccion, on_delete=models.CASCADE, related_name='tareas')
    plantilla_tarea = models.ForeignKey(TareaPlantilla, on_delete=models.SET_NULL, null=True, blank=True)

    # Descripción de la tarea
    descripcion = models.CharField(max_length=255, verbose_name="Punto de Control")
    observacion = models.TextField(blank=True, null=True)

    # Evidencia
    imagen_evidencia = models.ImageField(
        upload_to='inspecciones/evidencias/',
        blank=True,
        null=True,
        verbose_name="Imagen de Evidencia"
    )

    estado = models.CharField(
        max_length=50,
        choices=EstadoTarea.choices,
        default=EstadoTarea.PENDIENTE,
        verbose_name="Estado de la Tarea"
    )

    def __str__(self):
        return f"{self.descripcion} ({self.get_estado_display()})"


# ==========================================================
# 6. NOTIFICACIONES
# ==========================================================

class Notificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.CharField(max_length=255)
    enlace = models.CharField(max_length=255, blank=True, null=True)
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje}"
