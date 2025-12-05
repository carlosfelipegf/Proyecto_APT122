from django.contrib import admin
from django.urls import path, include
from django.conf import settings             # Configuración del proyecto
from django.conf.urls.static import static   # Función para servir archivos estáticos/media

# Importaciones de Vistas
from usuarios.views import (
    home, 
    login_view, 
    logout_view, 
    nosotros_view, 
    dashboard  # <--- Ya lo estabas importando, ¡bien!
)

# Definición de urlpatterns
urlpatterns = [
    # ----------------------------------------
    # A. RUTAS PÚBLICAS Y DE AUTENTICACIÓN (RAÍZ)
    # ----------------------------------------
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('nosotros/', nosotros_view, name='nosotros'), 
    
    # --- ESTA LÍNEA FALTABA ---
    # Es necesaria para que el login sepa a dónde redirigir inicialmente
    path('dashboard/', dashboard, name='dashboard'), 
    
    # ----------------------------------------
    # B. ADMIN DJANGO
    # ----------------------------------------
    path('admin/', admin.site.urls),
    
    # ----------------------------------------
    # C. RUTAS INTERNAS DE LA APLICACIÓN (BAJO /usuarios/)
    # ----------------------------------------
    path('usuarios/', include('usuarios.urls')), 
]

# ----------------------------------------
# D. CONFIGURACIÓN PARA MOSTRAR IMÁGENES (MEDIA)
# ----------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)