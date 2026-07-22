import io
import os
from datetime import datetime
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# ─── Paleta de colores institucional ───────────────────────────────────────────
AZUL_UTM    = colors.HexColor('#003087')   # Azul oscuro institucional
AZUL_CLARO  = colors.HexColor('#E8EEF7')   # Fondo cabeceras de tabla
VERDE_OK    = colors.HexColor('#1A7A4A')   # Estado resuelto
BORDE       = colors.HexColor('#B0BEC5')   # Gris neutro para bordes
FONDO_CELD  = colors.HexColor('#F5F7FA')   # Fondo alterno
NEGRO       = colors.HexColor('#1A1A2E')
GRIS_TEXT   = colors.HexColor('#455A64')


def _styles():
    """Devuelve un dict con todos los estilos del documento."""
    base = getSampleStyleSheet()

    def ps(name, **kw):
        kw.setdefault('fontName', 'Helvetica')
        kw.setdefault('fontSize', 9)
        kw.setdefault('leading', 13)
        kw.setdefault('textColor', NEGRO)
        return ParagraphStyle(name, parent=base['Normal'], **kw)

    return {
        'titulo_doc':   ps('TitDoc',   fontName='Helvetica-Bold', fontSize=13,
                           textColor=AZUL_UTM, alignment=TA_CENTER, spaceAfter=2),
        'subtitulo':    ps('SubTit',   fontSize=9, textColor=GRIS_TEXT,
                           alignment=TA_CENTER),
        'seccion':      ps('Sec',      fontName='Helvetica-Bold', fontSize=10,
                           textColor=colors.white, alignment=TA_CENTER),
        'label':        ps('Lbl',      fontName='Helvetica-Bold', fontSize=8.5,
                           textColor=AZUL_UTM),
        'valor':        ps('Val',      fontSize=8.5, textColor=NEGRO),
        'cuerpo':       ps('Body',     fontSize=9, leading=14,
                           alignment=TA_JUSTIFY, textColor=NEGRO),
        'firma_label':  ps('FirmaL',   fontName='Helvetica-Bold', fontSize=8,
                           textColor=GRIS_TEXT, alignment=TA_CENTER),
        'pie':          ps('Pie',      fontSize=7.5, textColor=GRIS_TEXT,
                           alignment=TA_CENTER),
        'num_pag':      ps('NumPag',   fontName='Helvetica-Bold', fontSize=8,
                           textColor=AZUL_UTM, alignment=TA_RIGHT),
    }


def _header_bar(text, s):
    """Barra de sección azul con texto blanco."""
    t = Table([[Paragraph(text, s['seccion'])]], colWidths=[540])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), AZUL_UTM),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
    ]))
    return t


def _info_table(rows, s, col_widths=None):
    """Tabla de datos con etiqueta/valor en pares."""
    cw = col_widths or [110, 160, 110, 160]
    data = []
    for row in rows:
        data.append([Paragraph(c, s['label'] if i % 2 == 0 else s['valor'])
                     for i, c in enumerate(row)])
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.8, BORDE),
        ('INNERGRID',     (0, 0), (-1, -1), 0.4, BORDE),
        ('BACKGROUND',    (0, 0), (-1, -1), FONDO_CELD),
        ('ROWBACKGROUNDS',(0, 0), (-1, -1), [colors.white, FONDO_CELD]),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
    ]))
    return t


def _text_block(content, s, bg=None):
    """Bloque de texto con borde suave."""
    if not content:
        content = '<i>No registrado.</i>'
    inner = Table([[Paragraph(content, s['cuerpo'])]], colWidths=[520])
    inner.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), bg or colors.white),
        ('BOX',           (0, 0), (-1, -1), 0.7, BORDE),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    return inner


def generar_pdf_solicitud(solicitud, incluir_anexos_firmas=True):
    """
    Genera el INFORME TÉCNICO DE MANTENIMIENTO en PDF.
    Retorna un buffer BytesIO con el contenido listo para enviar.
    Formato: Universidad Técnica de Manabí — SAST
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=36,  bottomMargin=48
    )

    s  = _styles()
    el = []   # elementos del documento

    # ─────────────────────────────────────────────────────────────────
    # ENCABEZADO INSTITUCIONAL
    # ─────────────────────────────────────────────────────────────────
    fecha_emision = datetime.now().strftime('%d/%m/%Y  %H:%M')

    # Intentar cargar logo si existe
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'utm_logo.png')
    logo_cell = []
    if os.path.exists(logo_path):
        try:
            logo_cell = [Image(logo_path, width=1.1*inch, height=1.1*inch)]
        except Exception:
            logo_cell = [Paragraph('', s['subtitulo'])]
    else:
        logo_cell = [Paragraph('', s['subtitulo'])]

    titulo_cell = [
        Paragraph('UNIVERSIDAD TÉCNICA DE MANABÍ', ParagraphStyle(
            'UTM', fontName='Helvetica-Bold', fontSize=11,
            textColor=AZUL_UTM, alignment=TA_CENTER, leading=14)),
        Paragraph('Facultad de Ciencias Informáticas', ParagraphStyle(
            'Fac', fontName='Helvetica', fontSize=8.5,
            textColor=GRIS_TEXT, alignment=TA_CENTER, leading=12)),
        Spacer(1, 4),
        Paragraph('INFORME TÉCNICO DE MANTENIMIENTO', ParagraphStyle(
            'ITitle', fontName='Helvetica-Bold', fontSize=12,
            textColor=NEGRO, alignment=TA_CENTER, leading=16)),
    ]

    codigo_cell = [
        Paragraph(f'N° <b>{solicitud.id_solicitud:04d}</b>',
                  ParagraphStyle('Cod', fontName='Helvetica-Bold', fontSize=10,
                                 textColor=AZUL_UTM, alignment=TA_RIGHT)),
        Paragraph(f'Emisión: {fecha_emision}',
                  ParagraphStyle('Fecha', fontSize=7.5,
                                 textColor=GRIS_TEXT, alignment=TA_RIGHT)),
    ]

    ht = Table([[logo_cell, titulo_cell, codigo_cell]], colWidths=[80, 370, 130])
    ht.setStyle(TableStyle([
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',   (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    el.append(ht)
    el.append(HRFlowable(width='100%', thickness=2,
                         color=AZUL_UTM, spaceBefore=6, spaceAfter=8))

    # ─────────────────────────────────────────────────────────────────
    # DATOS GENERALES DEL SERVICIO SOLICITADO
    # ─────────────────────────────────────────────────────────────────
    el.append(_header_bar('Datos Generales del Servicio Solicitado', s))
    el.append(Spacer(1, 4))

    cliente = solicitud.cliente
    tecnico  = solicitud.tecnico

    fecha_creacion  = solicitud.fecha_creacion.strftime('%d/%m/%Y') if solicitud.fecha_creacion else '—'
    hora_creacion   = solicitud.fecha_creacion.strftime('%H:%M:%S')  if solicitud.fecha_creacion else '—'
    fecha_atencion  = solicitud.fecha_atencion.strftime('%d/%m/%Y')  if solicitud.fecha_atencion else '—'
    horario         = solicitud.horario_solicitado or '—'
    tipo_servicio   = solicitud.tipo_soporte.nombre_soporte          if solicitud.tipo_soporte else '—'
    sector_cliente  = cliente.sector                                  if cliente else '—'
    tel_cliente     = cliente.numero_telefono                         if cliente else '—'
    correo_cliente  = cliente.correo                                  if cliente else '—'
    nombre_cliente  = cliente.nombre_completo                         if cliente else '—'
    cedula_cliente  = cliente.ncedula                                 if cliente else '—'
    nombre_tecnico  = tecnico.nombre_completo                         if tecnico else 'No asignado'

    el.append(_info_table([
        ['Usuario Solicitante / Contratista:', nombre_cliente,
         'Fecha Recepción Equipo:', fecha_creacion],
        ['Cédula:', cedula_cliente,
         'Hora:', hora_creacion],
        ['Técnico Asignado:', nombre_tecnico,
         'Fecha de Atención:', fecha_atencion],
        ['Lugar donde requiere el servicio:', sector_cliente,
         'Horario Solicitado:', horario],
        ['Correo del Usuario:', correo_cliente,
         'Teléfono Usuario:', tel_cliente],
    ], s))
    el.append(Spacer(1, 6))

    # Tabla de tipo de servicio
    header_ts = Table(
        [[Paragraph('Tipo de Servicio', s['label']),
          Paragraph('Información Preliminar de la Solicitud', s['label'])]],
        colWidths=[160, 380]
    )
    header_ts.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), AZUL_CLARO),
        ('BOX',           (0, 0), (-1, -1), 0.8, BORDE),
        ('INNERGRID',     (0, 0), (-1, -1), 0.4, BORDE),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    el.append(header_ts)

    descripcion_solicitud = solicitud.descripcion or 'Sin descripción.'
    body_ts = Table(
        [[Paragraph(tipo_servicio, s['valor']),
          Paragraph(descripcion_solicitud[:280] + ('…' if len(descripcion_solicitud) > 280 else ''), s['cuerpo'])]],
        colWidths=[160, 380]
    )
    body_ts.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.8, BORDE),
        ('INNERGRID',     (0, 0), (-1, -1), 0.4, BORDE),
        ('BACKGROUND',    (0, 0), (-1, -1), colors.white),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
    ]))
    el.append(body_ts)
    el.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────
    # DESCRIPCIÓN DE HALLAZGOS Y ACTIVIDADES REALIZADAS
    # ─────────────────────────────────────────────────────────────────
    if solicitud.reporte:
        rep = solicitud.reporte
        rep_fecha = rep.fecha_creacion.strftime('%d/%m/%Y') if rep.fecha_creacion else '—'

        fecha_col = Table(
            [[Paragraph('Fecha de la intervención:', s['label']),
              Paragraph(rep_fecha, s['valor'])],
             [Paragraph('Descripción de los hallazgos y actividades realizadas', s['label']), '']],
            colWidths=[180, 360]
        )
        fecha_col.setStyle(TableStyle([
            ('SPAN',          (0, 1), (1, 1)),
            ('BOX',           (0, 0), (-1, -1), 0.8, BORDE),
            ('INNERGRID',     (0, 0), (-1, -1), 0.4, BORDE),
            ('BACKGROUND',    (0, 0), (-1, -1), AZUL_CLARO),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
            ('FONTNAME',      (0, 1), (0, 1), 'Helvetica-Bold'),
        ]))
        el.append(fecha_col)

        desc_trabajo = rep.descripcion_trabajo or 'Sin descripción registrada.'
        el.append(_text_block(desc_trabajo, s))
        el.append(Spacer(1, 8))

        # ── Observaciones / Recomendaciones ──────────────────────────
        el.append(_header_bar('Observaciones / Recomendaciones', s))
        el.append(Spacer(1, 4))

        recom_text = rep.recomendaciones if rep.recomendaciones else \
            'No se registraron observaciones adicionales para esta intervención.'
        el.append(_text_block(recom_text, s, bg=colors.HexColor('#FAFFFE')))
        el.append(Spacer(1, 8))

        # ── Evidencia fotográfica ─────────────────────────────────────
        static_folder = os.path.join(current_app.root_path, 'static')
        img1_obj = img2_obj = None

        def _load_img(rel_path, w, h):
            """Carga una imagen de forma segura; retorna None si falla."""
            if not rel_path:
                return None
            full = os.path.join(static_folder, rel_path.replace('/', os.sep))
            if not os.path.exists(full):
                return None
            try:
                from PIL import Image as PILImage
                with open(full, 'rb') as f:
                    pil_img = PILImage.open(f)
                    pil_img.verify()          # valida integridad
                # Re-abrir tras verify (verify cierra el stream)
                pil_img = PILImage.open(full)
                # Convertir a RGB si es necesario (evita problemas con PNG/RGBA)
                if pil_img.mode not in ('RGB', 'L'):
                    pil_img = pil_img.convert('RGB')
                import io as _io
                buf = _io.BytesIO()
                pil_img.save(buf, format='JPEG', quality=85)
                buf.seek(0)
                return Image(buf, width=w, height=h)
            except Exception as e:
                current_app.logger.warning(f'PDF: no se pudo cargar imagen {rel_path}: {e}')
                return None

        if rep.imagen_evidencia_1:
            img1_obj = _load_img(rep.imagen_evidencia_1, 2.5*inch, 1.9*inch)
        if rep.imagen_evidencia_2:
            img2_obj = _load_img(rep.imagen_evidencia_2, 2.5*inch, 1.9*inch)

        if img1_obj or img2_obj:
            if incluir_anexos_firmas:
                el.append(_header_bar('Anexos (Evidencia Fotográfica)', s))
            el.append(Spacer(1, 6))

            cell1 = [[Paragraph('<b>Evidencia 1 — Recepción del equipo</b>', s['label'])],
                     [img1_obj if img1_obj else Paragraph('<i>Imagen no disponible</i>', s['valor'])]]
            cell2 = [[Paragraph('<b>Evidencia 2 — Entrega del equipo</b>', s['label'])],
                     [img2_obj if img2_obj else Paragraph('<i>Imagen no disponible</i>', s['valor'])]]

            if incluir_anexos_firmas:
                t_imgs = Table([[
                    Table(cell1, colWidths=[260]),
                    Table(cell2, colWidths=[260])
                ]], colWidths=[270, 270])
                t_imgs.setStyle(TableStyle([
                    ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                    ('BOX',           (0, 0), (-1, -1), 0.8, BORDE),
                    ('INNERGRID',     (0, 0), (-1, -1), 0.4, BORDE),
                    ('TOPPADDING',    (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
                ]))
                el.append(t_imgs)
                el.append(Spacer(1, 8))

    else:
        el.append(Paragraph('<i>Informe técnico aún no registrado.</i>', s['valor']))
        el.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────
    # CALIFICACIÓN DEL CLIENTE
    # ─────────────────────────────────────────────────────────────────
    if solicitud.calificacion:
        el.append(_header_bar('Conformidad y Calificación del Cliente', s))
        el.append(Spacer(1, 4))
        cal = solicitud.calificacion
        stars = '★' * cal.puntuacion + '☆' * (5 - cal.puntuacion)
        comentario = cal.comentario or 'Sin comentarios adicionales.'
        cal_rows = [
            ['Puntuación:', f'{stars}  ({cal.puntuacion}/5)'],
            ['Comentario:', comentario],
        ]
        t_cal = Table([[Paragraph(r[0], s['label']), Paragraph(r[1], s['valor'])]
                       for r in cal_rows], colWidths=[100, 440])
        t_cal.setStyle(TableStyle([
            ('BOX',           (0, 0), (-1, -1), 0.8, BORDE),
            ('INNERGRID',     (0, 0), (-1, -1), 0.4, BORDE),
            ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#FFFDE7')),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ]))
        el.append(t_cal)
        el.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────────
    # FIRMAS — 3 campos: Cliente · Técnico · Aprobado por
    # ─────────────────────────────────────────────────────────────────
    if incluir_anexos_firmas:
        el.append(HRFlowable(width='100%', thickness=1,
                             color=BORDE, spaceBefore=14, spaceAfter=10))

        tecnico_nombre_f = tecnico.nombre_completo if tecnico else '—'
        tecnico_cargo    = ''
        if tecnico and hasattr(tecnico, 'detalles_tecnico') and tecnico.detalles_tecnico:
            carrera = tecnico.detalles_tecnico.carrera or ''
            sem     = f'Semestre {tecnico.detalles_tecnico.semestre}' if tecnico.detalles_tecnico.semestre else ''
            tecnico_cargo = f'Estudiante • {carrera}'.rstrip(' •') if carrera else 'Técnico'

        firmas_data = [[
            Paragraph(
                '_______________________<br/>'
                f'<b>{tecnico_nombre_f}</b><br/>'
                f'{tecnico_cargo or "Técnico Asignado"}<br/>'
                '<font color="#888888" size="7">Técnico Asignado</font>',
                s['firma_label']),
            Paragraph(
                '_______________________<br/>'
                '<b>Ing. ________________________</b><br/>'
                'Coordinador del Servicio Técnico<br/>'
                '<font color="#888888" size="7">Revisado por</font>',
                s['firma_label']),
            Paragraph(
                '_______________________<br/>'
                '<b>Ing. ________________________</b><br/>'
                'Director / Jefe de Área<br/>'
                '<font color="#888888" size="7">Aprobado por</font>',
                s['firma_label']),
        ]]

        t_firmas = Table(firmas_data, colWidths=[180, 180, 180])
        t_firmas.setStyle(TableStyle([
            ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        el.append(KeepTogether([t_firmas]))
        el.append(Spacer(1, 8))

    # Pie de página
    el.append(HRFlowable(width='100%', thickness=0.5,
                         color=BORDE, spaceBefore=4, spaceAfter=4))
    el.append(Paragraph(
        f'Documento generado por SAST — Sistema de Agendamiento de Servicio Técnico  |  '
        f'Universidad Técnica de Manabí  |  {fecha_emision}',
        s['pie']))

    # Construir PDF
    doc.build(el)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
# COMPROBANTE DE SERVICIO — versión cliente (sin imágenes ni firmas)
# ─────────────────────────────────────────────────────────────────────────────
def generar_pdf_cliente(solicitud):
    """
    Genera un COMPROBANTE DE SERVICIO simplificado para el cliente.
    No incluye imágenes de evidencia ni bloque de firmas institucionales.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=40,  bottomMargin=50
    )

    s  = _styles()
    el = []
    fecha_emision = datetime.now().strftime('%d/%m/%Y  %H:%M')

    # ── Encabezado institucional ──────────────────────────────────────────────
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'utm_logo.png')
    logo_cell = []
    if os.path.exists(logo_path):
        try:
            logo_cell = [Image(logo_path, width=1.0*inch, height=1.0*inch)]
        except Exception:
            logo_cell = [Paragraph('', s['subtitulo'])]
    else:
        logo_cell = [Paragraph('', s['subtitulo'])]

    titulo_cell = [
        Paragraph('UNIVERSIDAD TÉCNICA DE MANABÍ', ParagraphStyle(
            'UTMc', fontName='Helvetica-Bold', fontSize=11,
            textColor=AZUL_UTM, alignment=TA_CENTER, leading=14)),
        Paragraph('Facultad de Ciencias Informáticas', ParagraphStyle(
            'Facc', fontName='Helvetica', fontSize=8.5,
            textColor=GRIS_TEXT, alignment=TA_CENTER, leading=12)),
        Spacer(1, 4),
        Paragraph('COMPROBANTE DE SERVICIO TÉCNICO', ParagraphStyle(
            'CTitle', fontName='Helvetica-Bold', fontSize=12,
            textColor=NEGRO, alignment=TA_CENTER, leading=16)),
    ]

    codigo_cell = [
        Paragraph(f'N° <b>{solicitud.id_solicitud:04d}</b>',
                  ParagraphStyle('CodC', fontName='Helvetica-Bold', fontSize=10,
                                 textColor=AZUL_UTM, alignment=TA_RIGHT)),
        Paragraph(f'Emisión: {fecha_emision}',
                  ParagraphStyle('FechaC', fontSize=7.5,
                                 textColor=GRIS_TEXT, alignment=TA_RIGHT)),
    ]

    ht = Table([[logo_cell, titulo_cell, codigo_cell]], colWidths=[80, 370, 130])
    ht.setStyle(TableStyle([
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',   (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    el.append(ht)
    el.append(HRFlowable(width='100%', thickness=2,
                         color=AZUL_UTM, spaceBefore=6, spaceAfter=8))

    # ── Datos generales ───────────────────────────────────────────────────────
    el.append(_header_bar('Información del Servicio', s))
    el.append(Spacer(1, 4))

    cliente = solicitud.cliente
    tecnico  = solicitud.tecnico
    rep      = solicitud.reporte if hasattr(solicitud, 'reporte') else None

    fecha_creacion = solicitud.fecha_creacion.strftime('%d/%m/%Y') if solicitud.fecha_creacion else '—'
    hora_creacion  = solicitud.fecha_creacion.strftime('%H:%M')    if solicitud.fecha_creacion else '—'
    fecha_atencion = solicitud.fecha_atencion.strftime('%d/%m/%Y') if solicitud.fecha_atencion else '—'
    tipo_servicio  = solicitud.tipo_soporte.nombre_soporte         if solicitud.tipo_soporte else '—'
    sector_cliente = cliente.sector                                 if cliente else '—'
    nombre_cliente = cliente.nombre_completo                        if cliente else '—'
    cedula_cliente = cliente.ncedula                                if cliente else '—'
    tel_cliente    = cliente.numero_telefono                        if cliente else '—'
    correo_cliente = cliente.correo                                 if cliente else '—'
    nombre_tecnico = tecnico.nombre_completo                        if tecnico else 'No asignado'
    estado         = solicitud.estado.nombre_estado                 if solicitud.estado else '—'

    el.append(_info_table([
        ['Cliente / Solicitante:', nombre_cliente,
         'Cédula:', cedula_cliente],
        ['Fecha de Creación:', fecha_creacion,
         'Hora:', hora_creacion],
        ['Técnico Asignado:', nombre_tecnico,
         'Fecha de Atención:', fecha_atencion],
        ['Tipo de Servicio:', tipo_servicio,
         'Estado:', estado],
        ['Sector:', sector_cliente,
         'Teléfono:', tel_cliente],
        ['Correo:', correo_cliente,
         'Horario Solicitado:', solicitud.horario_solicitado or '—'],
    ], s))
    el.append(Spacer(1, 8))

    # ── Descripción de la solicitud ───────────────────────────────────────────
    el.append(_header_bar('Descripción del Problema / Solicitud', s))
    el.append(Spacer(1, 4))
    el.append(_text_block(solicitud.descripcion or '—', s))
    el.append(Spacer(1, 8))

    if solicitud.recursos_adicionales:
        el.append(_header_bar('Recursos Adicionales Solicitados', s))
        el.append(Spacer(1, 4))
        el.append(_text_block(solicitud.recursos_adicionales, s))
        el.append(Spacer(1, 8))

    # ── Resultados del servicio (si ya fue resuelto) ──────────────────────────
    if rep:
        el.append(_header_bar('Resultado del Servicio Realizado', s))
        el.append(Spacer(1, 4))
        el.append(_text_block(getattr(rep, 'descripcion_trabajo', None) or '—', s))
        el.append(Spacer(1, 8))

        if getattr(rep, 'recomendaciones', None):
            el.append(_header_bar('Observaciones y Recomendaciones', s))
            el.append(Spacer(1, 4))
            el.append(_text_block(rep.recomendaciones, s))
            el.append(Spacer(1, 8))

    # ── Calificación del cliente ──────────────────────────────────────────────
    cal = getattr(solicitud, 'calificacion', None)
    if cal:
        estrellas = '★' * int(cal.puntuacion) + '☆' * (5 - int(cal.puntuacion))
        el.append(_header_bar('Calificación del Servicio', s))
        el.append(Spacer(1, 4))
        bloque_cal = [
            [Paragraph(f'Puntuación: <b>{cal.puntuacion}/5</b>  {estrellas}', s['valor']),
             Paragraph(f'Comentario: {cal.comentario or "Sin comentario"}', s['valor'])]
        ]
        tc = Table(bloque_cal, colWidths=[180, 360])
        tc.setStyle(TableStyle([
            ('BOX',         (0, 0), (-1, -1), 0.7, BORDE),
            ('INNERGRID',   (0, 0), (-1, -1), 0.4, BORDE),
            ('BACKGROUND',  (0, 0), (-1, -1), FONDO_CELD),
            ('TOPPADDING',  (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        el.append(tc)
        el.append(Spacer(1, 10))

    # ── Pie de página ─────────────────────────────────────────────────────────
    el.append(HRFlowable(width='100%', thickness=0.5,
                         color=BORDE, spaceBefore=4, spaceAfter=4))
    el.append(Paragraph(
        f'Comprobante generado por SAST — Sistema de Agendamiento de Servicio Técnico  |  '
        f'Universidad Técnica de Manabí  |  {fecha_emision}',
        s['pie']))

    doc.build(el)
    buffer.seek(0)
    return buffer
