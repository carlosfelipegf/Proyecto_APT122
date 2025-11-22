from django.urls import path
from django.contrib.auth import views as auth_views # Importamos vistas de auth de Django
from . import views

urlpatterns = [
    # ----------------------------------------
    # A. RUTAS DE DASHBOARDS
    # ----------------------------------------
    path('', views.dashboard, name='dashboard'), # Redirección principal post-login
    path('admin/', views.dashboard_administrador, name='dashboard_administrador'),
    path('tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    
    # ----------------------------------------
    # B. 🔑 RUTAS DE CAMBIO DE CONTRASEÑA OBLIGATORIO 🔑
    # ----------------------------------------
    # 1. Muestra el formulario: Usa la vista nativa de Django (PasswordChangeView)
    path('cambiar-password/', 
        auth_views.PasswordChangeView.as_view(
            template_name='perfil/password_change_form.html', 
            # Redirigimos a nuestra vista personalizada después del cambio exitoso
            success_url='/usuarios/password-cambiada/' 
        ), 
        name='password_change_obligatorio'
    ),
    # 2. Después del cambio exitoso: Vista personalizada para marcar el flag
    path('password-cambiada/', views.password_changed_done_view, name='password_change_done'),

    # ----------------------------------------
    # C. RUTAS DE ADMINISTRADOR
    # ----------------------------------------
    path('historial/', views.historial_solicitudes, name='historial_solicitudes'),
    # Nota: Cambié el nombre de la URL de gestionar_solicitud a aprobar_solicitud para que coincida con la vista
    path('solicitud/<int:pk>/gestionar/', views.aprobar_solicitud, name='aprobar_solicitud'), 
    path('usuarios/', views.admin_usuarios_list, name='admin_usuarios_list'),
    path('usuarios/crear/', views.admin_usuario_crear, name='admin_usuario_crear'),
    path('usuarios/editar/<int:pk>/', views.admin_usuario_editar, name='admin_usuario_editar'),
    path('usuarios/eliminar/<int:pk>/', views.admin_usuario_eliminar, name='admin_usuario_eliminar'),
    
    # ----------------------------------------
    # D. RUTAS DE TÉCNICO
    # ----------------------------------------
    path('inspeccion/<int:pk>/completar/', views.completar_inspeccion, name='completar_inspeccion'),
    path('tecnico/perfil/', views.perfil_tecnico, name='perfil_tecnico'),
    
    # ----------------------------------------
    # E. RUTAS DE CLIENTE
    # ----------------------------------------
    path('solicitar/', views.solicitar_inspeccion, name='solicitar_inspeccion'),
    path('orden/<int:pk>/detalle/', views.detalle_orden, name='detalle_orden'),
    path('orden/<int:pk>/anular/', views.anular_solicitud, name='anular_solicitud'),

    # ----------------------------------------
    # F. RUTAS DE PERFIL COMÚN
    # ----------------------------------------
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    
    # ----------------------------------------
    # G. RUTAS API DE NOTIFICACIONES (¡NUEVO!)
    # ----------------------------------------
    # Estas rutas serán llamadas por JavaScript para obtener y marcar como leídas las notificaciones
    path('api/notifications/get/', views.get_notifications, name='get_notifications_api'),
    path('api/notifications/read/', views.mark_as_read, name='mark_as_read_api'),
    
    # ----------------------------------------
    # H. 🔄 RUTAS DE RECUPERACIÓN DE CONTRASEÑA (SOLUCIÓN) 🔄
    # ----------------------------------------
    # 1. Envía el correo de reseteo: El botón de "Recuperar Contraseña" debe apuntar a este nombre de URL.
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), 
         name='password_reset'
    ),
    # 2. Pantalla de confirmación de correo enviado.
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
         name='password_reset_done'
    ),
    # 3. Formulario para ingresar la nueva contraseña (recibida por email).
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
         name='password_reset_confirm'
    ),
    # 4. Pantalla de éxito después de cambiar la contraseña.
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
         name='password_reset_complete'
    ),
]