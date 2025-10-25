from django.contrib import admin
from django.urls import path, include


# ASEGÚRATE DE NO IMPORTAR 'from usuarios import views' AQUÍ
from usuarios.views import home # Importa la vista home


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    # Las URLs de la app 'usuarios' se manejarán bajo la ruta 'usuarios/'
    path('usuarios/', include('usuarios.urls')),
    

    # ✅ ESTA LÍNEA ES CLAVE y engloba todas las URLs de usuarios (incluyendo el dashboard)
    path('', include('usuarios.urls')), 
    
    # 🚫 Todas las rutas específicas (como 'nueva_inspeccion') deben estar en usuarios/urls.py

# Importamos las vistas públicas directamente desde la app 'usuarios'
# Esto permite que login/, logout/ y nosotros/ funcionen en la raíz del sitio.
from usuarios.views import (
    home, 
    login_view, 
    logout_view, 
    nosotros_view, 
    dashboard # También importamos dashboard para que /usuarios/ te redirija
)

urlpatterns = [
    # ----------------------------------------
    # 1. RUTAS PÚBLICAS Y DE AUTENTICACIÓN (RAÍZ)
    # ----------------------------------------
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('nosotros/', nosotros_view, name='nosotros'), # ¡SOLUCIÓN AL 404!

    # ----------------------------------------
    # 2. ADMIN DJANGO
    # ----------------------------------------
    path('admin/', admin.site.urls),
    
    # ----------------------------------------
    # 3. RUTAS INTERNAS DE LA APLICACIÓN (BAJO /usuarios/)
    # ----------------------------------------
    # Estas URLs incluyen los dashboards y las vistas de gestión
    path('usuarios/', include('usuarios.urls')), 
    
    # Nota: El path('usuarios/', views.dashboard, name='dashboard') se mueve a usuarios/urls.py
    # Si quieres que login/logout/dashboard estén en la raíz, puedes hacerlo así,
    # pero es mejor mantenerlos dentro del 'usuarios.urls'

]