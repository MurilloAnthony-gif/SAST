from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Rol
from datetime import datetime

auth_bp = Blueprint('auth', __name__, template_folder='templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('contrasena', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(correo=correo).first()

        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            flash(f'¡Bienvenido, {user.nombres}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return _redirect_by_role(user)
        else:
            flash('Correo o contraseña incorrectos. Inténtalo de nuevo.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        # Validar términos
        if not request.form.get('declaracion_veracidad'):
            flash('Debes aceptar la declaración de veracidad.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if not request.form.get('autorizacion_datos'):
            flash('Debes autorizar el tratamiento de datos.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        # Validar campos requeridos
        ncedula = request.form.get('ncedula', '').strip()
        nombres = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        fecha_nacimiento_str = request.form.get('fecha_nacimiento', '')
        numero_telefono = request.form.get('numero_telefono', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('contrasena', '')
        confirm_password = request.form.get('confirm_password', '')
        sector = request.form.get('sector', '').strip()

        # Validaciones
        if not all([ncedula, nombres, apellidos, fecha_nacimiento_str,
                    numero_telefono, correo, password, sector]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        # Verificar unicidad
        if User.query.filter_by(correo=correo).first():
            flash('Ya existe una cuenta con ese correo electrónico.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if User.query.filter_by(ncedula=ncedula).first():
            flash('Ya existe una cuenta con ese número de cédula.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        rol_solicitante = Rol.query.filter_by(nombre_rol='solicitante').first()
        if not rol_solicitante:
            flash('Error de configuración del sistema. Contacta al administrador.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        user = User(
            ncedula=ncedula,
            nombres=nombres.title(),
            apellidos=apellidos.title(),
            fecha_nacimiento=fecha_nacimiento,
            numero_telefono=numero_telefono,
            correo=correo,
            sector=sector,
            declaracion_veracidad=True,
            autorizacion_datos=True,
            id_rol=rol_solicitante.id_rol
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form_data={})


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role(user):
    if user.es_admin:
        return redirect(url_for('admin.dashboard'))
    elif user.es_tecnico:
        return redirect(url_for('tecnico.dashboard'))
    else:
        return redirect(url_for('solicitante.dashboard'))
