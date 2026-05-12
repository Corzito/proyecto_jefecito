from django import forms
from .models import Colaborador, JefeInmediato


class JefeInmediatoForm(forms.ModelForm):
    class Meta:
        model = JefeInmediato
        fields = ['nombre', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ING. JAVIER MOJICA',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.com',
            }),
        }


class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = [
            'cedula', 'nombres', 'cargo', 'jefe_inmediato',
            'empresa', 'celular', 'fecha_ingreso'
        ]
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1055247375',
            }),
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo',
            }),
            'jefe_inmediato': forms.Select(attrs={
                'class': 'form-control',
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-control',
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'No. Celular',
            }),
            'fecha_ingreso': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }