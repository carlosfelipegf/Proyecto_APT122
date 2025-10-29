# usuarios/urls.py
# Este archivo contiene solo las rutas que son relativas al prefijo 'usuarios/'

from django.urls import path
from . import views # Importamos todas las vistas de la app 'usuarios'

urlpatterns = [

    # ----------------------------------------
    # 1. RUTAS DE DASHBOARDS
    # ----------------------------------------
    # path('') resuelve: /usuarios/ -> Dashboard principal (redirección por rol)
    path('', views.dashboard, name='dashboard'), 
    
    # Dashboards específicos
    path('cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('administrador/', views.dashboard_administrador, name='dashboard_administrador'),
    path('tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    
    # ----------------------------------------
    # 2. VISTAS DE CLIENTE
    # ----------------------------------------
    # path('solicitar/') resuelve: /usuarios/solicitar/
    path('solicitar/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    path('solicitud/eliminar/<int:pk>/', views.eliminar_solicitud, name='eliminar_solicitud'),

    # URL para ver el detalle de la orden
    path('orden/<int:pk>/detalle/', views.detalle_orden, name='detalle_orden'),
    
    # URL para descargar el acta (Agregada para resolver el NoReverseMatch)
    path('inspeccion/<int:pk>/descargar_acta/', views.descargar_acta, name='descargar_acta'),
    
    # ----------------------------------------
    # 3. VISTAS DE ADMINISTRADOR
    # ----------------------------------------
    path('admin/historial/', views.historial_solicitudes, name='historial_solicitudes'),
    path('admin/gestionar/<int:pk>/', views.aprobar_solicitud, name='aprobar_solicitud'), 
    path('admin/usuarios/', views.admin_usuarios_list, name='admin_usuarios_list'),
    path('admin/usuarios/nuevo/', views.admin_usuario_crear, name='admin_usuario_crear'),
    path('admin/usuarios/<int:pk>/editar/', views.admin_usuario_editar, name='admin_usuario_editar'),
    path('admin/usuarios/<int:pk>/eliminar/', views.admin_usuario_eliminar, name='admin_usuario_eliminar'),
    
    # ----------------------------------------
    # 4. VISTAS DE TÉCNICO
    # ----------------------------------------
    # path('tecnico/completar/') resuelve: /usuarios/tecnico/completar/
    path('tecnico/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion'),
    path('tecnico/perfil/', views.perfil_tecnico, name='perfil_tecnico'),
    
    # Ruta alternativa para completar la inspección (se mantiene para compatibilidad)
    path('tecnico/inspeccion/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion_alt'),

]