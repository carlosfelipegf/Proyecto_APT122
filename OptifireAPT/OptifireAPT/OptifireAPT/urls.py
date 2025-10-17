from django.contrib import admin
from django.urls import path, include
from usuarios.views import home # Importa la vista home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    # Las URLs de la app 'usuarios' se manejarán bajo la ruta 'usuarios/'
    path('usuarios/', include('usuarios.urls')),
    
    # Si quieres que login/logout/dashboard estén en la raíz, puedes hacerlo así,
    # pero es mejor mantenerlos dentro del 'usuarios.urls'
]