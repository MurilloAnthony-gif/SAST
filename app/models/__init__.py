from app.models.user import User, Rol, DetallesTecnico
from app.models.solicitud import Solicitud, EstadoSolicitud, TipoSoporte
from app.models.mensaje import Mensaje
from app.models.reporte import Reporte
from app.models.calificacion import CalificacionTecnico
from app.models.sector import Sector

__all__ = [
    'User', 'Rol', 'DetallesTecnico',
    'Solicitud', 'EstadoSolicitud', 'TipoSoporte',
    'Mensaje',
    'Reporte',
    'CalificacionTecnico',
    'Sector'
]
