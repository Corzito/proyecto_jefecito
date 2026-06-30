from django.contrib import admin
from .models import Colaborador


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombres', 'cargo', 'empresa', 'fecha_ingreso', 'dias_en_empresa', 'estado_periodo']
    list_filter = ['empresa', 'alerta_30_enviada', 'alerta_50_enviada']
    search_fields = ['cedula', 'nombres', 'cargo']
    readonly_fields = ['alerta_30_enviada', 'alerta_50_enviada', 'created_at']