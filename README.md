# SAST — Sistema de Agendamiento de Servicio Técnico

Bienvenido al proyecto SAST, una plataforma web construida en Python (Flask) diseñada para gestionar solicitudes de servicio técnico de manera eficiente y en tiempo real. 

## 🚀 Tecnologías Principales

- **Backend:** Python 3.14 con Flask
- **Base de Datos:** SQLite (SQLAlchemy ORM)
- **Tiempo Real:** Flask-SocketIO (usando `threading` por compatibilidad)
- **Frontend:** HTML5, Jinja2, Vanilla CSS (Dark Mode & Glassmorphism), Bootstrap 5 (Grids y Utilidades)
- **Seguridad:** Werkzeug (Hashing), Flask-WTF (Protección CSRF)

---

## 🛠️ Cómo Iniciar el Proyecto Localmente

Abre tu consola o terminal (como PowerShell) y sigue estos pasos:

```powershell
# 1. Navegar a la carpeta del proyecto
cd "c:\Users\antho\OneDrive\Escritorio\SAST"

# 2. Configurar la codificación de caracteres para evitar errores en Windows
$env:PYTHONIOENCODING="utf-8"

# 3. Inicializar la Base de Datos (Solo es necesario la primera vez)
python -m flask --app "run:app" init-db

# 4. Correr el servidor
python run.py
```

Una vez que veas el mensaje de que el servidor está corriendo, abre tu navegador y entra a:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Credenciales de Prueba

Si ejecutaste el script `seed_demo.py` (o la inicialización de la BD), tienes estos usuarios disponibles:

| Rol | Correo | Contraseña | ¿Dónde ingresa? |
|-----|--------|------------|----------------|
| **Administrador** | `admin@sast.com` | `Admin123!` | `/admin/dashboard` |
| **Técnico** | `tecnico@sast.com` | `Tecnico123!` | `/tecnico/dashboard` |
| **Cliente** | `cliente@sast.com` | `Cliente123!` | `/solicitante/dashboard` |

---

## 📂 Estructura del Proyecto

Esta es la organización de los archivos para que no te pierdas:

```
SAST/
├── run.py                          # Punto de entrada principal para arrancar el servidor
├── seed_demo.py                    # Script opcional para crear usuarios de prueba
├── requirements.txt                # Lista de librerías y dependencias instaladas
├── .env                            # Variables de entorno (correo, contraseñas, etc.)
└── app/
    ├── __init__.py                 # Fábrica de la aplicación Flask (Configuración inicial)
    ├── config.py                   # Configuración de rutas y variables globales
    ├── extensions.py               # Inicialización de extensiones (db, socketio, mail)
    ├── sockets.py                  # Lógica del chat en tiempo real (SocketIO)
    ├── utils.py                    # Funciones de ayuda (guardar imágenes, validaciones)
    ├── models/                     # Modelos de la Base de Datos (Tablas)
    │   ├── user.py                 # Usuarios, Roles y Detalles de Técnicos
    │   ├── solicitud.py            # Solicitudes, Estados y Tipos de Soporte
    │   ├── mensaje.py              # Mensajes del chat
    │   ├── reporte.py              # Reportes técnicos (imágenes obligatorias)
    │   └── calificacion.py        # Calificaciones de los clientes
    ├── blueprints/                 # Controladores y Lógica de las páginas
    │   ├── auth/                   # Todo lo relacionado a Iniciar Sesión y Registro
    │   ├── solicitante/            # Páginas exclusivas para los Clientes
    │   ├── tecnico/                # Páginas exclusivas para los Técnicos
    │   └── admin/                  # Panel de Administración
    ├── templates/                  # Archivos HTML (Diseño de la página)
    │   ├── base.html               # Estructura principal, Menú de navegación (Navbar)
    │   ├── auth/, solicitante/, tecnico/, admin/  # Plantillas divididas por rol
    └── static/                     # Archivos públicos (CSS, JS, Imágenes)
        ├── css/main.css            # Archivo de estilos principales (Colores oscuros)
        ├── js/chat.js              # Lógica de Javascript para el chat
        ├── js/notifications.js     # Lógica para las notificaciones emergentes
        └── uploads/                # Aquí se guardan las imágenes subidas
```

---

## 🔁 Flujo de Trabajo del Sistema

El sistema está diseñado para funcionar de la siguiente manera:

1. **El Cliente** se registra, inicia sesión y crea una **Nueva Solicitud** detallando su problema.
2. La solicitud entra en estado **Pendiente**.
3. **El Administrador** revisa la solicitud en su panel y se la **Asigna** a un técnico disponible.
4. El estado cambia automáticamente a **En Proceso**.
5. **El Técnico** revisa su panel, ve la solicitud asignada y puede usar el **Chat** integrado para hablar con el cliente si necesita más detalles.
6. Una vez terminado el trabajo, el técnico llena el **Informe Técnico**, donde es **obligatorio subir 2 fotos** (cómo recibió y cómo entregó el equipo) y detallar la solución.
7. Al enviar el informe, el estado cambia a **Resuelto**.
8. **El Cliente** recibe una notificación en tiempo real indicando que su equipo está listo y puede calificar el servicio del 1 al 5.

---

## 🛠️ Notas Importantes y Mantenimiento

* **Imágenes de los reportes:** Se guardan físicamente en la carpeta `app/static/uploads/reportes/`.
* **SocketIO en Python 3.14:** Dado que la librería `eventlet` daba problemas en esta versión de Python, SocketIO está configurado para usar `async_mode='threading'`.
* **Correos Electrónicos:** El sistema está preparado para enviar correos (cuando un ticket se resuelve). Para que funcione, debes configurar las credenciales SMTP en el archivo `.env`.

¡Disfruta construyendo y mejorando tu proyecto SAST!
