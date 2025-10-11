from django.db import models
from django.contrib.auth.models import User

# Modelo para la inspección principal
class Inspeccion(models.Model):
    # La inspección está ligada al usuario que la crea
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_inspeccion = models.CharField(max_length=200, verbose_name="Nombre de la Inspección")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    comentarios_generales = models.TextField(blank=True, null=True)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"Inspección {self.id} por {self.usuario.username}"

# Modelo para cada tarea/punto de control dentro de la inspección
class TareaInspeccion(models.Model):
    CHOICES_ESTADO = [
        ('B', 'Bueno'),
        ('M', 'Malo'),
        ('N/A', 'No Aplica'),
    ]

    inspeccion = models.ForeignKey(Inspeccion, on_delete=models.CASCADE, related_name='tareas')
    descripcion = models.CharField(max_length=255, verbose_name="Punto de Control")
    estado = models.CharField(max_length=3, choices=CHOICES_ESTADO)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.descripcion} ({self.estado})"