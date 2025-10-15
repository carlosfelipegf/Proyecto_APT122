# usuarios/admin.py

from django.contrib import admin
from .models import PlantillaInspeccion, PlantillaTarea, Inspeccion

# Inline para permitir editar las tareas dentro de la plantilla
class PlantillaTareaInline(admin.TabularInline):
    model = PlantillaTarea
    extra = 3  # Permite añadir 3 tareas vacías por defecto
    fields = ('descripcion', 'orden')

@admin.register(PlantillaInspeccion)
class PlantillaInspeccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    inlines = [PlantillaTareaInline]
    search_fields = ('nombre',)

@admin.register(Inspeccion)
class InspeccionAdmin(admin.ModelAdmin):
    list_display = ('nombre_inspeccion', 'tecnico', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tecnico')
    search_fields = ('nombre_inspeccion', 'tecnico__username')