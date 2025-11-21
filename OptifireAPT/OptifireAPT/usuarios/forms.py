from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
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
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'apellido_cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu apellido'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección exacta de la inspección'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 ...'}),
            'maquinaria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe la maquinaria o equipo a inspeccionar'}),
            'observaciones_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Instrucciones adicionales (opcional)'}),
        }

# ==========================================================
# 2. FORMULARIOS DE ADMINISTRACIÓN DE USUARIOS
# ==========================================================
class UsuarioAdminCreateForm(forms.ModelForm):
    """Formulario para que el Admin cree usuarios y les asigne Rol."""
    rol = forms.ChoiceField(choices=Roles.choices, label="Rol del Usuario", widget=forms.Select(attrs={'class': 'form-select'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Contraseña")
    
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
            # Asignar Grupo basado en el Rol seleccionado
            rol_seleccionado = self.cleaned_data['rol']
            grupo, _ = Group.objects.get_or_create(name=rol_seleccionado)
            user.groups.add(grupo)
            # Asegurar que tenga perfil
            Perfil.objects.get_or_create(usuario=user)
        return user

class UsuarioAdminUpdateForm(forms.ModelForm):
    """Formulario para editar usuarios existentes (sin password obligatoria)."""
    rol = forms.ChoiceField(choices=Roles.choices, label="Rol del Usuario", widget=forms.Select(attrs={'class': 'form-select'}))

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
        # Pre-seleccionar el rol actual
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
            # Actualizar Rol
            user.groups.clear()
            rol_seleccionado = self.cleaned_data['rol']
            grupo, _ = Group.objects.get_or_create(name=rol_seleccionado)
            user.groups.add(grupo)
        return user

# ==========================================================
# 3. FORMULARIOS DE PERFIL (Usuario Normal)
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

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'descripcion']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# ==========================================================
# 4. FORMULARIO DE APROBACIÓN (Admin
class AprobacionInspeccionForm(forms.Form):
    # Este formulario es manejado principalmente en el HTML manualmente,
    # pero lo dejamos aquí para que la importación en views.py no falle.
    pass