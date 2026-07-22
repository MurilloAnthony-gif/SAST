from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    User, Rol, Solicitud, EstadoSolicitud, TipoSoporte,
    CalificacionTecnico, DetallesTecnico
)
from app import email_service
from app.pdf_generator import generar_pdf_solicitud
from functools import wraps
from datetime import datetime
from sqlalchemy import func
import threading

admin_bp = Blueprint('admin', __name__, template_folder='templates')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.es_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Métricas
    total_solicitudes = Solicitud.query.count()

    estados = EstadoSolicitud.query.all()
    conteo_estados = {}
    for estado in estados:
        conteo_estados[estado.nombre_estado] = Solicitud.query.filter_by(
            id_estado=estado.id_estado
        ).count()

    total_clientes = User.query.join(Rol).filter(Rol.nombre_rol == 'solicitante').count()
    total_tecnicos = User.query.join(Rol).filter(Rol.nombre_rol == 'técnico').count()

    # Promedio de calificaciones
    avg_cal = db.session.query(func.avg(CalificacionTecnico.puntuacion)).scalar() or 0

    # Últimas solicitudes pendientes
    estado_pendiente = EstadoSolicitud.query.filter_by(nombre_estado='Pendiente').first()
    pendientes_recientes = []
    if estado_pendiente:
        pendientes_recientes = Solicitud.query.filter_by(
            id_estado=estado_pendiente.id_estado
        ).order_by(Solicitud.fecha_creacion.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_solicitudes=total_solicitudes,
        conteo_estados=conteo_estados,
        total_clientes=total_clientes,
        total_tecnicos=total_tecnicos,
        avg_calificacion=round(float(avg_cal), 1),
        pendientes_recientes=pendientes_recientes
    )


@admin_bp.route('/solicitudes')
@login_required
@admin_required
def solicitudes():
    # Filtros
    estado_filtro = request.args.get('estado', '').strip()
    tipo_filtro = request.args.get('tipo', '').strip()
    busqueda = request.args.get('q', '').strip()

    query = Solicitud.query

    if estado_filtro:
        estado_obj = EstadoSolicitud.query.filter_by(nombre_estado=estado_filtro).first()
        if estado_obj:
            query = query.filter_by(id_estado=estado_obj.id_estado)
    if tipo_filtro:
        query = query.filter_by(id_tipo_soporte=int(tipo_filtro))
    if busqueda:
        query = query.join(User, Solicitud.id_cliente == User.id_user).filter(
            User.nombres.ilike(f'%{busqueda}%') |
            User.apellidos.ilike(f'%{busqueda}%') |
            User.correo.ilike(f'%{busqueda}%')
        )

    all_solicitudes = query.order_by(Solicitud.fecha_creacion.desc()).all()
    estados = EstadoSolicitud.query.all()
    tipos = TipoSoporte.query.all()

    return render_template(
        'admin/solicitudes.html',
        solicitudes=all_solicitudes,
        estados=[e.nombre_estado for e in EstadoSolicitud.query.all()],
        tipos=tipos,
        estado_filtro=estado_filtro,
        tipo_filtro=tipo_filtro,
        busqueda=busqueda
    )


@admin_bp.route('/solicitudes/<int:solicitud_id>/asignar', methods=['GET', 'POST'])
@login_required
@admin_required
def asignar_tecnico(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)

    if solicitud.estado.nombre_estado not in ['Pendiente', 'En proceso']:
        flash('Solo se pueden asignar técnicos a solicitudes Pendientes o En proceso.', 'warning')
        return redirect(url_for('admin.solicitudes'))

    rol_tecnico = Rol.query.filter_by(nombre_rol='técnico').first()
    tecnicos = User.query.filter_by(id_rol=rol_tecnico.id_rol).all() if rol_tecnico else []

    if request.method == 'POST':
        id_tecnico = request.form.get('tecnico_id', type=int)

        if not id_tecnico:
            flash('Debes seleccionar un técnico.', 'danger')
            return render_template('admin/asignar.html', solicitud=solicitud, tecnicos=tecnicos)

        tecnico = db.session.get(User, id_tecnico)
        if not tecnico or not tecnico.es_tecnico:
            flash('Técnico inválido.', 'danger')
            return render_template('admin/asignar.html', solicitud=solicitud, tecnicos=tecnicos)

        solicitud.id_tecnico = id_tecnico
        estado_en_proceso = EstadoSolicitud.query.filter_by(nombre_estado='En proceso').first()
        solicitud.id_estado = estado_en_proceso.id_estado
        db.session.commit()

        # Notificar al cliente y al técnico en segundo plano
        threading.Thread(
            target=email_service.enviar_tecnico_asignado_cliente,
            args=(solicitud,),
            daemon=True
        ).start()
        threading.Thread(
            target=email_service.enviar_solicitud_asignada_tecnico,
            args=(solicitud,),
            daemon=True
        ).start()

        flash(f'Técnico {tecnico.nombre_completo} asignado con éxito. Estado → En proceso.', 'success')
        return redirect(url_for('admin.solicitudes'))

    return render_template('admin/asignar.html', solicitud=solicitud, tecnicos=tecnicos)


@admin_bp.route('/solicitudes/<int:solicitud_id>')
@login_required
@admin_required
def ver_solicitud(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    return render_template('admin/ver_solicitud.html', solicitud=solicitud)


@admin_bp.route('/solicitudes/<int:solicitud_id>/pdf')
@login_required
@admin_required
def descargar_pdf(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    if solicitud.estado.nombre_estado != 'Resuelto':
        flash('El informe PDF solo está disponible cuando la asistencia ha finalizado (Resuelto).', 'warning')
        return redirect(url_for('admin.ver_solicitud', solicitud_id=solicitud_id))

    pdf_buffer = generar_pdf_solicitud(solicitud)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Informe_Solicitud_{solicitud.id_solicitud}.pdf'
    )


@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    rol_filtro = request.args.get('rol', '')
    busqueda = request.args.get('q', '').strip()

    query = User.query.join(Rol)

    if rol_filtro:
        query = query.filter(Rol.nombre_rol == rol_filtro)
    if busqueda:
        query = query.filter(
            User.nombres.ilike(f'%{busqueda}%') |
            User.apellidos.ilike(f'%{busqueda}%') |
            User.correo.ilike(f'%{busqueda}%') |
            User.ncedula.ilike(f'%{busqueda}%')
        )

    all_users = query.order_by(User.nombres.asc()).all()
    roles = Rol.query.all()

    return render_template(
        'admin/usuarios.html',
        usuarios=all_users,
        roles=roles,
        rol_filtro=rol_filtro,
        busqueda=busqueda
    )


@admin_bp.route('/usuarios/crear-tecnico', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_tecnico():
    if request.method == 'POST':
        ncedula = request.form.get('ncedula', '').strip()
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        fecha_nacimiento_str = request.form.get('fecha_nacimiento', '')
        numero_telefono = request.form.get('numero_telefono', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('contrasena', '')
        sector = request.form.get('sector', '').strip()
        carrera = request.form.get('carrera', '').strip()
        semestre_str = request.form.get('semestre', '')

        if not all([ncedula, nombres, apellidos, fecha_nacimiento_str,
                    numero_telefono, correo, password, sector]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/crear_tecnico.html')

        if User.query.filter_by(correo=correo).first():
            flash('Ya existe un usuario con ese correo.', 'danger')
            return render_template('admin/crear_tecnico.html')

        if User.query.filter_by(ncedula=ncedula).first():
            flash('Ya existe un usuario con esa cédula.', 'danger')
            return render_template('admin/crear_tecnico.html')

        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido.', 'danger')
            return render_template('admin/crear_tecnico.html')

        rol_tecnico = Rol.query.filter_by(nombre_rol='técnico').first()

        user = User(
            ncedula=ncedula,
            nombres=nombres.title(),
            apellidos=apellidos.title(),
            fecha_nacimiento=fecha_nacimiento,
            numero_telefono=numero_telefono,
            correo=correo,
            sector=sector,
            declaracion_veracidad=True,
            autorizacion_datos=True,
            id_rol=rol_tecnico.id_rol
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Para obtener el id_user

        # Detalles del técnico
        semestre = int(semestre_str) if semestre_str.isdigit() else None
        detalles = DetallesTecnico(
            id_tecnico=user.id_user,
            carrera=carrera or None,
            semestre=semestre
        )
        db.session.add(detalles)
        db.session.commit()

        # Enviar correo de bienvenida al técnico con su contraseña
        threading.Thread(
            target=email_service.enviar_bienvenida_tecnico,
            args=(user, password),
            daemon=True
        ).start()

        flash(f'Técnico {user.nombre_completo} creado con éxito.', 'success')
        return redirect(url_for('admin.usuarios'))

    return render_template('admin/crear_tecnico.html')


@admin_bp.route('/usuarios/<int:user_id>/desactivar', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id_user == current_user.id_user:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('admin.usuarios'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Usuario {user.nombre_completo} eliminado.', 'success')
    return redirect(url_for('admin.usuarios'))
