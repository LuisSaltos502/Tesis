from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.models.usuarios import usuarios
from app.models.dispositivos import dispositivos
from app.models.lectura import lectura

__all__ = ["dispositivos", "lectura", "usuarios"]
