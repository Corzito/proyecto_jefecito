from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from _periodo_de_prueba.models import Colaborador

CORREO_CRISTIAN = 'cristian.barrera@incarsa.com.co'
BASE_URL = 'https://proyecto-jefecito.onrender.com'


class Command(BaseCommand):
    help = 'Envía alertas por correo cuando faltan 7 días para evaluaciones de periodo de prueba'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        colaboradores = Colaborador.objects.all()
        enviados_30 = 0
        enviados_50 = 0

        for col in colaboradores:
            dias = (hoy - col.fecha_ingreso).days

            if dias == 23 and not col.alerta_30_enviada:
                self._enviar_correo_cristian(col)
                col.alerta_30_enviada = True
                col.save(update_fields=['alerta_30_enviada'])
                enviados_30 += 1
                self.stdout.write(self.style.WARNING(
                    f'[ALERTA 30] {col.nombres} - {col.empresa} - faltan 7 días'
                ))

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

    def _enviar_correo_cristian(self, colaborador):
        url_boton = f"{BASE_URL}/periodo/enviar-jefe/{colaborador.pk}/"
        correo_jefe = colaborador.correo_jefe or 'Sin correo registrado'

        asunto = (
            f'⚠️ ALERTA PERIODO DE PRUEBA - {colaborador.nombres} '
            f'| Evaluación 30 días en 7 días'
        )
        mensaje_html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif; max-width:600px; margin:0 auto;">
    <div style="background-color:#E32822; padding:20px; text-align:center;">
        <h2 style="color:white; margin:0;">⚠️ ALERTA PERIODO DE PRUEBA</h2>
    </div>
    <div style="padding:20px; background-color:#f9f9f9;">
        <p>Se requiere evaluación de seguimiento para el siguiente colaborador:</p>
        <table style="width:100%; border-collapse:collapse; margin:15px 0;">
            <tr style="background:#fff;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Nombre</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.nombres}</td>
            </tr>
            <tr style="background:#f2f2f2;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Cédula</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.cedula}</td>
            </tr>
            <tr style="background:#fff;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Cargo</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.cargo}</td>
            </tr>
            <tr style="background:#f2f2f2;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Empresa</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.get_empresa_display()}</td>
            </tr>
            <tr style="background:#fff;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Jefe Inmediato</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.jefe_inmediato}</td>
            </tr>
            <tr style="background:#f2f2f2;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Celular</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.celular}</td>
            </tr>
            <tr style="background:#fff;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Fecha Ingreso</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.fecha_ingreso.strftime('%d/%m/%Y')}</td>
            </tr>
            <tr style="background:#f2f2f2;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Días en empresa</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.dias_en_empresa()} días (faltan 7 para evaluación)</td>
            </tr>
        </table>
        <div style="text-align:center; margin:25px 0;">
            <a href="{url_boton}"
               style="background-color:#E32822; color:white; padding:14px 28px;
                      text-decoration:none; border-radius:5px; font-size:16px;
                      font-weight:bold; display:inline-block;">
                📧 Enviar Alerta a Jefe Inmediato
            </a>
        </div>
        <p style="color:#666; font-size:12px; text-align:center;">
            Al hacer click se enviará automáticamente un correo a:
            <strong>{correo_jefe}</strong>
        </p>
    </div>
    <div style="background-color:#333; padding:10px; text-align:center;">
        <p style="color:#aaa; font-size:11px; margin:0;">Sistema de Seguimiento - Periodo de Prueba</p>
    </div>
</body>
</html>
        """.strip()

        try:
            email = EmailMultiAlternatives(
                subject=asunto,
                body=f"Alerta periodo de prueba: {colaborador.nombres}. Abra en HTML para ver el botón.",
                from_email=settings.EMAIL_HOST_USER,
                to=[CORREO_CRISTIAN],
            )
            email.attach_alternative(mensaje_html, "text/html")
            email.send(fail_silently=False)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error enviando correo para {colaborador.nombres}: {e}'))

    def _enviar_correo_alerta(self, colaborador, dias_evaluacion, dias_restantes):
        asunto = (
            f'⚠️ ALERTA PERIODO DE PRUEBA - {colaborador.nombres} '
            f'| Evaluación {dias_evaluacion} días en {dias_restantes} días'
        )
        mensaje = f"""
SISTEMA DE SEGUIMIENTO - PERIODO DE PRUEBA
{'='*50}

   • Nombre:         {colaborador.nombres}
   • Cédula:         {colaborador.cedula}
   • Cargo:          {colaborador.cargo}
   • Empresa:        {colaborador.get_empresa_display()}
   • Jefe Inmediato: {colaborador.jefe_inmediato}
   • Celular:        {colaborador.celular}
   • Fecha Ingreso:  {colaborador.fecha_ingreso.strftime('%d/%m/%Y')}

   • Tipo:           Evaluación de {dias_evaluacion} días
   • Días restantes: {dias_restantes} días

{'='*50}
        """.strip()

        try:
            from django.core.mail import send_mail
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[CORREO_CRISTIAN],
                fail_silently=False,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error enviando correo para {colaborador.nombres}: {e}'))