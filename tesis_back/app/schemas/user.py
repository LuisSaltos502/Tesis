from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.enums import UserRole


# -------------------------------------------------------------------
# Esquema base: lo que normalmente expones de un usuario
# -------------------------------------------------------------------
class UserBase(BaseModel):
    nombre: str
    segundo_nombre: str | None = None
    apellido: str
    segundo_apellido: str | None = None
    correo: EmailStr
    celular: str | None = None
    rol: UserRole
    estado_cuenta: int


# -------------------------------------------------------------------
# Lo que RECIBE la API cuando se crea un usuario
# (no heredamos de UserBase para no mezclar cosas de salida)
# -------------------------------------------------------------------
class UserCreate(BaseModel):
    nombre: str
    segundo_nombre: str | None = None
    apellido: str
    segundo_apellido: str | None = None
    correo: EmailStr
    celular: str | None = None
    password: str
    rol: UserRole
    class Config:
        # Para evitar que te manden campos raros que no existen
        extra = "forbid"


# -------------------------------------------------------------------
# Lo que DEVUELVE la API cuando quieres ver un usuario completo
# (incluye campos de auditoría)
# -------------------------------------------------------------------
class UserRead(UserBase):
    id_usuario: int
    creado_en: datetime
    actualizado_en: datetime
    ultimo_inicio: datetime | None = None

    class Config:
        # Para que pueda leer directamente desde modelos SQLAlchemy
        from_attributes = True


# -------------------------------------------------------------------
# Lo que RECIBE la API para actualizar un usuario (PATCH / PUT)
# Todos los campos son opcionales
# -------------------------------------------------------------------
class UserUpdate(BaseModel):
    nombre: str | None = None
    segundo_nombre: str | None = None
    apellido: str | None = None
    segundo_apellido: str | None = None
    correo: EmailStr | None = None
    celular: str | None = None
    rol: UserRole | None = None
    estado_cuenta: int | None = None
    password: str | None = None

    class Config:
        # Para evitar que te manden campos raros que no existen
        extra = "forbid"

# -------------------------------------------------------------------
# Esquema para token de login
# -------------------------------------------------------------------

class loginSchema(BaseModel):
    correo: EmailStr
    password: str
    class Config:
        # Para evitar que te manden campos raros que no existen
        extra = "forbid"
    
# -------------------------------------------------------------------
# Esquema para cambio de contraseña
# -------------------------------------------------------------------

class changePasswordSchema(BaseModel):
    current_password: str
    new_password: str
    class Config:
        # Para evitar que te manden campos raros que no existen
        extra = "forbid"