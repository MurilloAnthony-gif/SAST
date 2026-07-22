"""
Servicio centralizado de correos electrónicos para SAST.
Todas las notificaciones del sistema pasan por aquí.
"""
from flask_mail import Message
from app.extensions import mail


# ──────────────────────────────────────────────────────────────
#  Colores y estilos compartidos
# ──────────────────────────────────────────────────────────────
_PRIMARY   = '#6d28d9'
_SUCCESS   = '#059669'
_INFO      = '#0284c7'
_WARNING   = '#d97706'
_BASE_URL  = 'http://127.0.0.1:5000'   # Cambiar a dominio real en producción


def _base_html(title: str, body_html: str, cta_text: str = None, cta_url: str = None, color: str = _PRIMARY) -> str:
    """Genera el HTML base con cabecera y pie de página para todos los correos."""
    cta_block = ''
    if cta_text and cta_url:
        cta_block = f'''
        <div style="text-align:center;margin:28px 0;">
            <a href="{cta_url}"
               style="background:{color};color:#ffffff;padding:13px 32px;border-radius:8px;
                      text-decoration:none;font-weight:600;font-size:15px;display:inline-block;">
                {cta_text}
            </a>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#1a1a2e;border-radius:16px;overflow:hidden;
                    border:1px solid rgba(255,255,255,0.08);">

        <!-- Cabecera -->
        <tr>
          <td style="background:linear-gradient(135deg,{color} 0%,#1e1b4b 100%);
                     padding:28px 32px;text-align:center;">
            <div style="font-size:26px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">
              ⚙ SAST
            </div>
            <div style="color:rgba(255,255,255,0.7);font-size:13px;margin-top:4px;">
              Sistema de Agendamiento de Servicio Técnico
            </div>
          </td>
        </tr>

        <!-- Cuerpo -->
        <tr>
          <td style="padding:32px 36px;color:#e2e8f0;font-size:15px;line-height:1.7;">
            <h2 style="color:#ffffff;margin:0 0 16px;font-size:20px;">{title}</h2>
            {body_html}
            {cta_block}
          </td>
        </tr>

        <!-- Pie -->
        <tr>
          <td style="padding:20px 36px;border-top:1px solid rgba(255,255,255,0.06);
                     color:rgba(255,255,255,0.35);font-size:12px;text-align:center;">
            Este es un correo automático, no lo respondas directamente.<br>
            &copy; 2025 SAST — Sistema de Agendamiento de Servicio Técnico Universitario
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>'''


def _send(subject: str, recipients: list, html: str) -> bool:
    """Envía el correo de forma segura. Nunca falla el flujo principal."""
    try:
        msg = Message(subject=f'[SAST] {subject}', recipients=recipients, html=html)
        mail.send(msg)
        return True
    except Exception as e:
        print(f'[EMAIL ERROR] {e}')
        return False


# ══════════════════════════════════════════════════════════════
#  1. Bienvenida al CLIENTE al registrarse
# ══════════════════════════════════════════════════════════════
def enviar_bienvenida_cliente(user):
    body = f'''
    <p>Hola <strong style="color:#a78bfa;">{user.nombres}</strong>,</p>
    <p>¡Tu cuenta en <strong>SAST</strong> ha sido creada exitosamente! 🎉</p>
    <p>Ya puedes iniciar sesión y crear tu primera solicitud de servicio técnico.</p>
    <table style="background:rgba(255,255,255,0.04);border-radius:10px;padding:16px 20px;
                  border:1px solid rgba(255,255,255,0.08);width:100%;margin:20px 0;">
      <tr><td style="color:#94a3b8;font-size:13px;">Correo registrado</td></tr>
      <tr><td style="color:#e2e8f0;font-weight:600;">{user.correo}</td></tr>
    </table>
    <p style="color:#94a3b8;font-size:13px;">
      Si no fuiste tú quien creó esta cuenta, contacta al administrador del sistema.
    </p>'''

    html = _base_html(
        title='¡Bienvenido a SAST!',
        body_html=body,
        cta_text='Ir al Sistema',
        cta_url=f'{_BASE_URL}/auth/login',
        color=_PRIMARY
    )
    _send('Bienvenido al sistema', [user.correo], html)


# ══════════════════════════════════════════════════════════════
#  2. Bienvenida al TÉCNICO cuando el admin le crea la cuenta
# ══════════════════════════════════════════════════════════════
def enviar_bienvenida_tecnico(tecnico, password_temporal: str):
    carrera = tecnico.detalles_tecnico.carrera if tecnico.detalles_tecnico and tecnico.detalles_tecnico.carrera else '—'
    body = f'''
    <p>Hola <strong style="color:#22d3ee;">{tecnico.nombres}</strong>,</p>
    <p>El administrador ha creado tu cuenta de <strong>técnico</strong> en el sistema SAST.
       Ya puedes acceder con las siguientes credenciales:</p>
    <table style="background:rgba(255,255,255,0.04);border-radius:10px;padding:20px 24px;
                  border:1px solid rgba(255,255,255,0.08);width:100%;margin:20px 0;border-collapse:collapse;">
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Correo</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{tecnico.correo}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Contraseña</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{password_temporal}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Carrera</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{carrera}</td>
      </tr>
    </table>
    <p style="color:#fcd34d;font-size:13px;">
      ⚠ Por seguridad, te recomendamos cambiar tu contraseña después de tu primer inicio de sesión.
    </p>'''

    html = _base_html(
        title='Tu cuenta de técnico está lista',
        body_html=body,
        cta_text='Iniciar Sesión',
        cta_url=f'{_BASE_URL}/auth/login',
        color='#0e7490'
    )
    _send('Cuenta de técnico creada', [tecnico.correo], html)


# ══════════════════════════════════════════════════════════════
#  3. Recuperación de contraseña
# ══════════════════════════════════════════════════════════════
def enviar_reseteo_contrasena(user, token: str):
    reset_url = f'{_BASE_URL}/auth/reset-password/{token}'
    body = f'''
    <p>Hola <strong style="color:#a78bfa;">{user.nombres}</strong>,</p>
    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
    <p>Haz clic en el botón de abajo para crear una nueva contraseña.
       Este enlace es válido por <strong>30 minutos</strong>.</p>
    <p style="color:#94a3b8;font-size:13px;margin-top:20px;">
      Si no solicitaste este cambio, puedes ignorar este correo — tu contraseña permanecerá sin cambios.
    </p>'''

    html = _base_html(
        title='Restablecer tu contraseña',
        body_html=body,
        cta_text='Restablecer Contraseña',
        cta_url=reset_url,
        color=_WARNING
    )
    _send('Restablecer contraseña', [user.correo], html)


# ══════════════════════════════════════════════════════════════
#  4. Notificación a ADMINS cuando se crea una solicitud
# ══════════════════════════════════════════════════════════════
def enviar_nueva_solicitud_admin(solicitud, admins: list):
    if not admins:
        return
    recipients = [a.correo for a in admins]
    cta_url = f'{_BASE_URL}/admin/solicitudes/{solicitud.id_solicitud}/asignar'

    body = f'''
    <p>Un cliente ha creado una nueva solicitud de soporte técnico que requiere ser asignada:</p>
    <table style="background:rgba(255,255,255,0.04);border-radius:10px;padding:20px 24px;
                  border:1px solid rgba(255,255,255,0.08);width:100%;margin:20px 0;border-collapse:collapse;">
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">ID Solicitud</td>
        <td style="color:#a78bfa;font-weight:700;padding:6px 0;">#{ solicitud.id_solicitud }</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Cliente</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.cliente.nombre_completo}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Tipo</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.tipo_soporte.nombre_soporte}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Fecha solicitada</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.fecha_atencion.strftime('%d/%m/%Y')}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Horario</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.horario_solicitado}</td>
      </tr>
    </table>
    <p style="color:#94a3b8;font-size:13px;">Descripción: {solicitud.descripcion[:200]}{'...' if len(solicitud.descripcion) > 200 else ''}</p>'''

    html = _base_html(
        title=f'Nueva solicitud #{solicitud.id_solicitud} — Requiere asignación',
        body_html=body,
        cta_text='Asignar Técnico',
        cta_url=cta_url,
        color=_PRIMARY
    )
    _send(f'Nueva solicitud #{solicitud.id_solicitud} de {solicitud.cliente.nombre_completo}', recipients, html)


# ══════════════════════════════════════════════════════════════
#  5. Notificación al CLIENTE cuando se le asigna un técnico
# ══════════════════════════════════════════════════════════════
def enviar_tecnico_asignado_cliente(solicitud):
    cta_url = f'{_BASE_URL}/solicitante/solicitud/{solicitud.id_solicitud}'
    body = f'''
    <p>Hola <strong style="color:#a78bfa;">{solicitud.cliente.nombres}</strong>,</p>
    <p>¡Buenas noticias! Un técnico ha sido asignado a tu solicitud de soporte.</p>
    <table style="background:rgba(255,255,255,0.04);border-radius:10px;padding:20px 24px;
                  border:1px solid rgba(255,255,255,0.08);width:100%;margin:20px 0;border-collapse:collapse;">
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Solicitud</td>
        <td style="color:#a78bfa;font-weight:700;padding:6px 0;">#{solicitud.id_solicitud} — {solicitud.tipo_soporte.nombre_soporte}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Técnico asignado</td>
        <td style="color:#22d3ee;font-weight:600;padding:6px 0;">{solicitud.tecnico.nombre_completo}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Fecha de atención</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.fecha_atencion.strftime('%d/%m/%Y')}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Horario</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.horario_solicitado}</td>
      </tr>
    </table>
    <p>Puedes usar el chat del sistema para comunicarte directamente con el técnico.</p>'''

    html = _base_html(
        title='¡Tu técnico ha sido asignado!',
        body_html=body,
        cta_text='Ver mi Solicitud',
        cta_url=cta_url,
        color=_PRIMARY
    )
    _send(f'Técnico asignado a tu solicitud #{solicitud.id_solicitud}', [solicitud.cliente.correo], html)


# ══════════════════════════════════════════════════════════════
#  6. Notificación al TÉCNICO cuando se le asigna una solicitud
# ══════════════════════════════════════════════════════════════
def enviar_solicitud_asignada_tecnico(solicitud):
    cta_url = f'{_BASE_URL}/tecnico/solicitud/{solicitud.id_solicitud}'
    body = f'''
    <p>Hola <strong style="color:#22d3ee;">{solicitud.tecnico.nombres}</strong>,</p>
    <p>El administrador te ha asignado una nueva solicitud de soporte técnico.</p>
    <table style="background:rgba(255,255,255,0.04);border-radius:10px;padding:20px 24px;
                  border:1px solid rgba(255,255,255,0.08);width:100%;margin:20px 0;border-collapse:collapse;">
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">ID Solicitud</td>
        <td style="color:#a78bfa;font-weight:700;padding:6px 0;">#{solicitud.id_solicitud}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Tipo de servicio</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.tipo_soporte.nombre_soporte}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Cliente</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.cliente.nombre_completo}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Teléfono cliente</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.cliente.numero_telefono}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Sector</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.cliente.sector}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Fecha de atención</td>
        <td style="color:#fcd34d;font-weight:600;padding:6px 0;">{solicitud.fecha_atencion.strftime('%d/%m/%Y')}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Horario</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.horario_solicitado}</td>
      </tr>
    </table>
    <p style="color:#94a3b8;font-size:13px;">Descripción: {solicitud.descripcion[:300]}{'...' if len(solicitud.descripcion) > 300 else ''}</p>'''

    html = _base_html(
        title=f'Nueva solicitud #{solicitud.id_solicitud} asignada',
        body_html=body,
        cta_text='Ver Solicitud',
        cta_url=cta_url,
        color='#0e7490'
    )
    _send(f'Nueva solicitud #{solicitud.id_solicitud} asignada a ti', [solicitud.tecnico.correo], html)


# ══════════════════════════════════════════════════════════════
#  7. Notificación al CLIENTE cuando el técnico completa el trabajo
# ══════════════════════════════════════════════════════════════
def enviar_solicitud_resuelta_cliente(solicitud):
    cta_url = f'{_BASE_URL}/solicitante/solicitud/{solicitud.id_solicitud}/calificar'
    body = f'''
    <p>Hola <strong style="color:#a78bfa;">{solicitud.cliente.nombres}</strong>,</p>
    <p>¡Tu solicitud de soporte técnico ha sido completada exitosamente! 🎉</p>
    <table style="background:rgba(255,255,255,0.04);border-radius:10px;padding:20px 24px;
                  border:1px solid rgba(255,255,255,0.08);width:100%;margin:20px 0;border-collapse:collapse;">
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Solicitud</td>
        <td style="color:#a78bfa;font-weight:700;padding:6px 0;">#{solicitud.id_solicitud} — {solicitud.tipo_soporte.nombre_soporte}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Técnico</td>
        <td style="color:#22d3ee;font-weight:600;padding:6px 0;">{solicitud.tecnico.nombre_completo}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Estado</td>
        <td style="color:#4ade80;font-weight:700;padding:6px 0;">✔ Resuelto</td>
      </tr>
    </table>
    <p>Por favor tómate un momento para <strong>calificar el servicio recibido</strong>.
       Tu opinión nos ayuda a mejorar.</p>'''

    html = _base_html(
        title='¡Tu solicitud ha sido resuelta!',
        body_html=body,
        cta_text='Calificar el Servicio ⭐',
        cta_url=cta_url,
        color=_SUCCESS
    )
    _send(f'Solicitud #{solicitud.id_solicitud} completada', [solicitud.cliente.correo], html)


# ══════════════════════════════════════════════════════════════
#  8. Notificación a ADMINS cuando el técnico completa el trabajo
# ══════════════════════════════════════════════════════════════
def enviar_solicitud_resuelta_admin(solicitud, admins: list):
    if not admins:
        return
    recipients = [a.correo for a in admins]
    cta_url = f'{_BASE_URL}/admin/solicitudes/{solicitud.id_solicitud}'

    body = f'''
    <p>El técnico <strong style="color:#22d3ee;">{solicitud.tecnico.nombre_completo}</strong>
       ha completado y cerrado una solicitud de soporte.</p>
    <table style="background:rgba(255,255,255,0.04);border-radius:10px;padding:20px 24px;
                  border:1px solid rgba(255,255,255,0.08);width:100%;margin:20px 0;border-collapse:collapse;">
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">ID Solicitud</td>
        <td style="color:#a78bfa;font-weight:700;padding:6px 0;">#{solicitud.id_solicitud}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Tipo</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.tipo_soporte.nombre_soporte}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Cliente</td>
        <td style="color:#e2e8f0;font-weight:600;padding:6px 0;">{solicitud.cliente.nombre_completo}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Técnico</td>
        <td style="color:#22d3ee;font-weight:600;padding:6px 0;">{solicitud.tecnico.nombre_completo}</td>
      </tr>
      <tr>
        <td style="color:#94a3b8;font-size:13px;padding:6px 0;">Estado</td>
        <td style="color:#4ade80;font-weight:700;padding:6px 0;">✔ Resuelto</td>
      </tr>
    </table>'''

    html = _base_html(
        title=f'Solicitud #{solicitud.id_solicitud} completada por técnico',
        body_html=body,
        cta_text='Ver Detalle',
        cta_url=cta_url,
        color=_SUCCESS
    )
    _send(f'Solicitud #{solicitud.id_solicitud} resuelta por {solicitud.tecnico.nombre_completo}', recipients, html)
