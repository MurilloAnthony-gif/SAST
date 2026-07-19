"""
Script para crear usuario cliente y técnico de prueba en SAST.
Ejecutar con: python seed_demo.py
"""
from app import create_app
from app.extensions import db
from app.models import User, Rol, DetallesTecnico
from datetime import date

app = create_app()

with app.app_context():
    rol_sol = Rol.query.filter_by(nombre_rol='solicitante').first()
    rol_tec = Rol.query.filter_by(nombre_rol='técnico').first()

    # ── CLIENTE BASE ──────────────────────────────────────────
    if not User.query.filter_by(correo='cliente@sast.com').first():
        cliente = User(
            ncedula='1111111111',
            nombres='Carlos',
            apellidos='Ramirez',
            fecha_nacimiento=date(1995, 6, 15),
            numero_telefono='3001234567',
            correo='cliente@sast.com',
            sector='Centro',
            declaracion_veracidad=True,
            autorizacion_datos=True,
            id_rol=rol_sol.id_rol
        )
        cliente.set_password('Cliente123!')
        db.session.add(cliente)
        print('[OK] Cliente creado: cliente@sast.com / Cliente123!')
    else:
        print('[--] Cliente ya existe.')

    # ── TECNICO BASE ──────────────────────────────────────────
    if not User.query.filter_by(correo='tecnico@sast.com').first():
        tecnico = User(
            ncedula='2222222222',
            nombres='Maria',
            apellidos='Lopez',
            fecha_nacimiento=date(1998, 3, 20),
            numero_telefono='3109876543',
            correo='tecnico@sast.com',
            sector='Norte',
            declaracion_veracidad=True,
            autorizacion_datos=True,
            id_rol=rol_tec.id_rol
        )
        tecnico.set_password('Tecnico123!')
        db.session.add(tecnico)
        db.session.flush()  # obtener id_user antes del commit

        detalles = DetallesTecnico(
            id_tecnico=tecnico.id_user,
            carrera='Ingeniería de Sistemas',
            semestre=7
        )
        db.session.add(detalles)
        print('[OK] Tecnico creado:  tecnico@sast.com  / Tecnico123!')
    else:
        print('[--] Tecnico ya existe.')

    db.session.commit()
    print()
    print('============================================')
    print('  Usuarios de prueba listos')
    print('  Admin:    admin@sast.com    / Admin123!')
    print('  Cliente:  cliente@sast.com  / Cliente123!')
    print('  Tecnico:  tecnico@sast.com  / Tecnico123!')
    print('  URL: http://127.0.0.1:5000')
    print('============================================')
