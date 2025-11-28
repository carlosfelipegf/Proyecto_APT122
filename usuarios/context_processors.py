from .models import Notificacion

def notificaciones_usuario(request):
    """
    Inserta las notificaciones no leídas del usuario actual en el contexto
    para que puedan ser usadas en cualquier plantilla (ej: la campana en el navbar).
    """
    if request.user.is_authenticated:
        # Obtenemos las notificaciones NO leídas del usuario actual
        notificaciones = Notificacion.objects.filter(usuario=request.user, leido=False).order_by('-fecha_creacion')[:10]
        return {'mis_notificaciones': notificaciones}
    return {}