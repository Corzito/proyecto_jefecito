# test_alerta.py
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from _periodo_de_prueba.models import Colaborador, JefeInmediato
from datetime import date, timedelta

print("=" * 50)
print("TEST ENVÍO DE ALERTAS - PERIODO DE PRUEBA")
print("=" * 50)

CORREO_RRHH = 'cristian.barrera@incarsa.com.co'

# 1. Crear jefe de prueba
jefe, _ = JefeInmediato.objects.get_or_create(
    nombre='JEFE TEST TEMPORAL',
    defaults={'correo': CORREO_RRHH}
)
print(f"✅ Jefe creado/encontrado: {jefe.nombre}")

# 2. Crear colaborador con 23 días de antigüedad (trigger alerta 30)
fecha_ingreso_test = date.today() - timedelta(days=23)

col, creado = Colaborador.objects.get_or_create(
    cedula='0000000000',
    defaults={
        'nombres': 'COLABORADOR TEST',
        'cargo': 'CARGO TEST',
        'jefe_inmediato': jefe,
        'empresa': 'INCARSA',
        'celular': '3000000000',
        'fecha_ingreso': fecha_ingreso_test,
        'alerta_30_enviada': False,
    }
)

if not creado:
    # Si ya existía, resetear para que el comando lo procese
    col.fecha_ingreso = fecha_ingreso_test
    col.alerta_30_enviada = False
    col.save()

print(f"✅ Colaborador: {col.nombres} | Fecha ingreso: {col.fecha_ingreso} | Días: {(date.today() - col.fecha_ingreso).days}")

# 3. Probar envío directo del correo
print("\n📧 Enviando correo de prueba...")
asunto = f'⚠️ [TEST] ALERTA PERIODO DE PRUEBA - {col.nombres} | Evaluación 30 días en 7 días'
mensaje = f"""
SISTEMA DE SEGUIMIENTO - PERIODO DE PRUEBA (TEST)
{'='*50}

📋 DATOS DEL COLABORADOR:
   • Nombre:         {col.nombres}
   • Cédula:         {col.cedula}
   • Cargo:          {col.cargo}
   • Empresa:        {col.get_empresa_display()}
   • Jefe Inmediato: {col.jefe_inmediato}
   • Celular:        {col.celular}
   • Fecha Ingreso:  {col.fecha_ingreso.strftime('%d/%m/%Y')}

⏰ EVALUACIÓN PENDIENTE:
   • Tipo:           Evaluación de 30 días
   • Días restantes: 7 días para realizar la evaluación

{'='*50}
Este es un correo de PRUEBA generado manualmente.
""".strip()

try:
    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[CORREO_RRHH],
        fail_silently=False,
    )
    print(f"✅ Correo enviado correctamente a {CORREO_RRHH}")
except Exception as e:
    print(f"❌ Error al enviar correo: {e}")

# 4. Correr el comando real
print("\n🔄 Ejecutando comando enviar_alertas_periodo...")
from django.core.management import call_command
call_command('enviar_alertas_periodo')

# 5. Limpiar datos de prueba
col.delete()
jefe.delete()
print("\n🧹 Datos de prueba eliminados.")
print("=" * 50)
print("TEST FINALIZADO")
print("=" * 50)