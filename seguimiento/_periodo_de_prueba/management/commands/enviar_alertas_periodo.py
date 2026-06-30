"""
Comando: python manage.py enviar_alertas_periodo

Ejecutar diariamente con Celery Beat o cron.
Envía correo HTML con tabla de colaboradores que requieren evaluación.
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from _periodo_de_prueba.models import Colaborador


CORREO_RRHH = 'cristian.barrera@incarsa.com.co'


class Command(BaseCommand):
    help = 'Envía alertas por correo cuando faltan 7 días para evaluaciones de periodo de prueba'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        colaboradores = Colaborador.objects.all()

        alertas_30 = []
        alertas_50 = []

        for col in colaboradores:
            dias = (hoy - col.fecha_ingreso).days

            if dias >= 23 and not col.alerta_30_enviada:
                alertas_30.append(col)
                col.alerta_30_enviada = True
                col.save(update_fields=['alerta_30_enviada'])
                self.stdout.write(self.style.WARNING(
                    f'[ALERTA 30] {col.nombres} - {col.empresa}'
                ))

            if dias >= 43 and not col.alerta_50_enviada:
                alertas_50.append(col)
                col.alerta_50_enviada = True
                col.save(update_fields=['alerta_50_enviada'])
                self.stdout.write(self.style.WARNING(
                    f'[ALERTA 50] {col.nombres} - {col.empresa}'
                ))

        if alertas_30 or alertas_50:
            self._enviar_correo_agrupado(alertas_30, alertas_50, hoy)

        self.stdout.write(self.style.SUCCESS(
            f'Proceso completado. Alertas 30 días: {len(alertas_30)} | Alertas 50 días: {len(alertas_50)}'
        ))

    def _fila_tabla(self, col, color):
        return f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#333;">{col.nombres}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#555;">{col.cedula}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#555;">{col.cargo}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#555;">{col.jefe_inmediato}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#555;">{col.get_empresa_display()}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#555;">{col.celular}</td>
        </tr>"""

    def _seccion_tabla(self, colaboradores, titulo, color, descripcion):
        if not colaboradores:
            return ''

        filas = ''.join(self._fila_tabla(col, color) for col in colaboradores)
        cantidad = len(colaboradores)

        return f"""
        <div style="margin-bottom:32px;">
          <div style="background:{color};padding:12px 20px;border-radius:8px 8px 0 0;">
            <span style="color:#fff;font-size:15px;font-weight:bold;">&#9888; {titulo}</span>
            <span style="margin-left:12px;background:rgba(255,255,255,0.25);color:#fff;
                         padding:2px 10px;border-radius:10px;font-size:12px;">
              {cantidad} colaborador{'es' if cantidad > 1 else ''}
            </span>
          </div>
          <p style="margin:0;padding:10px 20px;background:#fffaf9;font-size:12px;color:#666;
                    border-left:3px solid {color};border-right:3px solid {color};">{descripcion}</p>
          <div style="overflow-x:auto;border:1px solid #eee;border-top:none;border-radius:0 0 8px 8px;">
            <table style="width:100%;border-collapse:collapse;background:#fff;">
              <thead>
                <tr style="background:#f8f9fa;">
                  <th style="padding:10px 14px;text-align:left;font-size:11px;color:#888;text-transform:uppercase;border-bottom:2px solid #eee;">Nombres</th>
                  <th style="padding:10px 14px;text-align:left;font-size:11px;color:#888;text-transform:uppercase;border-bottom:2px solid #eee;">Cédula</th>
                  <th style="padding:10px 14px;text-align:left;font-size:11px;color:#888;text-transform:uppercase;border-bottom:2px solid #eee;">Cargo</th>
                  <th style="padding:10px 14px;text-align:left;font-size:11px;color:#888;text-transform:uppercase;border-bottom:2px solid #eee;">Jefe Inmediato</th>
                  <th style="padding:10px 14px;text-align:left;font-size:11px;color:#888;text-transform:uppercase;border-bottom:2px solid #eee;">Empresa</th>
                  <th style="padding:10px 14px;text-align:left;font-size:11px;color:#888;text-transform:uppercase;border-bottom:2px solid #eee;">Celular</th>
                </tr>
              </thead>
              <tbody>{filas}</tbody>
            </table>
          </div>
        </div>"""

    def _enviar_correo_agrupado(self, alertas_30, alertas_50, hoy):
        import locale
        total = len(alertas_30) + len(alertas_50)
        fecha_str = hoy.strftime('%d/%m/%Y')

        seccion_30 = self._seccion_tabla(
            alertas_30,
            'Evaluación 30 días — Faltan 7 días',
            '#E32822',
            'Los siguientes colaboradores deben ser evaluados dentro de 7 días (cumplirán 30 días en la empresa).'
        )
        seccion_50 = self._seccion_tabla(
            alertas_50,
            'Evaluación 50 días — Faltan 7 días',
            '#e67e22',
            'Los siguientes colaboradores deben ser evaluados dentro de 7 días (cumplirán 50 días en la empresa).'
        )

        html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
  <tr><td align="center">
    <table width="680" cellpadding="0" cellspacing="0" style="max-width:680px;width:100%;">

      <!-- HEADER -->
      <tr>
        <td style="background:#E32822;padding:28px 32px;border-radius:10px 10px 0 0;text-align:center;">
          <p style="margin:0;color:rgba(255,255,255,0.8);font-size:11px;text-transform:uppercase;letter-spacing:2px;">
            Sistema de Seguimiento
          </p>
          <h1 style="margin:8px 0 0;color:#fff;font-size:22px;font-weight:700;">
            &#9888; Alerta Periodo de Prueba
          </h1>
          <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">{fecha_str}</p>
        </td>
      </tr>

      <!-- RESUMEN -->
      <tr>
        <td style="background:#fff;padding:24px 32px;border-left:1px solid #eee;border-right:1px solid #eee;">
          <p style="margin:0 0 20px;font-size:14px;color:#444;line-height:1.6;">
            Se han identificado <strong style="color:#E32822;">{total} colaborador{'es' if total > 1 else ''}</strong>
            que requieren periodo de prueba próximamente.
            Por favor coordinar con los jefes inmediatos para programar las evaluaciones.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="48%" style="background:#fff5f5;border:1px solid #fdd;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#E32822;">{len(alertas_30)}</div>
                <div style="font-size:12px;color:#888;margin-top:4px;">Evaluación 30 días</div>
              </td>
              <td width="4%"></td>
              <td width="48%" style="background:#fff8f0;border:1px solid #fde;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#e67e22;">{len(alertas_50)}</div>
                <div style="font-size:12px;color:#888;margin-top:4px;">Evaluación 50 días</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- TABLAS -->
      <tr>
        <td style="background:#fff;padding:8px 32px 28px;border-left:1px solid #eee;border-right:1px solid #eee;">
          {seccion_30}
          {seccion_50}
        </td>
      </tr>

      <!-- FOOTER -->
      <tr>
        <td style="background:#2c2c2c;padding:18px 32px;border-radius:0 0 10px 10px;text-align:center;">
          <p style="margin:0;color:#aaa;font-size:11px;">
            Sistema de Seguimiento — Periodo de Prueba &nbsp;|&nbsp;
            CARBOINSA &bull; INCARSA &bull; UNIMINAS &bull; MILPA
          </p>
          <p style="margin:6px 0 0;color:#666;font-size:10px;">
            Correo automático — por favor no responder.
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

        asunto = f'⚠️ Alerta Periodo de Prueba — {total} colaborador{"es" if total > 1 else ""} | {fecha_str}'

        texto_plano = f'Alerta Periodo de Prueba - {fecha_str}\n\n'
        if alertas_30:
            texto_plano += f'EVALUACIÓN 30 DÍAS ({len(alertas_30)} colaboradores):\n'
            for col in alertas_30:
                texto_plano += f'  - {col.nombres} | {col.cedula} | {col.cargo} | {col.empresa}\n'
        if alertas_50:
            texto_plano += f'\nEVALUACIÓN 50 DÍAS ({len(alertas_50)} colaboradores):\n'
            for col in alertas_50:
                texto_plano += f'  - {col.nombres} | {col.cedula} | {col.cargo} | {col.empresa}\n'

        try:
            email = EmailMultiAlternatives(
                subject=asunto,
                body=texto_plano,
                from_email=settings.EMAIL_HOST_USER,
                to=[CORREO_RRHH],
            )
            email.attach_alternative(html, "text/html")
            email.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS('Correo HTML enviado correctamente.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error enviando correo: {e}'))