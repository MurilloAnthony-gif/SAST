from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.extensions import db, socketio, mail
from app.models import Solicitud, EstadoSolicitud, Mensaje, Reporte
from app.utils import save_file, allowed_file
from flask_mail import Message
from functools import wraps

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

    mensajes = Mensaje.query.filter_by(
        id_solicitud=solicitud_id
    ).order_by(Mensaje.fecha_envio.asc()).all()

    # Marcar como leídos
    for msg in mensajes:
        if msg.id_usuario_remitente != current_user.id_user:
            msg.leido = True
    db.session.commit()

    return render_template(
        'tecnico/ver_solicitud.html',
        solicitud=solicitud,
        mensajes=mensajes
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

        # Notificar por email (si está configurado)
        _enviar_email_resolucion(solicitud)

        flash('¡Informe enviado con éxito! La solicitud ha sido marcada como Resuelta.', 'success')
        return redirect(url_for('tecnico.dashboard'))

    return render_template('tecnico/informe.html', solicitud=solicitud)


def _enviar_email_resolucion(solicitud):
    """Envía email de notificación al cliente cuando se resuelve su solicitud."""
    try:
        msg = Message(
            subject=f'✅ Tu solicitud #{solicitud.id_solicitud} ha sido resuelta — SAST',
            recipients=[solicitud.cliente.correo],
            html=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #4f46e5;">¡Tu servicio técnico ha sido completado!</h2>
                <p>Hola <strong>{solicitud.cliente.nombres}</strong>,</p>
                <p>El técnico <strong>{solicitud.tecnico.nombre_completo}</strong> ha finalizado 
                tu solicitud de soporte técnico.</p>
                <p><strong>Solicitud #:</strong> {solicitud.id_solicitud}<br>
                <strong>Tipo:</strong> {solicitud.tipo_soporte.nombre_soporte}</p>
                <p>Ingresa al sistema para <strong>calificar el servicio recibido</strong>.</p>
                <a href="#" style="background:#4f46e5;color:white;padding:12px 24px;
                   border-radius:8px;text-decoration:none;display:inline-block;margin-top:16px;">
                    Calificar Servicio
                </a>
                <p style="color:#888;margin-top:24px;font-size:12px;">
                    Sistema SAST — Servicio Técnico Universitario
                </p>
            </div>
            '''
        )
        mail.send(msg)
    except Exception:
        # No fallar si el email no está configurado
        pass
