"""
URL configuration for OptifireAPT project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# OptifireAPT/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Importamos las vistas de autenticación

urlpatterns = [
    # ADMIN SITE: Acceso exclusivo para Superusuario/Staff
    path('admin/', admin.site.urls),

    # AUTENTICACIÓN: Rutas estándar de Django (login/logout)
    path('auth/login/', auth_views.LoginView.as_view(), name='login'), # Nombre clave para LOGIN_URL
    path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Note: Usamos LoginView.as_view() en lugar de include('django.contrib.auth.urls') para simplificar el mapeo del nombre.

    # RUTA DE LA APLICACIÓN: Acceso para usuarios normales
    path('usuarios/', include('usuarios.urls')),
]