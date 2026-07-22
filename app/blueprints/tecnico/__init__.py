from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, send_file
from flask_login import login_required, current_user
from app.extensions import db, socketio, mail
from app.models import Solicitud, EstadoSolicitud, Mensaje, Reporte, User, Rol
from app.utils import save_file, allowed_file
from app import email_service
from app.pdf_generator import generar_pdf_solicitud
from flask_mail import Message
from functools import wraps
import threading

tecnico_bp = Blueprint('tecnico', __name__, template_folder='templates')


def tecnico_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.es_tecnico:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@tecnico_bp.route('/dashboard')
@login_required
@tecnico_required
def dashboard():
    solicitudes = Solicitud.query.filter_by(
        id_tecnico=current_user.id_user
    ).order_by(Solicitud.fecha_atencion.asc()).all()

    # Contar mensajes no leídos total
    total_no_leidos = 0
    for s in solicitudes:
        total_no_leidos += Mensaje.query.filter_by(
            id_solicitud=s.id_solicitud,
            leido=False
        ).filter(
            Mensaje.id_usuario_remitente != current_user.id_user
        ).count()

    return render_template(
        'tecnico/dashboard.html',
        solicitudes=solicitudes,
        total_no_leidos=total_no_leidos
    )


@tecnico_bp.route('/solicitud/<int:solicitud_id>')
@login_required
@tecnico_required
def ver_solicitud(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)

    if solicitud.id_tecnico != current_user.id_user:
        abort(403)

    # Mensajes públicos (cliente <-> técnico)
    mensajes = Mensaje.query.filter_by(
        id_solicitud=solicitud_id,
        canal='publico'
    ).order_by(Mensaje.fecha_envio.asc()).all()

    # Mensajes internos (admin <-> técnico)
    mensajes_internos = Mensaje.query.filter_by(
        id_solicitud=solicitud_id,
        canal='interno'
    ).order_by(Mensaje.fecha_envio.asc()).all()

    # Marcar mensajes públicos como leídos
    for msg in mensajes:
        if msg.id_usuario_remitente != current_user.id_user:
            msg.leido = True
    # Marcar mensajes internos como leídos
    for msg in mensajes_internos:
        if msg.id_usuario_remitente != current_user.id_user:
            msg.leido = True
    db.session.commit()

    is_closed = solicitud.estado.nombre_estado in ['Resuelto', 'Cancelado']
    return render_template(
        'tecnico/ver_solicitud.html',
        solicitud=solicitud,
        mensajes=mensajes,
        mensajes_internos=mensajes_internos,
        is_closed=is_closed
    )


@tecnico_bp.route('/solicitud/<int:solicitud_id>/pdf')
@login_required
@tecnico_required
def descargar_pdf(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    if solicitud.id_tecnico != current_user.id_user:
        abort(403)
    if solicitud.estado.nombre_estado != 'Resuelto':
        flash('El informe PDF solo está disponible cuando la asistencia ha finalizado (Resuelto).', 'warning')
        return redirect(url_for('tecnico.ver_solicitud', solicitud_id=solicitud_id))

    pdf_buffer = generar_pdf_solicitud(solicitud)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Informe_Solicitud_{solicitud.id_solicitud}.pdf'
    )


@tecnico_bp.route('/solicitud/<int:solicitud_id>/informe', methods=['GET', 'POST'])
@login_required
@tecnico_required
def crear_informe(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)

    if solicitud.id_tecnico != current_user.id_user:
        abort(403)

    if solicitud.estado.nombre_estado in ['Resuelto', 'Cancelado']:
        flash('Esta solicitud ya está cerrada y no puede recibir un informe.', 'warning')
        return redirect(url_for('tecnico.ver_solicitud', solicitud_id=solicitud_id))

    if solicitud.reporte:
        flash('Ya existe un informe para esta solicitud.', 'info')
        return redirect(url_for('tecnico.ver_solicitud', solicitud_id=solicitud_id))

    if request.method == 'POST':
        descripcion_trabajo = request.form.get('descripcion_trabajo', '').strip()
        recomendaciones = request.form.get('recomendaciones', '').strip()
        imagen_1 = request.files.get('imagen_evidencia_1')
        imagen_2 = request.files.get('imagen_evidencia_2')

        errores = []

        if not descripcion_trabajo:
            errores.append('La descripción del trabajo es obligatoria.')

        if not imagen_1 or not imagen_1.filename:
            errores.append('La imagen de cómo recibió el equipo es obligatoria.')
        elif not allowed_file(imagen_1.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
            errores.append('La imagen 1 debe ser un archivo de imagen válido (PNG, JPG, JPEG, GIF, WEBP).')

        if not imagen_2 or not imagen_2.filename:
            errores.append('La imagen de cómo entregó el equipo es obligatoria.')
        elif not allowed_file(imagen_2.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
            errores.append('La imagen 2 debe ser un archivo de imagen válido (PNG, JPG, JPEG, GIF, WEBP).')

        if errores:
            for error in errores:
                flash(error, 'danger')
            return render_template('tecnico/informe.html', solicitud=solicitud)

        # Guardar imágenes
        path_img1 = save_file(imagen_1, 'reportes')
        path_img2 = save_file(imagen_2, 'reportes')

        if not path_img1 or not path_img2:
            flash('Error al guardar las imágenes. Inténtalo de nuevo.', 'danger')
            return render_template('tecnico/informe.html', solicitud=solicitud)

        # Crear reporte
        reporte = Reporte(
            id_solicitud=solicitud_id,
            id_tecnico=current_user.id_user,
            descripcion_trabajo=descripcion_trabajo,
            recomendaciones=recomendaciones or None,
            imagen_evidencia_1=path_img1,
            imagen_evidencia_2=path_img2
        )
        db.session.add(reporte)

        # Cambiar estado a Resuelto
        estado_resuelto = EstadoSolicitud.query.filter_by(nombre_estado='Resuelto').first()
        solicitud.id_estado = estado_resuelto.id_estado
        db.session.commit()

        # Notificar al cliente por SocketIO
        socketio.emit('ticket_resuelto', {
            'solicitud_id': solicitud_id,
            'mensaje': f'Tu solicitud #{solicitud_id} ha sido resuelta. ¡Por favor califica el servicio!'
        }, room=f'user_{solicitud.id_cliente}')

        # Notificar por correo al cliente y admins en segundo plano
        rol_admin = Rol.query.filter_by(nombre_rol='admin').first()
        admins = User.query.filter_by(id_rol=rol_admin.id_rol).all() if rol_admin else []
        threading.Thread(
            target=email_service.enviar_solicitud_resuelta_cliente,
            args=(solicitud,),
            daemon=True
        ).start()
        threading.Thread(
            target=email_service.enviar_solicitud_resuelta_admin,
            args=(solicitud, admins),
            daemon=True
        ).start()

        flash('¡Informe enviado con éxito! La solicitud ha sido marcada como Resuelta.', 'success')
        return redirect(url_for('tecnico.dashboard'))

    return render_template('tecnico/informe.html', solicitud=solicitud)
