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
    import io
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Colaboradores"

    rojo       = "E32822"
    blanco     = "FFFFFF"
    gris_claro = "F2F2F2"

    header_font  = Font(bold=True, color=blanco, size=11)
    header_fill  = PatternFill("solid", fgColor=rojo)
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border  = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"),  bottom=Side(style="thin"),
    )
    data_align = Alignment(horizontal="left", vertical="center")

    columnas = [
        ("Cédula No",                   20),
        ("Nombres Completos",            35),
        ("Cargo",                        35),
        ("Jefe Inmediato",               28),
        ("Correo Jefe (opcional)",       30),
        ("Empresa",                      18),
        ("No Celular",                   18),
        ("Fecha Ingreso (AAAA-MM-DD)",   26),
    ]

    for col_idx, (label, width) in enumerate(columnas, start=1):
        cell = ws.cell(row=1, column=col_idx, value=label)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = header_align
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.row_dimensions[1].height = 32

    data_fill_par   = PatternFill("solid", fgColor=gris_claro)
    data_fill_impar = PatternFill("solid", fgColor=blanco)

    for row in range(2, 52):
        fill = data_fill_par if row % 2 == 0 else data_fill_impar
        for col in range(1, len(columnas) + 1):
            cell = ws.cell(row=row, column=col, value=None)
            cell.border    = thin_border
            cell.fill      = fill
            cell.alignment = data_align
        ws.row_dimensions[row].height = 18

    ws.freeze_panes = "A2"

    # Hoja instrucciones
    wi = wb.create_sheet("📋 Instrucciones")
    wi.column_dimensions["A"].width = 32
    wi.column_dimensions["B"].width = 55

    titulo_font = Font(bold=True, color=blanco, size=13)
    titulo_fill = PatternFill("solid", fgColor=rojo)
    ok_fill     = PatternFill("solid", fgColor="E2EFDA")
    ok_font     = Font(color="375623", size=10)

    wi.merge_cells("A1:B1")
    c = wi.cell(row=1, column=1, value="📋  INSTRUCCIONES DE DILIGENCIAMIENTO")
    c.font      = titulo_font
    c.fill      = titulo_fill
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border    = thin_border
    wi.row_dimensions[1].height = 30

    instrucciones = [
        ("Cédula No",                  "Número sin puntos ni espacios.",                          "1002368124"),
        ("Nombres Completos",          "Nombre y apellidos en mayúsculas.",                        "ALDO FLECHAS ALVAREZ"),
        ("Cargo",                      "Cargo o rol del colaborador.",                             "APRENDIZ SENA"),
        ("Jefe Inmediato",             "Nombre del jefe inmediato.",                               "ING. JAVIER MOJICA"),
        ("Correo Jefe (opcional)",     "Correo del jefe para notificaciones.",                     "javier.mojica@empresa.com"),
        ("Empresa",                    "CARBOINSA | INCARSA | UNIMINAS | MILPA",                   "INCARSA"),
        ("No Celular",                 "Sin espacios ni guiones.",                                 "3137774696"),
        ("Fecha Ingreso (AAAA-MM-DD)", "Formato AÑO-MES-DÍA.",                                    "2025-01-10"),
    ]

    fila_act = 2
    for campo, desc, ejemplo_val in instrucciones:
        c = wi.cell(row=fila_act, column=1, value=campo)
        c.font      = Font(size=10, bold=True)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        c.border    = thin_border
        wi.row_dimensions[fila_act].height = 36

        c = wi.cell(row=fila_act, column=2, value=desc)
        c.font      = Font(size=10)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        c.border    = thin_border

        fila_act += 1
        c = wi.cell(row=fila_act, column=1, value="Ejemplo →")
        c.font = ok_font; c.fill = ok_fill
        c.alignment = Alignment(horizontal="left", vertical="center")
        c.border = thin_border

        c = wi.cell(row=fila_act, column=2, value=ejemplo_val)
        c.font = ok_font; c.fill = ok_fill
        c.alignment = Alignment(horizontal="left", vertical="center")
        c.border = thin_border
        wi.row_dimensions[fila_act].height = 18
        fila_act += 1

    # Hoja empresas
    we = wb.create_sheet("Empresas válidas")
    we.column_dimensions["A"].width = 35
    c = we.cell(row=1, column=1, value="Valores aceptados en la columna EMPRESA")
    c.font      = Font(bold=True, color=blanco, size=11)
    c.fill      = PatternFill("solid", fgColor=rojo)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border    = thin_border
    we.row_dimensions[1].height = 28
    for i, emp in enumerate(["CARBOINSA", "INCARSA", "UNIMINAS", "MILPA"], start=2):
        c = we.cell(row=i, column=1, value=emp)
        c.font      = Font(size=11, bold=True)
        c.fill      = PatternFill("solid", fgColor="E2EFDA")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border    = thin_border
        we.row_dimensions[i].height = 22

    wb.active = ws
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="plantilla_colaboradores.xlsx"'
    return response