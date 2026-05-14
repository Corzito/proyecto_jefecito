from django import forms
from .models import Colaborador


class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = [
            'cedula', 'nombres', 'cargo', 'jefe_inmediato',
            'correo_jefe', 'empresa', 'celular', 'fecha_ingreso'
        ]
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1055247375'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo'}),
            'jefe_inmediato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del jefe'}),
            'correo_jefe': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}),
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No. Celular'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }