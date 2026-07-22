import io
import os
from datetime import datetime
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def generar_pdf_solicitud(solicitud):
    """
    Genera un informe técnico en formato PDF para una solicitud resuelta.
    Retorna un buffer BytesIO con el contenido del PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E1B4B'),
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=TA_LEFT
    )

    header_right_style = ParagraphStyle(
        'HeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#4338CA'),
        alignment=TA_RIGHT
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E1B4B'),
        spaceBefore=8,
        spaceAfter=4
    )

    label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    value_style = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )

    body_text = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        alignment=TA_JUSTIFY
    )

    elements = []

    # --- ENCABEZADO ---
    header_left = [
        Paragraph("SAST — Servicio Técnico", title_style),
        Paragraph("Sistema de Agendamiento de Servicio Técnico", subtitle_style)
    ]
    fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    header_right = [
        Paragraph("INFORME TÉCNICO DE SERVICIO", header_right_style),
        Paragraph(f"Solicitud #{solicitud.id_solicitud}", ParagraphStyle('HRightSub', parent=header_right_style, fontSize=10, textColor=colors.HexColor('#6366F1'))),
        Paragraph(f"Fecha emisión: {fecha_str}", ParagraphStyle('HRightDate', parent=subtitle_style, alignment=TA_RIGHT, fontSize=8))
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[320, 220]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#6366F1'), spaceBefore=4, spaceAfter=12))

    # --- RESUMEN GENERAL Y ESTADO ---
    elements.append(Paragraph("1. Información General de la Solicitud", section_heading))

    fecha_creacion_str = solicitud.fecha_creacion.strftime('%d/%m/%Y %H:%M') if solicitud.fecha_creacion else '—'
    fecha_atencion_str = solicitud.fecha_atencion.strftime('%d/%m/%Y') if solicitud.fecha_atencion else '—'
    horario_str = solicitud.horario_solicitado or '—'
    tipo_soporte_str = solicitud.tipo_soporte.nombre_soporte if solicitud.tipo_soporte else '—'
    estado_str = solicitud.estado.nombre_estado if solicitud.estado else '—'

    info_gen_data = [
        [
            Paragraph("<b>N° Solicitud:</b>", label_style), Paragraph(f"#{solicitud.id_solicitud}", value_style),
            Paragraph("<b>Tipo de Servicio:</b>", label_style), Paragraph(tipo_soporte_str, value_style)
        ],
        [
            Paragraph("<b>Fecha Registro:</b>", label_style), Paragraph(fecha_creacion_str, value_style),
            Paragraph("<b>Estado Ticket:</b>", label_style), Paragraph(f"<font color='#059669'><b>{estado_str.upper()}</b></font>", value_style)
        ],
        [
            Paragraph("<b>Fecha Atención:</b>", label_style), Paragraph(fecha_atencion_str, value_style),
            Paragraph("<b>Horario Solicitado:</b>", label_style), Paragraph(horario_str, value_style)
        ]
    ]

    t_info_gen = Table(info_gen_data, colWidths=[100, 170, 100, 170])
    t_info_gen.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F1F5F9')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_info_gen)
    elements.append(Spacer(1, 10))

    # --- CLIENTE Y TÉCNICO ---
    elements.append(Paragraph("2. Participantes del Servicio", section_heading))

    cliente_nombre = solicitud.cliente.nombre_completo if solicitud.cliente else '—'
    cliente_cedula = solicitud.cliente.ncedula if solicitud.cliente else '—'
    cliente_correo = solicitud.cliente.correo if solicitud.cliente else '—'
    cliente_telf = solicitud.cliente.numero_telefono if solicitud.cliente else '—'
    cliente_sector = solicitud.cliente.sector if solicitud.cliente else '—'

    tecnico_nombre = solicitud.tecnico.nombre_completo if solicitud.tecnico else 'No asignado'
    tecnico_correo = solicitud.tecnico.correo if solicitud.tecnico else '—'
    tecnico_telf = solicitud.tecnico.numero_telefono if solicitud.tecnico else '—'
    tecnico_detalle_str = ''
    if solicitud.tecnico and hasattr(solicitud.tecnico, 'detalles_tecnico') and solicitud.tecnico.detalles_tecnico:
        carrera = solicitud.tecnico.detalles_tecnico.carrera or ''
        semestre = f"Semestre {solicitud.tecnico.detalles_tecnico.semestre}" if solicitud.tecnico.detalles_tecnico.semestre else ''
        tecnico_detalle_str = f"{carrera} ({semestre})".strip(' ()')

    participantes_data = [
        [
            Paragraph("<b>DATOS DEL CLIENTE</b>", ParagraphStyle('HeaderCol', parent=label_style, textColor=colors.HexColor('#4338CA'))),
            Paragraph("<b>DATOS DEL TÉCNICO</b>", ParagraphStyle('HeaderCol2', parent=label_style, textColor=colors.HexColor('#4338CA')))
        ],
        [
            Paragraph(f"<b>Nombre:</b> {cliente_nombre}<br/>"
                      f"<b>Cédula:</b> {cliente_cedula}<br/>"
                      f"<b>Correo:</b> {cliente_correo}<br/>"
                      f"<b>Teléfono:</b> {cliente_telf}<br/>"
                      f"<b>Sector:</b> {cliente_sector}", value_style),
            Paragraph(f"<b>Técnico:</b> {tecnico_nombre}<br/>"
                      f"<b>Correo:</b> {tecnico_correo}<br/>"
                      f"<b>Teléfono:</b> {tecnico_telf}" +
                      (f"<br/><b>Especialidad:</b> {tecnico_detalle_str}" if tecnico_detalle_str else ""), value_style)
        ]
    ]

    t_part = Table(participantes_data, colWidths=[270, 270])
    t_part.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEF2FF')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFFFFF')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_part)
    elements.append(Spacer(1, 10))

    # --- DESCRIPCIÓN DEL PROBLEMA ---
    elements.append(Paragraph("3. Detalle de la Solicitud y Requerimiento", section_heading))
    desc_p = Paragraph(solicitud.descripcion or 'Sin descripción proporcionada.', body_text)
    
    recursos_p = None
    if solicitud.recursos_adicionales:
        recursos_p = Paragraph(f"<b>Recursos adicionales:</b> {solicitud.recursos_adicionales}", value_style)

    prob_cell = [desc_p]
    if recursos_p:
        prob_cell.extend([Spacer(1, 4), recursos_p])

    t_prob = Table([[prob_cell]], colWidths=[540])
    t_prob.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(t_prob)
    elements.append(Spacer(1, 10))

    # --- REPORTE TÉCNICO / DIAGNÓSTICO ---
    elements.append(Paragraph("4. Informe Técnico y Trabajo Realizado", section_heading))
    
    if solicitud.reporte:
        rep = solicitud.reporte
        rep_fecha = rep.fecha_creacion.strftime('%d/%m/%Y %H:%M') if rep.fecha_creacion else '—'
        diag_p = Paragraph(rep.descripcion_trabajo or 'No se registró descripción del trabajo.', body_text)
        
        rep_content = [
            Paragraph(f"<b>Fecha de registro de informe:</b> {rep_fecha}", label_style),
            Spacer(1, 4),
            diag_p
        ]

        t_diag = Table([[rep_content]], colWidths=[540])
        t_diag.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDF4')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#BBF7D0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(t_diag)
        elements.append(Spacer(1, 10))

        # --- EVIDENCIA FOTOGRÁFICA ---
        img1_obj = None
        img2_obj = None

        static_folder = os.path.join(current_app.root_path, 'static')

        if rep.imagen_evidencia_1:
            full_path1 = os.path.join(static_folder, rep.imagen_evidencia_1.replace('/', os.sep))
            if os.path.exists(full_path1):
                try:
                    img1_obj = Image(full_path1, width=2.4*inch, height=1.8*inch)
                except Exception as e:
                    current_app.logger.error(f"Error cargando imagen 1 en PDF: {e}")

        if rep.imagen_evidencia_2:
            full_path2 = os.path.join(static_folder, rep.imagen_evidencia_2.replace('/', os.sep))
            if os.path.exists(full_path2):
                try:
                    img2_obj = Image(full_path2, width=2.4*inch, height=1.8*inch)
                except Exception as e:
                    current_app.logger.error(f"Error cargando imagen 2 en PDF: {e}")

        if img1_obj or img2_obj:
            elements.append(Paragraph("5. Evidencia Fotográfica del Servicio", section_heading))
            
            cell_1 = [Paragraph("<b>Estado Inicial (Recepción)</b>", label_style), Spacer(1, 4)]
            if img1_obj:
                cell_1.append(img1_obj)
            else:
                cell_1.append(Paragraph("<i>Imagen no disponible</i>", value_style))

            cell_2 = [Paragraph("<b>Estado Final (Entrega)</b>", label_style), Spacer(1, 4)]
            if img2_obj:
                cell_2.append(img2_obj)
            else:
                cell_2.append(Paragraph("<i>Imagen no disponible</i>", value_style))

            t_imgs = Table([[cell_1, cell_2]], colWidths=[270, 270])
            t_imgs.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F1F5F9')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            elements.append(t_imgs)
            elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph("<i>Sin informe registrado aún.</i>", value_style))
        elements.append(Spacer(1, 10))

    # --- CALIFICACIÓN DEL CLIENTE ---
    if solicitud.calificacion:
        elements.append(Paragraph("6. Conformidad y Calificación del Cliente", section_heading))
        cal = solicitud.calificacion
        stars_str = "★" * cal.puntuacion + "☆" * (5 - cal.puntuacion)
        comentario_str = cal.comentario or 'Sin comentarios adicionales.'

        cal_content = [
            Paragraph(f"<b>Puntuación:</b> <font color='#D97706'><b>{stars_str} ({cal.puntuacion}/5)</b></font>", value_style),
            Spacer(1, 4),
            Paragraph(f"<b>Comentario del cliente:</b> <i>\"{comentario_str}\"</i>", value_style)
        ]

        t_cal = Table([[cal_content]], colWidths=[540])
        t_cal.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF3C7')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#FDE68A')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(t_cal)
        elements.append(Spacer(1, 15))

    # --- PIE DE PÁGINA / FIRMAS ---
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceBefore=10, spaceAfter=15))
    
    firmas_data = [
        [
            Paragraph("_____________________________<br/><b>Firma / Conformidad del Cliente</b>", ParagraphStyle('Firma1', parent=value_style, alignment=TA_CENTER)),
            Paragraph("_____________________________<br/><b>Firma / Técnico Responsable</b>", ParagraphStyle('Firma2', parent=value_style, alignment=TA_CENTER))
        ]
    ]
    t_firmas = Table(firmas_data, colWidths=[270, 270])
    t_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(KeepTogether([t_firmas]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
