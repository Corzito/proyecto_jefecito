from django.db import models


EMPRESA_CHOICES = [
    ('CARBOINSA', 'CARBOINSA S.A.S.'),
    ('INCARSA', 'INCARSA S.A.S.'),
    ('UNIMINAS', 'UNIMINAS'),
    ('MILPA', 'MILPA S.A.S.'),
]


class Colaborador(models.Model):
    cedula = models.CharField(max_length=20, unique=True, verbose_name='Cédula No')
    nombres = models.CharField(max_length=200, verbose_name='Nombres')
    cargo = models.CharField(max_length=200, verbose_name='Cargo')
    jefe_inmediato = models.CharField(max_length=200, verbose_name='Jefe Inmediato')
    correo_jefe = models.EmailField(blank=True, null=True, verbose_name='Correo Jefe Inmediato')
    empresa = models.CharField(max_length=20, choices=EMPRESA_CHOICES, verbose_name='Empresa')
    celular = models.CharField(max_length=20, verbose_name='No Celular')
    fecha_ingreso = models.DateField(verbose_name='Fecha de Ingreso')

    alerta_30_enviada = models.BooleanField(default=False, verbose_name='Alerta 30 días enviada')
    alerta_50_enviada = models.BooleanField(default=False, verbose_name='Alerta 50 días enviada')
    alerta_jefe_enviada = models.BooleanField(default=False, verbose_name='Alerta jefe enviada')

    evaluacion_30_completada = models.BooleanField(default=False, verbose_name='Evaluación 30 días completada')
    evaluacion_50_completada = models.BooleanField(default=False, verbose_name='Evaluación 50 días completada')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'
        ordering = ['fecha_ingreso', 'nombres']

    def __str__(self):
        return f"{self.nombres} - {self.cedula}"

    def dias_en_empresa(self):
        from django.utils import timezone
        return (timezone.now().date() - self.fecha_ingreso).days

    def estado_periodo(self):
        dias = self.dias_en_empresa()
        if dias < 23:
            return 'activo'
        elif 23 <= dias < 30:
            return 'alerta_30'
        elif 30 <= dias < 43:
            return 'en_seguimiento'
        elif 43 <= dias < 50:
            return 'alerta_50'
        elif dias >= 50:
            return 'completado'
        return 'activo'