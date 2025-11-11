# usuarios/admin.py (CÓDIGO COMPLETO Y CORREGIDO)

from django.contrib import admin

# Importamos solo los modelos existentes, reemplazando PerfilTecnico con Perfil
from .models import (
    PlantillaInspeccion, 
    TareaPlantilla, 
    Inspeccion, 
    # 🔥 CORRECCIÓN: Reemplazar PerfilTecnico y ProfileBase por el modelo Perfil unificado
    Perfil, 
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
# 3. PERFIL UNIFICADO Y OTROS REGISTROS
# ==========================================================

# 🔥 CORRECCIÓN: Registrar el modelo Perfil unificado en lugar de PerfilTecnico 🔥
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    # Esto facilita la administración de los perfiles
    list_display = ('usuario', 'get_rol_display', 'cambio_contrasena_obligatorio')
    search_fields = ('usuario__username', 'usuario__email', 'descripcion')
    list_filter = ('cambio_contrasena_obligatorio',)
    
    # Campo calculado para mostrar el rol del usuario en la lista
    def get_rol_display(self, obj):
        return obj.get_role()
    get_rol_display.short_description = 'Rol'


# Registros simples de los modelos que no necesitan customización
# 🔥 CORRECCIÓN: Eliminamos el registro de PerfilTecnico, ya está registrado Perfil
admin.site.register(SolicitudInspeccion)
admin.site.register(TareaInspeccion)