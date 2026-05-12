"""
Comando: python manage.py enviar_alertas_periodo

Ejecutar diariamente con Celery Beat o cron.
Envía correo cuando faltan 7 días para la evaluación de 30 y 50 días.
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from _periodo_de_prueba.models import Colaborador


CORREO_RRHH = 'cristian.barrera@incarsa.com.co'  # <-- Cambia este correo


class Command(BaseCommand):
    help = 'Envía alertas por correo cuando faltan 7 días para evaluaciones de periodo de prueba'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        colaboradores = Colaborador.objects.all()

        enviados_30 = 0
        enviados_50 = 0

        for col in colaboradores:
            dias = (hoy - col.fecha_ingreso).days

            # ALERTA 30 DÍAS: cuando lleva 23 días (faltan 7 para los 30)
            if dias == 23 and not col.alerta_30_enviada:
                self._enviar_correo_alerta(col, 30, 7)
                col.alerta_30_enviada = True
                col.save(update_fields=['alerta_30_enviada'])
                enviados_30 += 1
                self.stdout.write(self.style.WARNING(
                    f'[ALERTA 30] {col.nombres} - {col.empresa} - faltan 7 días'
                ))

            # ALERTA 50 DÍAS: cuando lleva 43 días (faltan 7 para los 50)
            if dias == 43 and not col.alerta_50_enviada:
                self._enviar_correo_alerta(col, 50, 7)
                col.alerta_50_enviada = True
                col.save(update_fields=['alerta_50_enviada'])
                enviados_50 += 1
                self.stdout.write(self.style.WARNING(
                    f'[ALERTA 50] {col.nombres} - {col.empresa} - faltan 7 días'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'Proceso completado. Alertas 30 días: {enviados_30} | Alertas 50 días: {enviados_50}'
        ))

    def _enviar_correo_alerta(self, colaborador, dias_evaluacion, dias_restantes):
        asunto = (
            f'⚠️ ALERTA PERIODO DE PRUEBA - {colaborador.nombres} '
            f'| Evaluación {dias_evaluacion} días en {dias_restantes} días'
        )
        mensaje = f"""
SISTEMA DE SEGUIMIENTO - PERIODO DE PRUEBA
{'='*50}

Se le informa que el siguiente colaborador requiere evaluación de seguimiento próximamente:

📋 DATOS DEL COLABORADOR:
   • Nombre:         {colaborador.nombres}
   • Cédula:         {colaborador.cedula}
   • Cargo:          {colaborador.cargo}
   • Empresa:        {colaborador.get_empresa_display()}
   • Jefe Inmediato: {colaborador.jefe_inmediato}
   • Celular:        {colaborador.celular}
   • Fecha Ingreso:  {colaborador.fecha_ingreso.strftime('%d/%m/%Y')}

⏰ EVALUACIÓN PENDIENTE:
   • Tipo:           Evaluación de {dias_evaluacion} días
   • Días restantes: {dias_restantes} días para realizar la evaluación

Por favor, coordinar con el jefe inmediato ({colaborador.jefe_inmediato}) 
para programar la evaluación de seguimiento.

{'='*50}
Sistema de Seguimiento - Periodo de Prueba
        """.strip()

        try:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[CORREO_RRHH],
                fail_silently=False,
            )
        except Exception as e:
            print(f'Error enviando correo para {colaborador.nombres}: {e}')