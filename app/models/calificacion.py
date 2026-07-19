from app.extensions import db
from datetime import datetime


class CalificacionTecnico(db.Model):
    __tablename__ = 'calificacion_tecnico'

    id_calificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitud = db.Column(db.Integer, db.ForeignKey('solicitudes.id_solicitud'), nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    puntuacion = db.Column(db.Integer, nullable=False)  # 1 a 5 estrellas
    comentario = db.Column(db.Text, nullable=True)
    fecha_calificacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Calificacion {self.puntuacion}★ para solicitud {self.id_solicitud}>'
