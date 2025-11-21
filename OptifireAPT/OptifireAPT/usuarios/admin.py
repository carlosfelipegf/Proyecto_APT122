"""Configuración del panel de administración de la app usuarios."""

from django.contrib import admin

from .models import (
    Inspeccion,
    PlantillaInspeccion,
    SolicitudInspeccion,
    TareaInspeccion,
    TareaPlantilla,
)


class PlantillaTareaInline(admin.TabularInline):
    """Permite gestionar las tareas directamente dentro de la plantilla."""

    model = TareaPlantilla
    extra = 1
    fields = ("descripcion", "orden")


@admin.register(PlantillaInspeccion)
class PlantillaInspeccionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha_creacion")
    search_fields = ("nombre",)
    inlines = [PlantillaTareaInline]


@admin.register(Inspeccion)
class InspeccionAdmin(admin.ModelAdmin):
    list_display = ("nombre_inspeccion", "tecnico", "estado", "fecha_creacion")
    list_filter = ("estado", "tecnico")
    search_fields = ("nombre_inspeccion", "tecnico__username")


@admin.register(SolicitudInspeccion)
class SolicitudInspeccionAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "estado", "fecha_solicitud")
    list_filter = ("estado", "fecha_solicitud")
    search_fields = ("cliente__username", "nombre_cliente", "direccion")


@admin.register(TareaInspeccion)
class TareaInspeccionAdmin(admin.ModelAdmin):
    list_display = ("inspeccion", "descripcion", "estado")
    list_filter = ("estado",)
    search_fields = ("inspeccion__nombre_inspeccion", "descripcion")