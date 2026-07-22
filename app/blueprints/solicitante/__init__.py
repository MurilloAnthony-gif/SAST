from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Solicitud, EstadoSolicitud, TipoSoporte, Mensaje, CalificacionTecnico, User, Rol
from app.utils import save_file, allowed_file
from app import email_service
from app.pdf_generator import generar_pdf_solicitud
from functools import wraps
from datetime import datetime
import threading

solicitante_bp = Blueprint('solicitante', __name__, template_folder='templates')


def solicitante_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.es_solicitante:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@solicitante_bp.route('/dashboard')
@login_required
@solicitante_required
def dashboard():
    solicitudes = Solicitud.query.filter_by(
        id_cliente=current_user.id_user
    ).order_by(Solicitud.fecha_creacion.desc()).all()

    # Solicitudes resueltas sin calificar (para notificación)
    estado_resuelto = EstadoSolicitud.query.filter_by(nombre_estado='Resuelto').first()
    sin_calificar = []
    if estado_resuelto:
        sin_calificar = [s for s in solicitudes
                         if s.id_estado == estado_resuelto.id_estado and not s.calificacion]

    return render_template(
        'solicitante/dashboard.html',
        solicitudes=solicitudes,
        sin_calificar=sin_calificar
    )


@solicitante_bp.route('/nueva-solicitud', methods=['GET', 'POST'])
@login_required
@solicitante_required
def nueva_solicitud():
    tipos = TipoSoporte.query.all()

    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '').strip()
        fecha_atencion_str = request.form.get('fecha_atencion', '')
        horario_solicitado = request.form.get('horario_solicitado', '').strip()
        recursos_adicionales = request.form.get('recursos_adicionales', '').strip()
        id_tipo_soporte = request.form.get('id_tipo_soporte', type=int)

        if not all([descripcion, fecha_atencion_str, horario_solicitado, id_tipo_soporte]):
            flash('Por favor, completa todos los campos obligatorios.', 'danger')
            return render_template('solicitante/nueva_solicitud.html', tipos=tipos)

        try:
            fecha_atencion = datetime.strptime(fecha_atencion_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido.', 'danger')
            return render_template('solicitante/nueva_solicitud.html', tipos=tipos)

        if fecha_atencion < datetime.utcnow().date():
            flash('La fecha de atención no puede ser en el pasado.', 'danger')
            return render_template('solicitante/nueva_solicitud.html', tipos=tipos)

        estado_pendiente = EstadoSolicitud.query.filter_by(nombre_estado='Pendiente').first()

        solicitud = Solicitud(
            descripcion=descripcion,
            fecha_atencion=fecha_atencion,
            horario_solicitado=horario_solicitado,
            recursos_adicionales=recursos_adicionales or None,
            id_cliente=current_user.id_user,
            id_estado=estado_pendiente.id_estado,
            id_tipo_soporte=id_tipo_soporte
        )
        db.session.add(solicitud)
        db.session.commit()

        flash('¡Solicitud creada con éxito! El administrador la revisará pronto.', 'success')

        # Notificar a todos los admins en segundo plano
        rol_admin = Rol.query.filter_by(nombre_rol='admin').first()
        admins = User.query.filter_by(id_rol=rol_admin.id_rol).all() if rol_admin else []
        threading.Thread(
            target=email_service.enviar_nueva_solicitud_admin,
            args=(solicitud, admins),
            daemon=True
        ).start()

        return redirect(url_for('solicitante.dashboard'))

    return render_template('solicitante/nueva_solicitud.html', tipos=tipos)


@solicitante_bp.route('/solicitud/<int:solicitud_id>')
@login_required
@solicitante_required
def ver_solicitud(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)

    if solicitud.id_cliente != current_user.id_user:
        abort(403)

    mensajes = Mensaje.query.filter_by(
        id_solicitud=solicitud_id
    ).order_by(Mensaje.fecha_envio.asc()).all()

    # Marcar mensajes como leídos
    for msg in mensajes:
        if msg.id_usuario_remitente != current_user.id_user:
            msg.leido = True
    db.session.commit()

    return render_template(
        'solicitante/ver_solicitud.html',
        solicitud=solicitud,
        mensajes=mensajes
    )


@solicitante_bp.route('/solicitud/<int:solicitud_id>/pdf')
@login_required
@solicitante_required
def descargar_pdf(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    if solicitud.id_cliente != current_user.id_user:
        abort(403)
    if solicitud.estado.nombre_estado != 'Resuelto':
        flash('El informe PDF solo está disponible cuando la asistencia ha finalizado (Resuelto).', 'warning')
        return redirect(url_for('solicitante.ver_solicitud', solicitud_id=solicitud_id))

    pdf_buffer = generar_pdf_solicitud(solicitud)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Informe_Solicitud_{solicitud.id_solicitud}.pdf'
    )


@solicitante_bp.route('/solicitud/<int:solicitud_id>/cancelar', methods=['POST'])
@login_required
@solicitante_required
def cancelar_solicitud(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)

    if solicitud.id_cliente != current_user.id_user:
        abort(403)

    if solicitud.estado.nombre_estado not in ['Pendiente']:
        flash('Solo se pueden cancelar solicitudes en estado Pendiente.', 'warning')
        return redirect(url_for('solicitante.ver_solicitud', solicitud_id=solicitud_id))

    estado_cancelado = EstadoSolicitud.query.filter_by(nombre_estado='Cancelado').first()
    solicitud.id_estado = estado_cancelado.id_estado
    db.session.commit()

    flash('Solicitud cancelada.', 'info')
    return redirect(url_for('solicitante.dashboard'))


@solicitante_bp.route('/solicitud/<int:solicitud_id>/calificar', methods=['GET', 'POST'])
@login_required
@solicitante_required
def calificar(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)

    if solicitud.id_cliente != current_user.id_user:
        abort(403)

    if solicitud.estado.nombre_estado != 'Resuelto':
        flash('Solo puedes calificar servicios resueltos.', 'warning')
        return redirect(url_for('solicitante.dashboard'))

    if solicitud.calificacion:
        flash('Ya calificaste este servicio.', 'info')
        return redirect(url_for('solicitante.ver_solicitud', solicitud_id=solicitud_id))

    if request.method == 'POST':
        puntuacion = request.form.get('puntuacion', type=int)
        comentario = request.form.get('comentario', '').strip()

        if not puntuacion or puntuacion < 1 or puntuacion > 5:
            flash('Debes seleccionar una puntuación entre 1 y 5 estrellas.', 'danger')
            return render_template('solicitante/calificar.html', solicitud=solicitud)

        calificacion = CalificacionTecnico(
            id_solicitud=solicitud_id,
            id_cliente=current_user.id_user,
            puntuacion=puntuacion,
            comentario=comentario or None
        )
        db.session.add(calificacion)
        db.session.commit()

        flash('¡Gracias por tu calificación! Tu opinión es muy importante.', 'success')
        return redirect(url_for('solicitante.dashboard'))

    return render_template('solicitante/calificar.html', solicitud=solicitud)
