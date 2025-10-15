from django.urls import path
from . import views

urlpatterns = [
    # --- 1. Rutas Públicas/Autenticación ---
    
    # Ruta principal (Landing page)
    path('', views.home, name='home'), 
    path('login/', views.login_view, name='login'), # Esta ruta debe estar en el proyecto principal (OptifireAPT/urls.py)
    path('logout/', views.logout_view, name='logout'),
    path('nosotros/', views.nosotros_view, name='nosotros'),
    
    # --- 2. Dashboard General (Redirige según el Rol) ---
    # Esta es la URL que se usa después del login exitoso.
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ==================================
    # 3. RUTAS DE CLIENTE
    # ==================================
    path('cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('cliente/solicitar/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    path('cliente/solicitud/eliminar/<int:pk>/', views.eliminar_solicitud, name='eliminar_solicitud'),

    # ==================================
    # 4. RUTAS DE ADMINISTRADOR
    # ==================================
    path('admin/', views.dashboard_administrador, name='dashboard_administrador'),
    path('admin/historial/', views.historial_solicitudes, name='historial_solicitudes'),
    path('admin/solicitud/gestionar/<int:pk>/', views.gestionar_solicitud, name='gestionar_solicitud'),

    # ==================================
    # 5. RUTAS DE TÉCNICO
    # ==================================
    path('tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('tecnico/perfil/', views.perfil_tecnico, name='perfil_tecnico'),
    path('tecnico/inspeccion/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion'),
]
