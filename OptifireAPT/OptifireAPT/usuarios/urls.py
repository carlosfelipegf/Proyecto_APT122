
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CambioContrasenaForzadoView 

urlpatterns = [
    # =========================================
    # RUTAS PÚBLICAS
    # =========================================
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('nosotros/', views.nosotros_view, name='nosotros'),
    path('notificacion/leida/<int:pk>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('seguridad/cambiar-password/', CambioContrasenaForzadoView.as_view(), name='cambiar_password_forzado'),
    
    # --- Recuperación de contraseña ---
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    # =========================================
    # ROUTER CENTRAL (DASHBOARD)
    # =========================================
    path('dashboard/', views.dashboard, name='dashboard'),
    #  ESTADÍSTICAS
    path('estadisticas/', views.estadisticas_view, name='estadisticas'),

    #  CALENDARIO (API)
    path('api/tecnico/disponibilidad/<int:tecnico_id>/', views.api_disponibilidad_tecnico, name='api_disponibilidad'),

    # =========================================
    # RUTAS CLIENTE
    # =========================================
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('solicitar-inspeccion/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    path('solicitud/detalle/<int:pk>/', views.detalle_orden, name='detalle_orden'),
    path('solicitud/aceptar-cotizacion/<int:pk>/', views.aceptar_cotizacion_cliente, name='aceptar_cotizacion_cliente'),
    path('solicitud/anular/<int:pk>/', views.anular_solicitud, name='anular_solicitud'), 
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    # =========================================
    # RUTAS TÉCNICO
    # =========================================
    path('dashboard/tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('inspeccion/completar/<int:pk>/', views.completar_inspeccion, name='completar_inspeccion'),
    path('perfil/tecnico/', views.perfil_tecnico, name='perfil_tecnico'),
    path('dashboard/tecnico/registro/', views.registro_trabajos, name='registro_trabajos'),

    # 🚨 NUEVA RUTA PARA EL PDF (Puede usarla Cliente, Técnico o Admin) 🚨
    path('inspeccion/acta/<int:pk>/', views.descargar_acta, name='descargar_acta'),

    # =========================================
    # RUTAS ADMINISTRADOR
    # =========================================
    path('dashboard/admin/', views.dashboard_administrador, name='dashboard_administrador'),
    path('historial/', views.historial_solicitudes, name='historial_solicitudes'),
    path('admin/solicitud/detalle/<int:pk>/', views.ver_detalle_solicitud, name='ver_detalle_solicitud'),
    # Gestión de Usuarios
    path('usuarios/', views.admin_usuarios_list, name='admin_usuarios_list'),
    path('usuarios/crear/', views.admin_usuario_crear, name='admin_usuario_crear'),
    path('usuarios/editar/<int:pk>/', views.admin_usuario_editar, name='admin_usuario_editar'),
    path('usuarios/eliminar/<int:pk>/', views.admin_usuario_eliminar, name='admin_usuario_eliminar'),
    # Nueva ruta para finanzas
    path('admin/facturacion/<int:pk>/', views.enviar_orden_facturacion, name='enviar_orden_facturacion'),
    # Gestión de Solicitudes
    path('solicitud/gestionar/<int:pk>/', views.aprobar_solicitud, name='gestionar_solicitud'),
]