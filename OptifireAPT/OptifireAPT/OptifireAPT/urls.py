# urls.py ARREGLADO

from django.contrib import admin
from django.urls import path, include

# 1. Importaciones de Vistas
# Es mejor importar solo las vistas necesarias.
# Agrupa todas las vistas públicas y de autenticación que irán en la raíz.
from usuarios.views import (
    home, 
    login_view, 
    logout_view, 
    nosotros_view, 
    dashboard 
)


# 2. Definición de urlpatterns (SOLO UNA VEZ)
urlpatterns = [
    # ----------------------------------------
    # A. RUTAS PÚBLICAS Y DE AUTENTICACIÓN (RAÍZ)
    # ----------------------------------------
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('nosotros/', nosotros_view, name='nosotros'), 
    
    # ----------------------------------------
    # B. ADMIN DJANGO
    # ----------------------------------------
    path('admin/', admin.site.urls),
    
    # ----------------------------------------
    # C. RUTAS INTERNAS DE LA APLICACIÓN (BAJO /usuarios/)
    # ----------------------------------------
    # Esto manejará todas las URLs privadas y de gestión, como /usuarios/dashboard/, 
    # /usuarios/nueva_inspeccion/, etc.
    path('usuarios/', include('usuarios.urls')), 
    
] # <--- ¡Este corchete de cierre es crucial!