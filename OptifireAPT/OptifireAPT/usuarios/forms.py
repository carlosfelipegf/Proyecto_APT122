# usuarios/forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

# Importaciones de modelos y constantes de roles (Grupos)
from .models import SolicitudInspeccion, PlantillaInspeccion 
from .models import ROL_ADMINISTRADOR, ROL_TECNICO, ROL_CLIENTE

User = get_user_model()

ROLE_NAMES = [ROL_ADMINISTRADOR, ROL_TECNICO, ROL_CLIENTE]
ROLE_CHOICES = (
    (ROL_ADMINISTRADOR, "Administrador"),
    (ROL_TECNICO, "Técnico"),
    (ROL_CLIENTE, "Cliente"),
)

SPANISH_LABELS_COMMON = {
    'username': 'Nombre de usuario',
    'first_name': 'Nombre',
    'last_name': 'Apellido',
    'email': 'Correo electrónico',
    'rol': 'Rol del usuario',
    'is_active': 'Usuario activo',
}

SPANISH_HELP_TEXTS_CREATE = {
    'username': 'Obligatorio. 150 caracteres o menos. Solo letras, números y @/./+/-/_.',
    'email': 'Opcional. Se utiliza para notificaciones.',
    'password1': 'Debe tener al menos 8 caracteres y no puede ser completamente numérica.',
    'password2': 'Introduce la misma contraseña nuevamente para confirmarla.',
}

SPANISH_HELP_TEXTS_UPDATE = {
    'username': 'Obligatorio. 150 caracteres o menos. Solo letras, números y @/./+/-/_.',
    'email': 'Opcional. Se utiliza para notificaciones.',
}


def assign_role_group(user, role_name):
    """Ensure the user belongs only to the selected role group."""
    if role_name not in ROLE_NAMES:
        return

    groups_to_clear = Group.objects.filter(name__in=ROLE_NAMES)
    user.groups.remove(*groups_to_clear)

    group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.add(group)

    user.is_staff = role_name == ROL_ADMINISTRADOR


# ==========================================================
# 1. Formulario para el Cliente (Solicitud)
# ==========================================================
class SolicitudInspeccionForm(forms.ModelForm):
    
    class Meta:
        model = SolicitudInspeccion
        fields = [
            'nombre_cliente', 
            'apellido_cliente', 
            'direccion', 
            'telefono', 
            'maquinaria', 
            'observaciones_cliente'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('nombre_cliente', css_class='form-group col-md-6 mb-0'),
                Column('apellido_cliente', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('direccion', css_class='form-group col-md-8 mb-0'),
                Column('telefono', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'maquinaria',
            'observaciones_cliente',
            
            Submit('submit', 'Crear Solicitud de Inspección', css_class='btn-success mt-4')
        )

# ==========================================================
# 2. Formulario para el Administrador (Aprobación/Rechazo)
# ==========================================================
class AprobacionInspeccionForm(forms.Form):
    
    # Campo oculto para manejar la acción de forma clara en la vista
    ACCIONES = (
        ('APROBAR', 'Aprobar Solicitud y Asignar'),
        ('RECHAZAR', 'Rechazar Solicitud'),
    )
    accion = forms.ChoiceField(
        choices=ACCIONES, 
        initial='APROBAR', 
        label="Acción a realizar",
        widget=forms.Select(attrs={'onchange': 'toggleFields(this.value)'}) 
    )
    
    # 🚨 SOLUCIÓN: Filtrar por GRUPO DE DJANGO, NO por campo 'rol' inexistente 🚨
    tecnico = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name=ROL_TECNICO).order_by('first_name'), 
        label="Técnico a asignar",
        required=False 
    )
    plantilla = forms.ModelChoiceField(
        queryset=PlantillaInspeccion.objects.all(),
        label="Plantilla de Inspección",
        required=False 
    )
    
    motivo_rechazo = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), 
        required=False, 
        label="Motivo del Rechazo (Requerido si se rechaza)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        # Este campo será llenado automáticamente con un nombre basado en la solicitud
        self.fields['nombre_inspeccion'] = forms.CharField(
            max_length=200, 
            label="Título de la Inspección", 
            required=False, 
            initial="Inspección de [Cliente]" # Se inicializará en la vista
        )

        self.helper.layout = Layout(
            'accion',
            
            # Campos de APROBACIÓN
            Div(
                'nombre_inspeccion',
                'tecnico',
                'plantilla',
                css_id='aprobacion-fields',
            ),
            
            # Campos de RECHAZO
            Div(
                'motivo_rechazo',
                css_id='rechazo-fields',
                style="display:none;"
            ),
            
            Submit('submit', 'Confirmar Acción', css_class='btn-primary mt-3')
        )

    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')

        if accion == 'APROBAR':
            if not cleaned_data.get('tecnico'):
                self.add_error('tecnico', "Debe seleccionar un técnico para aprobar la solicitud.")
            if not cleaned_data.get('plantilla'):
                self.add_error('plantilla', "Debe seleccionar una plantilla para aprobar la solicitud.")
            
        elif accion == 'RECHAZAR':
            if not cleaned_data.get('motivo_rechazo'):
                self.add_error('motivo_rechazo', "Debe ingresar un motivo para rechazar la solicitud.")
                
        return cleaned_data


# ==========================================================
# 3. Formularios de Administración de Usuarios
# ==========================================================
class UsuarioAdminCreateForm(UserCreationForm):
    rol = forms.ChoiceField(choices=ROLE_CHOICES, label="Rol del Usuario")
    is_active = forms.BooleanField(label="Usuario activo", required=False, initial=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'

        for name, label in {**SPANISH_LABELS_COMMON, 'password1': 'Contraseña', 'password2': 'Confirmar contraseña'}.items():
            if name in self.fields:
                self.fields[name].label = label

        for name, help_text in SPANISH_HELP_TEXTS_CREATE.items():
            if name in self.fields:
                self.fields[name].help_text = help_text

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.is_active = self.cleaned_data.get('is_active', True)
        user.is_staff = self.cleaned_data['rol'] == ROL_ADMINISTRADOR

        if commit:
            user.save()
            assign_role_group(user, self.cleaned_data['rol'])
        else:
            # Defer group assignment until the instance is persisted.
            self._pending_role = self.cleaned_data['rol']

        return user

    def save_m2m(self):
        super().save_m2m()
        role = getattr(self, '_pending_role', None)
        if role and self.instance.pk:
            assign_role_group(self.instance, role)


class UsuarioAdminUpdateForm(forms.ModelForm):
    rol = forms.ChoiceField(choices=ROLE_CHOICES, label="Rol del Usuario")
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput,
        required=False,
        strip=False,
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput,
        required=False,
        strip=False,
    )

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        role_group = self.instance.groups.filter(name__in=ROLE_NAMES).first()
        if role_group:
            self.fields['rol'].initial = role_group.name
        self.fields['password1'].help_text = 'Deja en blanco para mantener la contraseña actual.'
        self.fields['password2'].help_text = 'Confirma la nueva contraseña si decides cambiarla.'
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'

        for name, label in {**SPANISH_LABELS_COMMON, 'password1': 'Nueva contraseña', 'password2': 'Confirmar contraseña'}.items():
            if name in self.fields:
                self.fields[name].label = label

        for name, help_text in SPANISH_HELP_TEXTS_UPDATE.items():
            if name in self.fields:
                self.fields[name].help_text = help_text

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', "Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        role = self.cleaned_data['rol']

        if password1:
            user.set_password(password1)

        user.is_staff = role == ROL_ADMINISTRADOR

        if commit:
            user.save()
            assign_role_group(user, role)
        else:
            self._pending_role = role

        return user

    def save_m2m(self):
        super().save_m2m()
        role = getattr(self, '_pending_role', None)
        if role and self.instance.pk:
            assign_role_group(self.instance, role)