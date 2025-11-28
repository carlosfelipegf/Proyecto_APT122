from django.urls import path
from . import views

urlpatterns = [

    # =========================================
    # RUTAS PÚBLICAS
    # =========================================
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('nosotros/', views.nosotros_view, name='nosotros'),
    path('notificacion/leida/<int:pk>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),

    # =========================================
    # RUTAS DE SEGURIDAD
    # =========================================
    # 1. Cambio obligatorio de contraseña
    path('seguridad/cambiar-clave-obligatorio/', views.cambiar_clave_obligatorio, name='cambiar_clave_obligatorio'),

    # 2. Recuperación de contraseña
    path('reset-password/', views.password_reset_request_view, name='password_reset_request'),
    path('reset-password/confirm/<str:uidb64>/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),

    # =========================================
    # ROUTER CENTRAL (DASHBOARD)
    # =========================================
    path('dashboard/', views.dashboard, name='dashboard'),

    # =========================================
    # RUTAS CLIENTE
    # =========================================
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('solicitar-inspeccion/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    path('solicitud/detalle/<int:pk>/', views.detalle_orden, name='detalle_orden'),
    path('solicitud/anular/<int:pk>/', views.anular_solicitud, name='anular_solicitud'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    # =========================================
    # RUTAS TÉCNICO
    # =========================================
    path('dashboard/tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('inspeccion/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion'),
    path('perfil/tecnico/', views.perfil_tecnico, name='perfil_tecnico'),
    path('notificacion/leida/<int:pk>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),

    # 🟦 DESCARGA DE PDF DE ACTA (Cliente, Técnico o Admin)
    path('inspeccion/acta/<int:pk>/', views.descargar_acta, name='descargar_acta'),

    # =========================================
    # RUTAS ADMINISTRADOR
    # =========================================
    path('dashboard/admin/', views.dashboard_administrador, name='dashboard_administrador'),
    path('historial/', views.historial_solicitudes, name='historial_solicitudes'),

    # Gestión de Usuarios
    path('usuarios/', views.admin_usuarios_list, name='admin_usuarios_list'),
    path('usuarios/crear/', views.admin_usuario_crear, name='admin_usuario_crear'),
    path('usuarios/editar/<int:pk>/', views.admin_usuario_editar, name='admin_usuario_editar'),
    path('usuarios/eliminar/<int:pk>/', views.admin_usuario_eliminar, name='admin_usuario_eliminar'),

    # Gestión de Solicitudes
    path('solicitud/gestionar/<int:pk>/', views.aprobar_solicitud, name='gestionar_solicitud'),
]
