from datetime import datetime
from pydantic import BaseModel
from app.models.enums import DeviceRole, OrigenRole


# -------------------------------------------------------------------
# Esquema base: campos comunes del dispositivo
# -------------------------------------------------------------------
class DispositivoBase(BaseModel):
    nombre: str
    rol_dispositivo: DeviceRole
    origen: OrigenRole
    estado_dispositivo: int = 1
    ubicacion_texto: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    ultimo_heartbeat: datetime | None = None


# -------------------------------------------------------------------
# Lo que RECIBE la API cuando se crea un dispositivo
# -------------------------------------------------------------------
class DispositivoCreate(BaseModel):
    nombre: str
    mac: str
    rol_dispositivo: DeviceRole
    origen: OrigenRole
    id_usuario: int | None = None
    ubicacion_texto: str | None = None
    latitud: float | None = None
    longitud: float | None = None


# -------------------------------------------------------------------
# Lo que RECIBE la API al actualizar un dispositivo
# -------------------------------------------------------------------
class DispositivoUpdate(BaseModel):
    nombre: str | None = None
    rol_dispositivo: DeviceRole | None = None
    origen: OrigenRole | None = None
    estado_dispositivo: int | None = None
    id_usuario: int | None = None
    ubicacion_texto: str | None = None
    latitud: float | None = None
    longitud: float | None = None

    class Config:
        extra = "forbid"


# -------------------------------------------------------------------
# Lo que DEVUELVE la API al consultar un dispositivo
# -------------------------------------------------------------------
class DispositivoRead(DispositivoBase):
    id_dispositivo: int
    id_usuario: int
    mac: str
    device_key: str
    fecha_de_instalacion: datetime
    fecha_de_actualizacion: datetime

    class Config:
        from_attributes = True
