# usuarios/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Mapea la ruta raíz de la app (/usuarios/) a la nueva vista del dashboard
    path('', views.dashboard_inspector, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/nueva_inspeccion/', views.nueva_inspeccion, name='nueva_inspeccion'),
    # Asegúrese de que esta app NO tenga sus propias URLs de login
]