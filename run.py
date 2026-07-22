from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    print('🚀 Iniciando SAST — Sistema de Agendamiento de Servicio Técnico')
    print('📍 URL: http://127.0.0.1:5000')
    print('---')
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        allow_unsafe_werkzeug=True
    )
