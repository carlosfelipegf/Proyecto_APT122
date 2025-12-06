from django import forms
from django.contrib.auth.models import User, Group
import re
from django.core.exceptions import ValidationError
from .models import (
    SolicitudInspeccion,
    Perfil,
    Roles,
    EstadoSolicitud
)

# ==========================================================
# 0. FORMULARIO DE PERFIL ADMIN (COMBINADO)
# ==========================================================

class AdminPerfilForm(forms.ModelForm):
    # Campos del modelo User
    first_name = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Apellidos",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = Perfil
        # Ajustado a los nuevos campos del modelo Perfil
        fields = [
            'foto',
            'descripcion',
            'telefono',
            'direccion',
            'region',
            'ciudad',
        ]
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        perfil = super().save(commit=False)

        # Actualizar datos del usuario asociado
        if self.instance.usuario:
            self.instance.usuario.first_name = self.cleaned_data['first_name']
            self.instance.usuario.last_name = self.cleaned_data['last_name']
            self.instance.usuario.save()

        if commit:
            perfil.save()

        return perfil


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
            'maquinaria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                'placeholder': 'Describe la maquinaria o equipo a inspeccionar'}),
            'observaciones_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                           'placeholder': 'Instrucciones adicionales (opcional)'}),
        }


# ==========================================================
# 2. FORMULARIOS DE ADMINISTRACIÓN DE USUARIOS
# ==========================================================

class UsuarioAdminCreateForm(forms.ModelForm):
    rol = forms.ChoiceField(
        choices=Roles.choices,
        label="Rol del Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    rut = forms.CharField(
        label="RUT",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña"
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar Contraseña"
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

    # ----------------------------
    # VALIDACIÓN RUT CHILENO
    # ----------------------------
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        rut_limpio = rut.replace(".", "").replace("-", "").upper()

        if len(rut_limpio) < 8:
            raise forms.ValidationError("El RUT es demasiado corto.")

        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]

        if not cuerpo.isdigit():
            raise forms.ValidationError("El cuerpo del RUT debe contener solo números.")

        suma = 0
        multiplo = 2

        for i in reversed(cuerpo):
            suma += int(i) * multiplo
            multiplo = 2 if multiplo == 7 else multiplo + 1

        dv_esperado = 11 - (suma % 11)
        dv_esperado = '0' if dv_esperado == 11 else 'K' if dv_esperado == 10 else str(dv_esperado)

        if dv != dv_esperado:
            raise forms.ValidationError("El RUT ingresado es inválido.")

        return rut

    # ----------------------------
    # VALIDACIÓN CONTRASEÑA
    # ----------------------------
    def clean_password(self):
        password = self.cleaned_data.get('password')
        regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

        if not re.match(regex, password):
            raise forms.ValidationError(
                "Debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número."
            )
        return password

    # ----------------------------
    # VALIDACIÓN PASSWORD MATCH
    # ----------------------------
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirmar_password")

        if p1 and p2 and p1 != p2:
            self.add_error('confirmar_password', "Las contraseñas no coinciden.")

    # ----------------------------
    # GUARDADO FINAL
    # ----------------------------
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

            rol = self.cleaned_data['rol']
            grupo, _ = Group.objects.get_or_create(name=rol)
            user.groups.add(grupo)

            perfil, _ = Perfil.objects.get_or_create(usuario=user)
            perfil.rut = self.cleaned_data['rut']
            perfil.save()

            if rol == Roles.ADMINISTRADOR:
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False

            user.save()

        return user


class UsuarioAdminUpdateForm(forms.ModelForm):
    rol = forms.ChoiceField(
        choices=Roles.choices,
        label="Rol del Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

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
        rol = self.cleaned_data['rol']

        if rol == Roles.ADMINISTRADOR:
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()
            user.groups.clear()
            grupo, _ = Group.objects.get_or_create(name=rol)
            user.groups.add(grupo)

        return user


# ==========================================================
# 3. FORMULARIOS DE PERFIL POR ROL
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
        fields = [
            'foto', 'telefono', 'direccion',
            'rubro', 'rut_empresa', 'descripcion'
        ]
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'rubro': forms.TextInput(attrs={'class': 'form-control'}),
            'rut_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ==========================================================
# 4. FORMULARIO DE APROBACIÓN (Admin)
# ==========================================================

class AprobacionInspeccionForm(forms.Form):
    pass
