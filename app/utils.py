import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions=None):
    """Verifica si la extensión del archivo está permitida."""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_file(file, subfolder=''):
    """
    Guarda un archivo en la carpeta de uploads con nombre único.
    Retorna la ruta relativa desde static/.
    """
    if not file or not file.filename:
        return None

    upload_base = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
    upload_dir = os.path.join(upload_base, subfolder) if subfolder else upload_base
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'bin'
    unique_filename = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)

    # Retorna ruta relativa para usar en url_for('static', filename=...)
    rel_path = os.path.join('uploads', subfolder, unique_filename).replace('\\', '/')
    return rel_path


def format_date(value, fmt='%d/%m/%Y'):
    """Formatea una fecha para mostrarla en templates."""
    if value is None:
        return ''
    return value.strftime(fmt)
