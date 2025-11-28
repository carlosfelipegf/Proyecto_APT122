from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import password_validation

from .models import (
    SolicitudInspeccion,
    Perfil,
    Roles,
    EstadoSolicitud
)

# ==========================================================
# 1. FORMULARIO DE SOLICITUD (CLIENTE)
# ==========================================================
class SolicitudInspeccionForm(forms.ModelForm):
    class Meta:
        model = SolicitudInspeccion
        fields = [
            'nombre_cliente', 'apellido_cliente',
            'direccion', 'telefono',
            'maquinaria', 'observaciones_cliente'
        ]
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'maquinaria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# ==========================================================
# 2. FORMULARIOS ADMINISTRATIVOS (CREATE / UPDATE)
# ==========================================================
class UsuarioAdminCreateForm(forms.ModelForm):
    """Formulario para crear usuarios y asignar Rol."""
    rol = forms.ChoiceField(
        choices=Roles.choices,
        label="Rol del Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()

            # Asignación de Rol (grupo)
            rol = self.cleaned_data['rol']
            grupo, _ = Group.objects.get_or_create(name=rol)
            user.groups.add(grupo)

            # Crear Perfil
            # NOTA: Perfil.objects.get_or_create(usuario=user) 
            # Debería usar 'user' en lugar de 'usuario' si el campo es 'user' en Perfil,
            # como se define en la solución original: Perfil.objects.get_or_create(user=user)
            # Asegúrate de que el campo sea 'user' o cámbialo a 'usuario' si es así.
            Perfil.objects.get_or_create(user=user)

        return user


class UsuarioAdminUpdateForm(forms.ModelForm):
    """Editar usuario existente + actualizar rol."""
    rol = forms.ChoiceField(
        choices=Roles.choices,
        label="Rol del Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            grupos = self.instance.groups.values_list('name', flat=True)
            if Roles.ADMINISTRADOR in grupos:
                self.initial['rol'] = Roles.ADMINISTRADOR
            elif Roles.TECNICO in grupos:
                self.initial['rol'] = Roles.TECNICO
            else:
                self.initial['rol'] = Roles.CLIENTE

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.groups.clear()

            rol = self.cleaned_data['rol']
            grupo, _ = Group.objects.get_or_create(name=rol)
            user.groups.add(grupo)

        return user

# ==========================================================
# 3. FORMULARIOS DE PERFIL (TÉCNICO / CLIENTE)
# ==========================================================
class UsuarioPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class TecnicoPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'telefono', 'region', 'ciudad', 'descripcion', 'fecha_contratacion']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'fecha_contratacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ClientePerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'telefono', 'direccion', 'rubro', 'rut_empresa', 'descripcion']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'rubro': forms.TextInput(attrs={'class': 'form-control'}),
            'rut_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# ==========================================================
# 4. FORMULARIOS DE SEGURIDAD (NUEVOS)
# ==========================================================
class CambioClaveObligatorioForm(SetPasswordForm):
    """Cambio de contraseña obligatorio + validación fuerte."""
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

        self.fields['new_password1'].label = "Nueva Contraseña"
        self.fields['new_password2'].label = "Confirmar Nueva Contraseña"

        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingresa tu nueva clave'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repite la nueva clave'
        })

    # 🚨 CORRECCIÓN DEL ERROR 'super' object has no attribute 'clean_new_password2' 🚨
    def clean_new_password2(self):
        # 1. Obtener el valor del campo del diccionario cleaned_data
        new_password2 = self.cleaned_data.get('new_password2')
        
        # 2. Aplicar las validaciones de seguridad de Django (si el valor existe)
        if new_password2:
            password_validation.validate_password(new_password2, self.user)
            
        return new_password2


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu email registrado'
        })
    )

# ==========================================================
# 5. FORMULARIO DE APROBACIÓN (ADMIN)
# ==========================================================
class AprobacionInspeccionForm(forms.Form):
    pass