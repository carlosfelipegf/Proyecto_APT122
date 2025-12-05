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
    # Campos extra que no están en el modelo User directamente
    rol = forms.ChoiceField(choices=Roles.choices, label="Rol del Usuario", widget=forms.Select(attrs={'class': 'form-select'}))
    rut = forms.CharField(label="RUT", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Contraseña")
    confirmar_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Confirmar Contraseña")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    # 1. VALIDACIÓN DE RUT (Lógica Chilena en Python)
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        # Limpiar puntos y guión, y convertir a mayúsculas
        rut_limpio = rut.replace(".", "").replace("-", "").upper()
        
        # Validación básica de longitud
        if len(rut_limpio) < 8:
            raise forms.ValidationError("El RUT es demasiado corto.")

        # Separar cuerpo y dígito verificador
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]

        # CORRECCIÓN: Validar que el cuerpo sea numérico antes de calcular
        if not cuerpo.isdigit():
            raise forms.ValidationError("El cuerpo del RUT debe contener solo números.")

        # Algoritmo Modulo 11
        suma = 0
        multiplo = 2
        for i in reversed(cuerpo):
            suma += int(i) * multiplo
            multiplo = 2 if multiplo == 7 else multiplo + 1
        
        dv_esperado = 11 - (suma % 11)
        dv_esperado = '0' if dv_esperado == 11 else 'K' if dv_esperado == 10 else str(dv_esperado)

        if dv != dv_esperado:
            raise forms.ValidationError("El RUT ingresado es inválido (Dígito verificador incorrecto).")
        
        return rut  # Retornamos el valor limpio o original si pasa

    # 2. VALIDACIÓN DE CONTRASEÑA SEGURA (Regex)
    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Regex: Al menos 1 minúscula, 1 mayúscula, 1 número, min 8 caracteres
        regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
        
        if not re.match(regex, password):
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.")
        return password

    # 3. VALIDACIÓN GENERAL (Coincidencia de contraseñas)
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirmar_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirmar_password', "Las contraseñas no coinciden.")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            
            # Guardar Rol
            rol_seleccionado = self.cleaned_data['rol']
            grupo, _ = Group.objects.get_or_create(name=rol_seleccionado)
            user.groups.add(grupo)
            
            # Guardar RUT en Perfil
            perfil, _ = Perfil.objects.get_or_create(usuario=user)
            perfil.rut = self.cleaned_data['rut']
            perfil.save()
            
            # Lógica Superadmin
            if rol_seleccionado == Roles.ADMINISTRADOR:
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            user.save()
            
        return user

class UsuarioAdminUpdateForm(forms.ModelForm):
    """Formulario para editar usuarios existentes."""
    rol = forms.ChoiceField(choices=Roles.choices, label="Rol del Usuario", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        # ... (tus widgets siguen igual) ...

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
        
        # LÓGICA DE SUPER ADMIN AL EDITAR
        rol_seleccionado = self.cleaned_data['rol']
        
        if rol_seleccionado == Roles.ADMINISTRADOR:
            user.is_staff = True
            user.is_superuser = True
        else:
            # Si le bajan el rango a Técnico o Cliente, pierde los poderes
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()
            
            # Actualizar Grupo
            user.groups.clear()
            grupo, _ = Group.objects.get_or_create(name=rol_seleccionado)
            user.groups.add(grupo)
            
        return user

# ==========================================================
# 3. FORMULARIOS DE PERFIL (DIVIDIDOS POR ROL)
# ==========================================================

# Formulario base para datos del modelo USER (Nombre, Apellido, Email)
class UsuarioPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# Formulario EXCLUSIVO para Técnicos (Ve región, ciudad, etc.)
class TecnicoPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        # 1. AGREGAMOS 'fecha_contratacion' A LA LISTA DE CAMPOS
        fields = ['foto', 'telefono', 'region', 'ciudad', 'descripcion', 'fecha_contratacion']
        
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9...'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Experiencia y certificaciones'}),
            
            # 2. AGREGAMOS EL WIDGET DE CALENDARIO
            'fecha_contratacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

# Formulario EXCLUSIVO para Clientes (Ve empresa, rubro, dirección)
class ClientePerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'telefono', 'direccion', 'rubro', 'rut_empresa', 'descripcion']
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección casa matriz'}),
            'rubro': forms.TextInput(attrs={'class': 'form-control'}),
            'rut_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Información sobre la empresa...'}),
        }

# ==========================================================
# 4. FORMULARIO DE APROBACIÓN (Admin)
# ==========================================================
class AprobacionInspeccionForm(forms.Form):
    # Este formulario es manejado principalmente en el HTML manualmente,
    # pero lo dejamos aquí para que la importación en views.py no falle.
    pass