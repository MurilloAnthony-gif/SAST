from flask_socketio import join_room, leave_room, emit
from flask_login import current_user
from app.extensions import db
from app.models import Mensaje, Solicitud
from datetime import datetime


def register_socketio_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            # Unir al usuario a su sala personal para notificaciones
            join_room(f'user_{current_user.id_user}')

    @socketio.on('join_chat')
    def handle_join(data):
        """El usuario se une a la sala del chat de una solicitud."""
        solicitud_id = data.get('solicitud_id')
        if not solicitud_id:
            return

        solicitud = Solicitud.query.get(solicitud_id)
        if not solicitud:
            return

        # Verificar que el usuario tiene acceso a esta solicitud
        if (current_user.id_user == solicitud.id_cliente or
                current_user.id_user == solicitud.id_tecnico or
                current_user.es_admin):
            join_room(f'solicitud_{solicitud_id}')

            # Marcar mensajes como leídos
            mensajes_no_leidos = Mensaje.query.filter_by(
                id_solicitud=solicitud_id,
                leido=False
            ).filter(
                Mensaje.id_usuario_remitente != current_user.id_user
            ).all()

            for msg in mensajes_no_leidos:
                msg.leido = True
            db.session.commit()

    @socketio.on('leave_chat')
    def handle_leave(data):
        solicitud_id = data.get('solicitud_id')
        if solicitud_id:
            leave_room(f'solicitud_{solicitud_id}')

    @socketio.on('send_message')
    def handle_message(data):
        """Procesa y distribuye un mensaje en el chat."""
        solicitud_id = data.get('solicitud_id')
        contenido = data.get('contenido', '').strip()

        if not solicitud_id or not contenido:
            return

        solicitud = Solicitud.query.get(solicitud_id)
        if not solicitud:
            return

        # Verificar acceso
        if (current_user.id_user != solicitud.id_cliente and
                current_user.id_user != solicitud.id_tecnico and
                not current_user.es_admin):
            return

        # No se puede chatear si el ticket está resuelto o cancelado
        if solicitud.estado.nombre_estado in ['Resuelto', 'Cancelado']:
            emit('error', {'msg': 'No se puede enviar mensajes en un ticket cerrado.'})
            return

        # Guardar mensaje
        mensaje = Mensaje(
            id_solicitud=solicitud_id,
            id_usuario_remitente=current_user.id_user,
            contenido=contenido
        )
        db.session.add(mensaje)
        db.session.commit()

        # Emitir a todos en la sala
        emit('new_message', mensaje.to_dict(), room=f'solicitud_{solicitud_id}')

    @socketio.on('disconnect')
    def handle_disconnect():
        pass
