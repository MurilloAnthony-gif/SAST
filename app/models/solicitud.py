from app.extensions import db
from datetime import datetime


class EstadoSolicitud(db.Model):
    __tablename__ = 'estado_solicitudes'

    id_estado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_estado = db.Column(db.String(50), nullable=False)

    solicitudes = db.relationship('Solicitud', backref='estado', lazy=True)

    def __repr__(self):
        return f'<EstadoSolicitud {self.nombre_estado}>'


class TipoSoporte(db.Model):
    __tablename__ = 'tipo_soportes'

    id_tipo_soporte = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_soporte = db.Column(db.String(100), nullable=False)

    solicitudes = db.relationship('Solicitud', backref='tipo_soporte', lazy=True)

    def __repr__(self):
        return f'<TipoSoporte {self.nombre_soporte}>'


class Solicitud(db.Model):
    __tablename__ = 'solicitudes'

    id_solicitud = db.Column(db.Integer, primary_key=True, autoincrement=True)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_atencion = db.Column(db.Date, nullable=False)
    horario_solicitado = db.Column(db.String(50), nullable=False)
    recursos_adicionales = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    id_cliente = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    id_tecnico = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=True)
    id_estado = db.Column(db.Integer, db.ForeignKey('estado_solicitudes.id_estado'), nullable=False)
    id_tipo_soporte = db.Column(db.Integer, db.ForeignKey('tipo_soportes.id_tipo_soporte'), nullable=False)

    # Relaciones
    mensajes = db.relationship('Mensaje', backref='solicitud', lazy='dynamic', cascade='all, delete-orphan')
    reporte = db.relationship('Reporte', backref='solicitud', uselist=False, cascade='all, delete-orphan')
    calificacion = db.relationship('CalificacionTecnico', backref='solicitud', uselist=False, cascade='all, delete-orphan')

    @property
    def mensajes_no_leidos(self):
        """Retorna el total de mensajes no leídos en esta solicitud."""
        return self.mensajes.filter_by(leido=False).count()

    def __repr__(self):
        return f'<Solicitud {self.id_solicitud} - {self.estado.nombre_estado}>'
