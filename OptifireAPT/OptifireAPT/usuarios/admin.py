# usuarios/admin.py (CÓDIGO COMPLETO Y CORREGIDO)

from django.contrib import admin

# Importamos explícitamente todos los modelos que existen en usuarios/models.py
# El error está aquí, debe asegurar que todos los modelos se importan
from .models import (
    PlantillaInspeccion, 
    TareaPlantilla, 
    Inspeccion, 
    PerfilTecnico, 
    SolicitudInspeccion, 
    TareaInspeccion
)

# ==========================================================
# 1. PLANTILLA Y TAREAS (Ya existía)
# ==========================================================

# Inline para permitir editar las tareas dentro de la plantilla
class PlantillaTareaInline(admin.TabularInline):
    model = TareaPlantilla
    extra = 3  # Permite añadir 3 tareas vacías por defecto
    fields = ('descripcion', 'orden')

@admin.register(PlantillaInspeccion)
class PlantillaInspeccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    inlines = [PlantillaTareaInline]
    search_fields = ('nombre',)

# ==========================================================
# 2. INSPECCIÓN (Ya existía)
# ==========================================================

@admin.register(Inspeccion)
class InspeccionAdmin(admin.ModelAdmin):
    list_display = ('nombre_inspeccion', 'tecnico', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tecnico')
    search_fields = ('nombre_inspeccion', 'tecnico__username')

# ==========================================================
# 3. REGISTROS FALTANTES (Añadidos para estabilidad)
# ==========================================================

# Registros simples de los modelos que no necesitan customización
admin.site.register(PerfilTecnico)
admin.site.register(SolicitudInspeccion)

# Si TareaInspeccion y TareaPlantilla no se manejan en inlines, deben registrarse
# TareaPlantilla se maneja en PlantillaInspeccionAdmin, así que no se registra aquí
admin.site.register(TareaInspeccion)