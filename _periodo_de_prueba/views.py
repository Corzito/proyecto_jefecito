import openpyxl
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.http import require_GET
from .models import Colaborador
from .forms import ColaboradorForm


def lista_colaboradores(request):
    colaboradores = Colaborador.objects.all()
    hoy = timezone.now().date()
    data = []
    alertas_pendientes = 0

    for col in colaboradores:
        dias = (hoy - col.fecha_ingreso).days
        estado = col.estado_periodo()
        if estado in ('alerta_30', 'alerta_50'):
            alertas_pendientes += 1
        data.append({
            'obj': col,
            'dias': dias,
            'estado': estado,
            'dias_para_30': max(0, 30 - dias),
            'dias_para_50': max(0, 50 - dias),
        })

    return render(request, '_periodo_de_prueba/lista.html', {
        'colaboradores': data,
        'alertas_pendientes': alertas_pendientes,
        'hoy': hoy,
    })


def agregar_colaborador(request):
    if request.method == 'POST':
        form = ColaboradorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Colaborador registrado correctamente.')
            return redirect('periodo:lista')
    else:
        form = ColaboradorForm()
    return render(request, '_periodo_de_prueba/form.html', {'form': form, 'titulo': 'Registrar Colaborador'})


def editar_colaborador(request, pk):
    colaborador = get_object_or_404(Colaborador, pk=pk)
    if request.method == 'POST':
        form = ColaboradorForm(request.POST, instance=colaborador)
        if form.is_valid():
            form.save()
            messages.success(request, 'Colaborador actualizado.')
            return redirect('periodo:lista')
    else:
        form = ColaboradorForm(instance=colaborador)
    return render(request, '_periodo_de_prueba/form.html', {'form': form, 'titulo': 'Editar Colaborador'})


def eliminar_colaborador(request, pk):
    colaborador = get_object_or_404(Colaborador, pk=pk)
    if request.method == 'POST':
        colaborador.delete()
        messages.success(request, 'Colaborador eliminado.')
        return redirect('periodo:lista')
    return render(request, '_periodo_de_prueba/confirmar_eliminar.html', {'colaborador': colaborador})


def marcar_evaluacion(request, pk, tipo):
    colaborador = get_object_or_404(Colaborador, pk=pk)
    if tipo == '30':
        colaborador.evaluacion_30_completada = True
    elif tipo == '50':
        colaborador.evaluacion_50_completada = True
    colaborador.save()
    messages.success(request, f'Evaluación de {tipo} días marcada como completada.')
    return redirect('periodo:lista')


@require_GET
def enviar_alerta_jefe(request, pk):
    colaborador = get_object_or_404(Colaborador, pk=pk)

    if colaborador.alerta_jefe_enviada:
        return render(request, '_periodo_de_prueba/alerta_jefe_confirmacion.html', {
            'colaborador': colaborador,
            'ya_enviada': True,
        })

    if not colaborador.correo_jefe:
        return render(request, '_periodo_de_prueba/alerta_jefe_confirmacion.html', {
            'colaborador': colaborador,
            'sin_correo': True,
        })

    asunto = (
        f'⚠️ EVALUACIÓN PERIODO DE PRUEBA - {colaborador.nombres} '
        f'| Evaluación 30 días próximamente'
    )
    mensaje_html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #E32822; padding: 20px; text-align: center;">
        <h2 style="color: white; margin: 0;">⚠️ EVALUACIÓN PERIODO DE PRUEBA</h2>
    </div>
    <div style="padding: 20px; background-color: #f9f9f9;">
        <p>Estimado/a <strong>{colaborador.jefe_inmediato}</strong>,</p>
        <p>Le informamos que el siguiente colaborador a su cargo requiere evaluación de seguimiento:</p>
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
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Celular</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.celular}</td>
            </tr>
            <tr style="background:#f2f2f2;">
                <td style="padding:8px; border:1px solid #ddd; font-weight:bold;">Fecha Ingreso</td>
                <td style="padding:8px; border:1px solid #ddd;">{colaborador.fecha_ingreso.strftime('%d/%m/%Y')}</td>
            </tr>
        </table>
        <p>Por favor coordinar y realizar la evaluación de 30 días en los próximos 7 días.</p>
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
            body=f"Evaluación pendiente para {colaborador.nombres}. Abra en HTML para ver el detalle.",
            from_email=settings.EMAIL_HOST_USER,
            to=[colaborador.correo_jefe],
        )
        email.attach_alternative(mensaje_html, "text/html")
        email.send(fail_silently=False)
        colaborador.alerta_jefe_enviada = True
        colaborador.save(update_fields=['alerta_jefe_enviada'])
        enviado = True
    except Exception:
        enviado = False

    return render(request, '_periodo_de_prueba/alerta_jefe_confirmacion.html', {
        'colaborador': colaborador,
        'enviado': enviado,
    })


def importar_excel(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_excel')
        if not archivo:
            messages.error(request, 'Selecciona un archivo Excel.')
            return redirect('periodo:importar')
        if not archivo.name.endswith('.xlsx'):
            messages.error(request, 'El archivo debe ser .xlsx')
            return redirect('periodo:importar')
        try:
            wb = openpyxl.load_workbook(archivo)
            ws = wb['COLABORADORES']
        except Exception:
            messages.error(request, 'No se pudo leer el archivo. Asegúrate de usar la plantilla original.')
            return redirect('periodo:importar')

        exitosos = 0
        errores = []
        duplicados = 0

        for fila_num, row in enumerate(ws.iter_rows(min_row=5, values_only=True), start=5):
            if not row[1]:
                continue
            try:
                cedula    = str(row[1]).strip().replace('.', '').replace(',', '').split('.')[0]
                nombres   = str(row[2]).strip().upper() if row[2] else ''
                cargo     = str(row[3]).strip().upper() if row[3] else ''
                jefe      = str(row[4]).strip().upper() if row[4] else ''
                fecha_raw = row[7]
                celular   = str(row[6]).strip() if row[6] else ''
                empresa_raw = str(row[5]).strip().upper() if row[5] else ''
                empresa = (empresa_raw
                           .replace(' S.A.S.', '').replace(' S.A.S', '')
                           .replace(' SAS', '').strip())

                if not all([cedula, nombres, cargo, jefe, empresa, celular, fecha_raw]):
                    errores.append(f'Fila {fila_num}: campos incompletos.')
                    continue

                if empresa not in ['CARBOINSA', 'INCARSA', 'UNIMINAS', 'MILPA']:
                    errores.append(f'Fila {fila_num}: empresa "{empresa_raw}" no válida.')
                    continue

                if isinstance(fecha_raw, datetime):
                    fecha_ingreso = fecha_raw.date()
                elif isinstance(fecha_raw, str):
                    fecha_ingreso = None
                    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y'):
                        try:
                            fecha_ingreso = datetime.strptime(fecha_raw.strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                    if not fecha_ingreso:
                        errores.append(f'Fila {fila_num}: fecha "{fecha_raw}" no válida.')
                        continue
                else:
                    errores.append(f'Fila {fila_num}: formato de fecha no reconocido.')
                    continue

                if Colaborador.objects.filter(cedula=cedula).exists():
                    duplicados += 1
                    continue

                Colaborador.objects.create(
                    cedula=cedula,
                    nombres=nombres,
                    cargo=cargo,
                    jefe_inmediato=jefe,
                    empresa=empresa,
                    celular=celular,
                    fecha_ingreso=fecha_ingreso,
                )
                exitosos += 1

            except Exception as e:
                errores.append(f'Fila {fila_num}: error inesperado ({str(e)}).')

        if exitosos:
            messages.success(request, f'✅ {exitosos} colaborador(es) importado(s) correctamente.')
        if duplicados:
            messages.warning(request, f'⚠️ {duplicados} registro(s) omitido(s) por cédula duplicada.')
        for err in errores:
            messages.error(request, err)
        if not exitosos and not duplicados:
            messages.error(request, 'No se importó ningún registro. Revisa el archivo.')

        return redirect('periodo:lista')

    return render(request, '_periodo_de_prueba/importar.html')


def descargar_plantilla(request):
    import os
    from django.http import FileResponse, Http404
    ruta = os.path.join(settings.BASE_DIR, 'static', 'plantilla_colaboradores.xlsx')
    if not os.path.exists(ruta):
        raise Http404("Plantilla no encontrada.")
    return FileResponse(open(ruta, 'rb'), as_attachment=True, filename='plantilla_colaboradores.xlsx')