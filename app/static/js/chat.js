/**
 * SAST — Chat en tiempo real con Flask-SocketIO
 */

class SastChat {
    constructor(solicitudId, currentUserId, isClosed) {
        this.solicitudId = solicitudId;
        this.currentUserId = currentUserId;
        this.isClosed = isClosed;
        this.socket = null;
        this.init();
    }

    init() {
        this.socket = io();
        this.bindElements();
        this.joinRoom();
        this.registerEvents();
        this.scrollToBottom();
    }

    bindElements() {
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.messagesContainer = document.getElementById('chatMessages');
    }

    joinRoom() {
        this.socket.on('connect', () => {
            this.socket.emit('join_chat', { solicitud_id: this.solicitudId });
        });
    }

    registerEvents() {
        // Recibir mensajes
        this.socket.on('new_message', (data) => {
            this.appendMessage(data);
            this.scrollToBottom();
        });

        this.socket.on('error', (data) => {
            alert(data.msg);
        });

        // Enviar con botón
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Enviar con Enter (Shift+Enter para nueva línea)
        if (this.chatInput) {
            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize textarea
            this.chatInput.addEventListener('input', () => {
                this.chatInput.style.height = 'auto';
                this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 100) + 'px';
            });
        }
    }

    sendMessage() {
        if (this.isClosed) {
            alert('No puedes enviar mensajes en un ticket cerrado.');
            return;
        }

        const content = this.chatInput.value.trim();
        if (!content) return;

        this.sendBtn.disabled = true;
        this.sendBtn.innerHTML = '<i class="bi bi-hourglass-split spin"></i>';

        this.socket.emit('send_message', {
            solicitud_id: this.solicitudId,
            contenido: content
        });

        this.chatInput.value = '';
        this.chatInput.style.height = 'auto';

        setTimeout(() => {
            this.sendBtn.disabled = false;
            this.sendBtn.innerHTML = '<i class="bi bi-send-fill"></i>';
        }, 500);
    }

    appendMessage(data) {
        const isMine = data.id_remitente === this.currentUserId;
        const div = document.createElement('div');
        div.className = `d-flex flex-column ${isMine ? 'align-items-end' : 'align-items-start'}`;
        div.innerHTML = `
            ${!isMine ? `<span class="msg-meta mb-1">${data.remitente}</span>` : ''}
            <div class="msg-bubble ${isMine ? 'msg-mine' : 'msg-other'}">
                ${this.escapeHTML(data.contenido)}
                ${data.archivo_adjunto ? `<br><a href="/static/${data.archivo_adjunto}" target="_blank" class="text-white-50 small"><i class="bi bi-paperclip"></i> Adjunto</a>` : ''}
            </div>
            <span class="msg-meta mt-1">${data.fecha_envio}</span>
        `;
        this.messagesContainer.appendChild(div);
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }
}
