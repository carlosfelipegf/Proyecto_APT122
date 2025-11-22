from .models import Notificacion

def notificaciones_usuario(request):
    if request.user.is_authenticated:
        # Obtenemos las notificaciones NO leídas del usuario actual
        notificaciones = Notificacion.objects.filter(usuario=request.user, leido=False).order_by('-fecha_creacion')
        return {'mis_notificaciones': notificaciones}
    return {}