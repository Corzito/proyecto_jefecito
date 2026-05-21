from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from _periodo_de_prueba.models import Colaborador

CORREO_CRISTIAN = 'cristian.barrera@incarsa.com.co'
BASE_URL = 'https://proyecto-jefecito.onrender.com'


class Command(BaseCommand):
    help = 'Envía alertas agrupadas por correo cuando faltan 7 días para evaluaciones'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        colaboradores = Colaborador.objects.all()

        alerta_30 = []
        alerta_50 = []

        for col in colaboradores:
            dias = (hoy - col.fecha_ingreso).days

            if dias == 23 and not col.alerta_30_enviada:
                alerta_30.append(col)
                col.alerta_30_enviada = True
                col.save(update_fields=['alerta_30_enviada'])
                self.stdout.write(self.style.WARNING(
                    f'[ALERTA 30] {col.nombres} - {col.empresa}'
                ))

            if dias == 43 and not col.alerta_50_enviada:
                alerta_50.append(col)
                col.alerta_50_enviada = True
                col.save(update_fields=['alerta_50_enviada'])
                self.stdout.write(self.style.WARNING(
                    f'[ALERTA 50] {col.nombres} - {col.empresa}'
                ))

        if alerta_30 or alerta_50:
            self._enviar_correo_agrupado(alerta_30, alerta_50)

        self.stdout.write(self.style.SUCCESS(
            f'Proceso completado. Alertas 30 días: {len(alerta_30)} | Alertas 50 días: {len(alerta_50)}'
        ))

    def _build_tabla(self, colaboradores):
        filas = ''
        for i, col in enumerate(colaboradores):
            bg = '#ffffff' if i % 2 == 0 else '#f2f2f2'
            filas += f"""
            <tr style="background:{bg};">
                <td style="padding:8px; border:1px solid #ddd;">{col.nombres}</td>
                <td style="padding:8px; border:1px solid #ddd;">{col.cedula}</td>
                <td style="padding:8px; border:1px solid #ddd;">{col.cargo}</td>
                <td style="padding:8px; border:1px solid #ddd;">{col.get_empresa_display()}</td>
                <td style="padding:8px; border:1px solid #ddd;">{col.jefe_inmediato}</td>
                <td style="padding:8px; border:1px solid #ddd;">{col.fecha_ingreso.strftime('%d/%m/%Y')}</td>
                <td style="padding:8px; border:1px solid #ddd;">{col.dias_en_empresa()} días</td>
            </tr>
            """
        return f"""
        <table style="width:100%; border-collapse:collapse; margin:15px 0;">
            <thead>
                <tr style="background:#E32822; color:white;">
                    <th style="padding:8px; border:1px solid #ddd;">Nombre</th>
                    <th style="padding:8px; border:1px solid #ddd;">Cédula</th>
                    <th style="padding:8px; border:1px solid #ddd;">Cargo</th>
                    <th style="padding:8px; border:1px solid #ddd;">Empresa</th>
                    <th style="padding:8px; border:1px solid #ddd;">Jefe Inmediato</th>
                    <th style="padding:8px; border:1px solid #ddd;">F. Ingreso</th>
                    <th style="padding:8px; border:1px solid #ddd;">Días</th>
                </tr>
            </thead>
            <tbody>{filas}</tbody>
        </table>
        """

    def _enviar_correo_agrupado(self, alerta_30, alerta_50):
        seccion_30 = ''
        if alerta_30:
            seccion_30 = f"""
            <div style="margin-bottom:30px;">
                <h3 style="color:#E32822; border-bottom:2px solid #E32822; padding-bottom:5px;">
                    ⚠️ Evaluación de 30 días — {len(alerta_30)} colaborador(es)
                </h3>
                <p>Faltan 7 días para la evaluación de 30 días de los siguientes colaboradores:</p>
                {self._build_tabla(alerta_30)}
            </div>
            """

        seccion_50 = ''
        if alerta_50:
            seccion_50 = f"""
            <div style="margin-bottom:30px;">
                <h3 style="color:#e6a817; border-bottom:2px solid #e6a817; padding-bottom:5px;">
                    ⚠️ Evaluación de 50 días — {len(alerta_50)} colaborador(es)
                </h3>
                <p>Faltan 7 días para la evaluación de 50 días de los siguientes colaboradores:</p>
                {self._build_tabla(alerta_50)}
            </div>
            """

        asunto = f'⚠️ ALERTAS PERIODO DE PRUEBA — {len(alerta_30)} alerta(s) 30d | {len(alerta_50)} alerta(s) 50d'

        mensaje_html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif; max-width:800px; margin:0 auto;">
    <div style="background-color:#E32822; padding:20px; text-align:center;">
        <h2 style="color:white; margin:0;">⚠️ ALERTAS PERIODO DE PRUEBA</h2>
        <p style="color:rgba(255,255,255,0.9); margin:5px 0 0 0;">
            {timezone.now().strftime('%d/%m/%Y')}
        </p>
    </div>
    <div style="padding:25px; background-color:#f9f9f9;">
        {seccion_30}
        {seccion_50}
        <p style="color:#666; font-size:12px; text-align:center;">
            Por favor coordinar con los jefes inmediatos para programar las evaluaciones.
        </p>
    </div>
    <div style="background-color:#333; padding:10px; text-align:center;">
        <p style="color:#aaa; font-size:11px; margin:0;">
            Sistema de Seguimiento - Periodo de Prueba
        </p>
    </div>
</body>
</html>
        """.strip()

        try:
            email = EmailMultiAlternatives(
                subject=asunto,
                body="Alertas periodo de prueba. Abra en HTML para ver el detalle.",
                from_email=settings.EMAIL_HOST_USER,
                to=[CORREO_CRISTIAN],
            )
            email.attach_alternative(mensaje_html, "text/html")
            email.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS('Correo agrupado enviado a Cristian.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error enviando correo: {e}'))