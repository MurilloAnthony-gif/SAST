# SAST — Sistema de Agendamiento de Servicio Técnico

Bienvenido al proyecto SAST, una plataforma web construida en Python (Flask) diseñada para gestionar solicitudes de servicio técnico de manera eficiente y en tiempo real. 

Este proyecto fue estructurado especialmente para la **Universidad Técnica de Manabí (UTM)**, enfocado en el manejo de soporte técnico para sus distintas ubicaciones (sectores).

---

## 🚀 Tecnologías Principales

- **Backend:** Python (Flask)
- **Base de Datos (Local):** SQLite (SQLAlchemy ORM)
- **Base de Datos (Producción):** PostgreSQL (psycopg2)
- **Tiempo Real:** Flask-SocketIO (usando Gevent-WebSocket para producción)
- **Generación de PDF:** ReportLab
- **Frontend:** HTML5, Jinja2, Vanilla CSS (Dark Mode & Glassmorphism), Bootstrap 5 (Grids y Utilidades)
- **Despliegue (Nube):** Gunicorn & Render.com

---

## ☁️ Producción (Render.com)

El sistema está configurado para ser desplegado fácilmente en **Render.com** utilizando una base de datos PostgreSQL.

### Credenciales del Administrador (Producción)
Al ejecutar el comando de inicialización de base de datos en la nube (`flask init-db`), se creará automáticamente el siguiente usuario administrador predeterminado:

- **Correo:** `sastutm@gmail.com`
- **Contraseña:** `Sast20260722JARJ`

### Comando de Arranque (Render Start Command)
En la configuración del Web Service en Render, asegúrate de utilizar el siguiente comando de inicio para garantizar el correcto funcionamiento del chat en tiempo real:
```bash
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 app:create_app()
```

---

## 🛠️ Cómo Iniciar el Proyecto Localmente (Desarrollo)

Abre tu consola o terminal y sigue estos pasos:

```powershell
# 1. Configurar la codificación de caracteres para evitar errores en Windows
$env:PYTHONIOENCODING="utf-8"

# 2. Inicializar la Base de Datos (Solo es necesario la primera vez)
# Esto creará las tablas, ubicaciones base (sectores de la UTM) y el administrador.
python -m flask --app "run:app" init-db

# 3. Correr el servidor de desarrollo
python run.py
```

Una vez que veas el mensaje de que el servidor está corriendo, abre tu navegador y entra a:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📂 Estructura del Proyecto

Esta es la organización principal de los archivos:

```text
SAST/
├── run.py                          # Punto de entrada principal para arrancar el servidor local
├── requirements.txt                # Dependencias de Python (Flask, Gunicorn, psycopg2, etc.)
├── .env                            # Variables de entorno (DATABASE_URL, SECRET_KEY)
└── app/
    ├── __init__.py                 # Fábrica de la aplicación Flask y lógica init-db
    ├── config.py                   # Configuración de variables globales e interceptor de Postgres
    ├── extensions.py               # Instancias compartidas (db, socketio, mail)
    ├── pdf_generator.py            # Lógica para la generación de reportes e informes en PDF
    ├── sockets.py                  # Lógica del chat en tiempo real (SocketIO)
    ├── utils.py                    # Funciones útiles para subir archivos y manejo general
    ├── models/                     # Modelos de la Base de Datos (Tablas)
    │   ├── user.py                 # Usuarios, Roles y Detalles
    │   ├── solicitud.py            # Solicitudes y Estados
    │   ├── mensaje.py              # Mensajes del chat
    │   ├── reporte.py              # Informes técnicos (imágenes obligatorias)
    │   └── sector.py               # Ubicaciones (Sistemas, Biblioteca, etc.)
    ├── blueprints/                 # Controladores por tipo de usuario
    │   ├── auth/                   # Autenticación (Login / Registro)
    │   ├── solicitante/            # Funciones de Clientes (Crear tickets, ver PDF sin firmas)
    │   ├── tecnico/                # Funciones de Técnicos (Responder tickets, crear reporte)
    │   └── admin/                  # Dashboard, gestión de roles y asignación por ubicación
    ├── templates/                  # Interfaz gráfica (HTML + Jinja2)
    └── static/                     # Archivos públicos (CSS, JS, Imágenes)
```

---

## 🔁 Flujo de Trabajo del Sistema

1. **El Cliente** se registra, inicia sesión y crea una **Nueva Solicitud**.
2. La solicitud entra en estado **Pendiente**.
3. **El Administrador** revisa la solicitud en su panel y, observando la **Ubicación (Sector)** del problema, se la **Asigna** al técnico que esté más cerca o disponible en esa misma ubicación.
4. El estado cambia automáticamente a **En Proceso**.
5. **El Técnico** puede usar el **Chat** integrado para conversar con el cliente o el administrador.
6. Una vez terminado el trabajo, el técnico genera el **Informe Técnico**, detallando la solución y subiendo **fotos de evidencia** (recepción y entrega).
7. Al enviar el informe, el estado cambia a **Resuelto**.
8. **El Cliente** puede descargar su informe en **PDF** (versión limpia, sin firmas ni fotos de evidencia internas) y calificar el servicio del 1 al 5. El Administrador o Técnico pueden descargar el PDF completo con firmas digitales e imágenes.
