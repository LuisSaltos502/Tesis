from __future__ import annotations
from datetime import datetime
from typing import List
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    DateTime,
    TIMESTAMP,
    SmallInteger,
    Numeric,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base

class dispositivos(Base):
    __tablename__ = "dispositivos"
    
    id_dispositivo: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    
    id_usuario: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario"),
        nullable=False,
        index=True,
    )
    
    id_padre: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("dispositivos.id_dispositivo"),
        nullable=True,
    )
    
    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    # En la base este campo se encuentra como enum
    rol_dispositivo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    origen: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    mac: Mapped[str] = mapped_column(
        String(17),
        nullable=False,
        unique=True,
        index=True,
    )
    
    ubicacion_texto: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    latitud: Mapped[float | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )
    longitud: Mapped[float | None] = mapped_column(
        Numeric(9, 6),  
        nullable=True,
    )
    estado_dispositivo: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
    )
    ultimo_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
    device_key: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Relaciones
    usuario: Mapped["usuarios"] = relationship(
        back_populates="dispositivos",
    )
    
    padre: Mapped["dispositivos | None"] = relationship(
        "dispositivos",
        remote_side="dispositivos.id_dispositivo",
        back_populates="hijos",
    )
    hijos: Mapped[List["dispositivos"]] = relationship(
        "dispositivos",
        back_populates="padre",
    )
    lecturas: Mapped[List["lectura"]] = relationship(
        "lectura",
        back_populates="dispositivo",
        cascade="all, delete-orphan",
    )
    def __repr__(self) -> str:
        return f"<Dispositivo(id_dispositivo={self.id_dispositivo}, nombre={self.nombre}, mac={self.mac!r})>"
