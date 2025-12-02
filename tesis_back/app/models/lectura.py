from __future__ import annotations
from datetime import datetime
from sqlalchemy import BigInteger, TIMESTAMP, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base
from app.models.dispositivos import dispositivos

class lectura(Base):
    __tablename__ = "lectura"
    
    id_lectura: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    id_dispositivo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dispositivos.id_dispositivo"),
        nullable=False,
        index=True,
    )
    fecha_de_medicion: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
    )
    
    # En el Workbench se ve DECIMAL(10,0); si cambias precisión,
    # ajusta estos Numeric.

    valor_ph: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    valor_turbidez: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    valor_temperatura: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    valor_conductividad: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    
    #relaciones

    dispositivo: Mapped[dispositivos] = relationship(
        "dispositivos",
        back_populates="lecturas",
    )
    
    def __repr__(self) -> str:
        return f"<lectura(id_lectura={self.id_lectura}, id_dispositivo={self.id_dispositivo}, fecha_de_medicion={self.fecha_de_medicion}, valor_ph={self.valor_ph}, valor_turbidez={self.valor_turbidez}, valor_temperatura={self.valor_temperatura}, valor_conductividad={self.valor_conductividad})>"
    
