# OptifireAPT/urls.py CORREGIDO

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Elimina las importaciones directas de vistas (home, login_view, etc.)
# ya que ahora serán gestionadas por el include de 'usuarios.urls'
# from usuarios.views import (...)

urlpatterns = [
    # ----------------------------------------
    # A. RUTAS DE ADMINISTRACIÓN (Django Admin)
    # ----------------------------------------
    path('admin/', admin.site.urls),
    
    # ----------------------------------------
    # B. RUTAS DE LA APLICACIÓN 'USUARIOS'
    # ----------------------------------------
    # 🔥 INCLUIR TODAS las URLs de la app 'usuarios' en la raíz del proyecto.
    # Esto incluye home, login, logout, password_reset, dashboard, etc.
    # Esto asegura que {% url 'password_reset' %} encuentre la ruta correcta. 🔥
    path('', include('usuarios.urls')), 
    
    # Nota: Eliminamos las rutas duplicadas (login, logout, home, nosotros) que
    # estaban definidas aquí, porque ahora están en usuarios/urls.py.
]

# Configuración para servir archivos MEDIA en desarrollo
if settings.DEBUG:
    # Debes importar settings y static arriba:
    # from django.conf import settings
    # from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)