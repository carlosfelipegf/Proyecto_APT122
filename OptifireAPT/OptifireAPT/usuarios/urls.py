# usuarios/urls.py CORREGIDO y LIMPIO

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ==========================================================
    # 0. VISTAS PÚBLICAS Y AUTENTICACIÓN
    # ==========================================================
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('nosotros/', views.nosotros_view, name='nosotros'),

    # RUTAS DE RESTABLECIMIENTO DE CONTRASEÑA (CRÍTICAS PARA EL BOTÓN)
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset_form.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt',
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    # OTRAS RUTAS DE AUTENTICACIÓN
    path('change-password/required/', views.change_password_required_view, name='change_password_required'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    
    # ==========================================================
    # 1. DASHBOARD PRINCIPAL (Redirige por Rol)
    # ==========================================================
    path('dashboard/', views.dashboard, name='dashboard'),

    # ==========================================================
    # 2. VISTAS DEL CLIENTE
    # ==========================================================
    path('cliente/dashboard/', views.dashboard_cliente, name='dashboard_cliente'),
    path('cliente/solicitar/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    
    # 🔥 RUTA CORREGIDA: Usamos anular_solicitud para el botón 🔥
    path('cliente/solicitud/anular/<int:pk>/', views.anular_solicitud, name='anular_solicitud'), 
    
    path('cliente/orden/<int:pk>/', views.detalle_orden, name='detalle_orden'),
    
    # ==========================================================
    # 3. VISTAS DEL ADMINISTRADOR
    # ==========================================================
    path('administrador/dashboard/', views.dashboard_administrador, name='dashboard_administrador'),
    path('administrador/solicitudes/<int:pk>/gestionar/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('administrador/solicitudes/historial/', views.historial_solicitudes, name='historial_solicitudes'),

    # GESTIÓN DE USUARIOS
    path('administrador/usuarios/', views.admin_usuarios_list, name='admin_usuarios_list'),
    path('administrador/usuarios/crear/', views.admin_usuario_crear, name='admin_usuario_crear'),
    path('administrador/usuarios/editar/<int:pk>/', views.admin_usuario_editar, name='admin_usuario_editar'),
    path('administrador/usuarios/eliminar/<int:pk>/', views.admin_usuario_eliminar, name='admin_usuario_eliminar'),

    # 🔥 GESTIÓN DE PLANTILLAS 🔥
    path('administrador/plantillas/', views.plantilla_list, name='plantilla_list'),
    path('administrador/plantillas/crear/', views.plantilla_crear, name='plantilla_crear'),
    path('administrador/plantillas/editar/<int:pk>/', views.plantilla_editar, name='plantilla_editar'),
    path('administrador/plantillas/eliminar/<int:pk>/', views.plantilla_eliminar, name='plantilla_eliminar'),


    # ==========================================================
    # 4. VISTAS DEL TÉCNICO
    # ==========================================================
    path('tecnico/dashboard/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('tecnico/inspeccion/<int:pk>/completar/', views.completar_inspeccion, name='completar_inspeccion'),
    
    # Descarga del acta (para Cliente, Técnico, Admin)
    path('acta/<int:pk>/descargar/', views.descargar_acta, name='descargar_acta'),
]

if settings.DEBUG:
    # Nota: static ya está importado arriba.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)