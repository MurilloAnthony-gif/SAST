from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
import secrets


class Rol(db.Model):
    __tablename__ = 'roles'

    id_rol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_rol = db.Column(db.String(50), nullable=False)

    usuarios = db.relationship('User', backref='rol', lazy=True)

    def __repr__(self):
        return f'<Rol {self.nombre_rol}>'


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id_user = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ncedula = db.Column('Ncedula', db.String(20), nullable=False, unique=True)
    nombres = db.Column('Nombres', db.String(100), nullable=False)
    apellidos = db.Column('Apellidos', db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    numero_telefono = db.Column(db.String(20), nullable=False)
    correo = db.Column('Correo', db.String(150), nullable=False, unique=True)
    contrasena = db.Column(db.String(255), nullable=False)
    sector = db.Column('Sector', db.String(100), nullable=False)

    declaracion_veracidad = db.Column(db.Boolean, default=False)
    autorizacion_datos = db.Column(db.Boolean, default=False)

    # Recuperación de contraseña
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)

    # Relaciones
    solicitudes_como_cliente = db.relationship(
        'Solicitud', foreign_keys='Solicitud.id_cliente',
        backref='cliente', lazy='dynamic'
    )
    solicitudes_como_tecnico = db.relationship(
        'Solicitud', foreign_keys='Solicitud.id_tecnico',
        backref='tecnico', lazy='dynamic'
    )
    mensajes_enviados = db.relationship('Mensaje', backref='remitente', lazy='dynamic')
    reportes = db.relationship('Reporte', backref='tecnico_reporte', lazy='dynamic')
    calificaciones_dadas = db.relationship('CalificacionTecnico', backref='cliente_calificador', lazy='dynamic')
    detalles_tecnico = db.relationship('DetallesTecnico', backref='tecnico_detalle', uselist=False)

    def get_id(self):
        return str(self.id_user)

    def set_password(self, password):
        self.contrasena = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasena, password)

    def generar_reset_token(self, expiry_minutes: int = 30):
        """Genera un token seguro para reseteo de contraseña."""
        from datetime import timedelta
        self.reset_token = secrets.token_urlsafe(48)
        self.reset_token_expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        return self.reset_token

    def reset_token_valido(self) -> bool:
        """Verifica si el token existe y no ha expirado."""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        return datetime.utcnow() < self.reset_token_expiry

    def limpiar_reset_token(self):
        """Limpia el token después de usarlo."""
        self.reset_token = None
        self.reset_token_expiry = None

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def es_admin(self):
        return self.rol.nombre_rol == 'admin'

    @property
    def es_tecnico(self):
        return self.rol.nombre_rol == 'técnico'

    @property
    def es_solicitante(self):
        return self.rol.nombre_rol == 'solicitante'

    def __repr__(self):
        return f'<User {self.correo}>'


class DetallesTecnico(db.Model):
    __tablename__ = 'detalles_tecnico'

    id_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_tecnico = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    carrera = db.Column(db.String(100))
    semestre = db.Column(db.Integer)

    def __repr__(self):
        return f'<DetallesTecnico tecnico={self.id_tecnico}>'
