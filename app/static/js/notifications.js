/**
 * SAST — Notificaciones en tiempo real (SocketIO)
 */

function showToast(message) {
    const toastEl = document.getElementById('liveToast');
    const toastMsg = document.getElementById('toastMessage');
    if (!toastEl || !toastMsg) return;

    toastMsg.textContent = message;
    const toast = new bootstrap.Toast(toastEl, { delay: 6000 });
    toast.show();
}

// Auto-cerrar flash alerts después de 5 segundos
document.addEventListener('DOMContentLoaded', () => {
    const flashAlerts = document.querySelectorAll('.flash-alert');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Navbar scroll effect
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 10) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
});
