import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate, socketio, mail, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')
    mail.init_app(app)
    csrf.init_app(app)

    # Crear carpetas de uploads
    upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
    os.makedirs(os.path.join(upload_folder, 'reportes'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'mensajes'), exist_ok=True)

    # Importar modelos para que Flask-Migrate los detecte
    with app.app_context():
        from app.models import (
            User, Rol, DetallesTecnico,
            Solicitud, EstadoSolicitud, TipoSoporte,
            Mensaje, Reporte, CalificacionTecnico
        )

        # Registrar blueprints
        from app.blueprints.auth import auth_bp
        from app.blueprints.solicitante import solicitante_bp
        from app.blueprints.tecnico import tecnico_bp
        from app.blueprints.admin import admin_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(solicitante_bp, url_prefix='/solicitante')
        app.register_blueprint(tecnico_bp, url_prefix='/tecnico')
        app.register_blueprint(admin_bp, url_prefix='/admin')

        # Registrar SocketIO events
        from app.sockets import register_socketio_events
        register_socketio_events(socketio)

        # Registrar user_loader
        from app.extensions import login_manager as lm

        @lm.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

        # Ruta raíz
        from flask import redirect, url_for
        from flask_login import current_user

        @app.route('/')
        def index():
            if current_user.is_authenticated:
                if current_user.es_admin:
                    return redirect(url_for('admin.dashboard'))
                elif current_user.es_tecnico:
                    return redirect(url_for('tecnico.dashboard'))
                else:
                    return redirect(url_for('solicitante.dashboard'))
            return redirect(url_for('auth.login'))

        # Comando CLI para inicializar la BD con datos semilla
        @app.cli.command('init-db')
        def init_db_command():
            """Inicializa la base de datos y carga datos semilla."""
            db.create_all()
            _seed_data()
            print('[OK] Base de datos inicializada con exito.')

        # Contexto para templates
        @app.context_processor
        def inject_globals():
            from app.models import Solicitud, EstadoSolicitud
            notificaciones = []
            if current_user.is_authenticated and current_user.es_solicitante:
                estado_resuelto = EstadoSolicitud.query.filter_by(nombre_estado='Resuelto').first()
                if estado_resuelto:
                    notificaciones = Solicitud.query.filter_by(
                        id_cliente=current_user.id_user,
                        id_estado=estado_resuelto.id_estado
                    ).filter(
                        ~Solicitud.calificacion.has()
                    ).all()
            return dict(notificaciones_pendientes=notificaciones)

    return app


def _seed_data():
    """Pobla la base de datos con datos iniciales."""
    from app.models import Rol, EstadoSolicitud, TipoSoporte, User
    from datetime import date

    # Roles
    if not Rol.query.first():
        roles = [
            Rol(nombre_rol='solicitante'),
            Rol(nombre_rol='técnico'),
            Rol(nombre_rol='admin'),
        ]
        db.session.add_all(roles)

    # Estados
    if not EstadoSolicitud.query.first():
        estados = [
            EstadoSolicitud(nombre_estado='Pendiente'),
            EstadoSolicitud(nombre_estado='En proceso'),
            EstadoSolicitud(nombre_estado='Resuelto'),
            EstadoSolicitud(nombre_estado='Cancelado'),
        ]
        db.session.add_all(estados)

    # Tipos de soporte
    if not TipoSoporte.query.first():
        tipos = [
            TipoSoporte(nombre_soporte='Mantenimiento de software'),
            TipoSoporte(nombre_soporte='Formateo de computadoras'),
            TipoSoporte(nombre_soporte='Instalación de sistema operativo'),
            TipoSoporte(nombre_soporte='Soporte de instalación de aplicaciones'),
            TipoSoporte(nombre_soporte='Otro'),
        ]
        db.session.add_all(tipos)

    db.session.commit()

    # Admin por defecto (solo si no existe)
    rol_admin = Rol.query.filter_by(nombre_rol='admin').first()
    if rol_admin and not User.query.filter_by(correo='admin@sast.com').first():
        admin = User(
            ncedula='0000000000',
            nombres='Administrador',
            apellidos='SAST',
            fecha_nacimiento=date(1990, 1, 1),
            numero_telefono='0000000000',
            correo='admin@sast.com',
            sector='Sistema',
            declaracion_veracidad=True,
            autorizacion_datos=True,
            id_rol=rol_admin.id_rol
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        print('[OK] Admin creado: admin@sast.com / Admin123!')
