# OptifireAPT/OptifireAPT/urls.py (Versión Corregida)

from django.contrib import admin
from django.urls import path, include
# ASEGÚRATE DE NO IMPORTAR 'from usuarios import views' AQUÍ

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ✅ ESTA LÍNEA ES CLAVE y engloba todas las URLs de usuarios (incluyendo el dashboard)
    path('', include('usuarios.urls')), 
    
    # 🚫 Todas las rutas específicas (como 'nueva_inspeccion') deben estar en usuarios/urls.py
]