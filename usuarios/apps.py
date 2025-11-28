from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        # 🚨 Importamos las señales para asegurarnos de que se conecten 🚨
        import usuarios.signals