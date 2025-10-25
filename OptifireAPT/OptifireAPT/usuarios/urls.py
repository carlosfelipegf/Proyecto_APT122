
# usuarios/urls.py
# (Archivo ubicado en la carpeta de la app 'usuarios')


# usuarios/urls.py (CÓDIGO CORREGIDO)


from django.urls import path
from . import views

urlpatterns = [

    # --- 1. Rutas Públicas/Autenticación ---
    
    # Ruta principal (Landing page)
    path('', views.home, name='home'), 
    path('login/', views.login_view, name='login'), # Esta ruta debe estar en el proyecto principal (OptifireAPT/urls.py)

    # VISTAS DE AUTENTICACIÓN
    path('login/', views.login_view, name='login'),

    path('logout/', views.logout_view, name='logout'),
    
    # VISTA CENTRAL DE REDIRECCIÓN
    path('', views.dashboard, name='dashboard'), 
    
    # DASHBOARDS ESPECÍFICOS
    path('cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('administrador/', views.dashboard_administrador, name='dashboard_administrador'),
    path('tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    
    # VISTAS DE CLIENTE
    path('solicitar/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    path('solicitud/eliminar/<int:pk>/', views.eliminar_solicitud, name='eliminar_solicitud'),

    # VISTAS DE ADMINISTRADOR
    path('admin/historial/', views.historial_solicitudes, name='historial_solicitudes'),
    
    # 🚨 LÍNEA CORREGIDA: Apunta a 'aprobar_solicitud' en lugar de 'gestionar_solicitud'
    path('admin/gestionar/<int:pk>/', views.aprobar_solicitud, name='aprobar_solicitud'), 
    
    # VISTAS DE TÉCNICO
    path('tecnico/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion'),
    path('tecnico/perfil/', views.perfil_tecnico, name='perfil_tecnico'),

    path('tecnico/inspeccion/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion'),
]

    # 🚨 VISTAS DE AUTENTICACIÓN (ELIMINADAS: Ahora en OptifireAPT/urls.py)
    # path('login/', views.login_view, name='login'),
    # path('logout/', views.logout_view, name='logout'),
    
    # ----------------------------------------
    # 1. VISTAS DE DASHBOARDS
    # ----------------------------------------
    # La ruta raíz de la app ('usuarios/') lleva al dashboard principal
    path('', views.dashboard, name='dashboard'), # Resuelve /usuarios/
    
    # DASHBOARDS ESPECÍFICOS
    path('cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('administrador/', views.dashboard_administrador, name='dashboard_administrador'),
    path('tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    
    # ----------------------------------------
    # 2. VISTAS DE CLIENTE
    # ----------------------------------------
    path('solicitar/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    path('solicitud/eliminar/<int:pk>/', views.eliminar_solicitud, name='eliminar_solicitud'),

    # ----------------------------------------
    # 3. VISTAS DE ADMINISTRADOR
    # ----------------------------------------
    path('admin/historial/', views.historial_solicitudes, name='historial_solicitudes'),
    path('admin/gestionar/<int:pk>/', views.aprobar_solicitud, name='aprobar_solicitud'), 
    
    # ----------------------------------------
    # 4. VISTAS DE TÉCNICO
    # ----------------------------------------
    path('tecnico/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion'),
    path('tecnico/perfil/', views.perfil_tecnico, name='perfil_tecnico'),
    
    # 🚨 RUTA NOSOTROS (ELIMINADA: Ahora en OptifireAPT/urls.py)
    # path('nosotros/', views.nosotros_view, name='nosotros'),
]


    path('nosotros/', views.nosotros_view, name='nosotros'),
]

