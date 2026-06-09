from django.db import models

EMPRESA_CHOICES = [
    ('CARBOINSA', 'CARBOINSA S.A.S.'),
    ('INCARSA', 'INCARSA S.A.S.'),
    ('UNIMINAS', 'UNIMINAS'),
    ('MILPA', 'MILPA S.A.S.'),
]

RESULTADO_CHOICES = [
    ('pendiente',    'Pendiente'),
    ('aprobado',     'Aprobó'),
    ('no_aprobado',  'No Aprobó'),
]


class Colaborador(models.Model):
    cedula         = models.CharField(max_length=20, unique=True, verbose_name='Cédula No')
    nombres        = models.CharField(max_length=200, verbose_name='Nombres')
    cargo          = models.CharField(max_length=200, verbose_name='Cargo')
    jefe_inmediato = models.CharField(max_length=200, verbose_name='Jefe Inmediato')
    correo_jefe    = models.EmailField(blank=True, null=True, verbose_name='Correo Jefe Inmediato')
    empresa        = models.CharField(max_length=20, choices=EMPRESA_CHOICES, verbose_name='Empresa')
    celular        = models.CharField(max_length=20, verbose_name='No Celular')
    fecha_ingreso  = models.DateField(verbose_name='Fecha de Ingreso')

    alerta_30_enviada   = models.BooleanField(default=False, verbose_name='Alerta 30 días enviada')
    alerta_50_enviada   = models.BooleanField(default=False, verbose_name='Alerta 50 días enviada')
    alerta_jefe_enviada = models.BooleanField(default=False, verbose_name='Alerta jefe enviada')

    evaluacion_30_completada = models.BooleanField(default=False, verbose_name='Evaluación 30 días completada')
    evaluacion_50_completada = models.BooleanField(default=False, verbose_name='Evaluación 50 días completada')

    resultado_periodo = models.CharField(
        max_length=20,
        choices=RESULTADO_CHOICES,
        default='pendiente',
        verbose_name='Resultado Periodo de Prueba'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Colaborador'
        verbose_name_plural = 'Colaboradores'
        ordering            = ['fecha_ingreso', 'nombres']

    def __str__(self):
        return f"{self.nombres} - {self.cedula}"

    def dias_en_empresa(self):
        from django.utils import timezone
        return (timezone.now().date() - self.fecha_ingreso).days

    def estado_periodo(self):
        dias  = self.dias_en_empresa()
        e30   = self.evaluacion_30_completada
        e50   = self.evaluacion_50_completada
        res   = self.resultado_periodo

        # ── Antes de los 23 días ──────────────────────────────────────────
        if dias < 23:
            return 'activo'

        # ── Zona de alerta 30 (23-29 días) ───────────────────────────────
        if dias < 30:
            return 'alerta_30'

        # ── Entre 30 y 49 días ────────────────────────────────────────────
        if dias < 50:
            if dias < 43:
                # Primer periodo cumplido
                if not e30:
                    return 'pendiente_eval_30'
                return 'en_seguimiento'
            else:
                # Zona de alerta 50 (43-49 días)
                if not e50:
                    return 'alerta_50'
                return 'en_seguimiento'

        # ── 50 días o más ─────────────────────────────────────────────────
        if not e30 and not e50:
            return 'pendiente_eval_30_y_50'

        if e30 and not e50:
            return 'pendiente_eval_50'

        if not e30 and e50:
            return 'pendiente_eval_30'

        # Ambas evaluaciones completadas
        if res == 'aprobado':
            return 'completado_aprobado'
        if res == 'no_aprobado':
            return 'completado_no_aprobado'
        return 'pendiente_resultado'

    def estado_display(self):
        """Etiqueta legible del estado para usar en templates y Excel."""
        return {
            'activo':               'Activo',
            'alerta_30':            '⚠️ Alerta — Evaluar 30 días',
            'pendiente_eval_30':    '🔴 Pendiente evaluación 30 días',
            'en_seguimiento':       '🔵 En seguimiento',
            'alerta_50':            '⚠️ Alerta — Evaluar 50 días',
            'pendiente_eval_30_y_50': '🔴 Pendiente eval. 30 y 50 días',
            'pendiente_eval_50':    '🟡 Pendiente evaluación 50 días',
            'pendiente_resultado':  '🟡 Evaluaciones completas — Resultado pendiente',
            'completado_aprobado':  '✅ Completado — Aprobó',
            'completado_no_aprobado': '❌ Completado — No aprobó',
        }.get(self.estado_periodo(), self.estado_periodo())

    def periodo_actual(self):
        dias = self.dias_en_empresa()
        if dias < 30:
            return 'primer_periodo'
        elif dias < 50:
            return 'segundo_periodo'
        return 'completado'