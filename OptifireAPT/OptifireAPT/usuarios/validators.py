import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ValidarComplejidad:
    def validate(self, password, user=None):
        # 1. Verificar Mayúscula
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper',
            )

        # 2. Verificar Minúscula
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra minúscula."),
                code='password_no_lower',
            )

        # 3. Verificar Número
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un número."),
                code='password_no_number',
            )

        # 4. Verificar Símbolo (Opcional, pero recomendado)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un símbolo especial (!@#$%^&*)."),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Tu contraseña debe contener al menos una mayúscula, una minúscula, un número y un símbolo especial."
        )