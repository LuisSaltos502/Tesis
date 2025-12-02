from __future__ import annotations
from datetime import datetime
from typing import List
from sqlalchemy import Integer, String, DateTime, TIMESTAMP, SmallInteger, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base
from app.models.enums import UserRole

# Define la tabla de usuarios mapeando las configuraiones de la base

class usuarios(Base):
    __tablename__ = "usuarios"
    id_usuario:Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    nombre:Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    segundo_nombre:Mapped[str | None ] = mapped_column(
        String(50),
        nullable=True,
    )

    apellido:Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    segundo_apellido:Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    
    correo:Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
        index=True,
    )
    
    password_hash:Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    celular:Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        unique=True,
        index=True,
    )
    
    rol:Mapped[str] = mapped_column(
        SAEnum(UserRole, name="rol_usuario"),
        nullable=False,
    )
        
    creado_en:Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
    actualizado_en:Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
        
    
    
    estado_cuenta:Mapped[SmallInteger] = mapped_column(
        
        SmallInteger,
        nullable=False,
        default=1,
        
    )
    
    ultimo_inicio:Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Relaciones
    dispositivos:Mapped[List["dispositivos"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Usuario(id_usuario={self.id_usuario}, correo={self.correo})>"
