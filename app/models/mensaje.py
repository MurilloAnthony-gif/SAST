from app.extensions import db
from datetime import datetime


class Mensaje(db.Model):
    __tablename__ = 'mensajes'

    id_mensaje = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitud = db.Column(db.Integer, db.ForeignKey('solicitudes.id_solicitud'), nullable=False)
    id_usuario_remitente = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    archivo_adjunto = db.Column(db.String(255), nullable=True)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    leido = db.Column(db.Boolean, default=False)
    canal = db.Column(db.String(20), default='publico', nullable=False)
    # canal: 'publico' = cliente<->tecnico | 'interno' = admin<->tecnico

    def to_dict(self):
        return {
            'id': self.id_mensaje,
            'contenido': self.contenido,
            'archivo_adjunto': self.archivo_adjunto,
            'fecha_envio': self.fecha_envio.strftime('%d/%m/%Y %H:%M'),
            'remitente': self.remitente.nombre_completo,
            'id_remitente': self.id_usuario_remitente,
            'leido': self.leido,
            'canal': self.canal
        }

    def __repr__(self):
        return f'<Mensaje {self.id_mensaje} en solicitud {self.id_solicitud}>'
