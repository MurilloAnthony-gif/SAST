from app.extensions import db
from datetime import datetime


class Reporte(db.Model):
    __tablename__ = 'reportes'

    id_reporte = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitud = db.Column(db.Integer, db.ForeignKey('solicitudes.id_solicitud'), nullable=False)
    id_tecnico = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    descripcion_trabajo = db.Column(db.Text, nullable=False)
    imagen_evidencia_1 = db.Column(db.String(255), nullable=False)  # Obligatorio: cómo recibió
    imagen_evidencia_2 = db.Column(db.String(255), nullable=False)  # Obligatorio: cómo entregó
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reporte {self.id_reporte} para solicitud {self.id_solicitud}>'
