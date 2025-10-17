# usuarios/forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

# Importaciones de modelos y constantes de roles (Grupos)
from .models import SolicitudInspeccion, PlantillaInspeccion 
from .models import ROL_TECNICO # Solo necesitamos esta constante para el queryset

User = get_user_model()

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