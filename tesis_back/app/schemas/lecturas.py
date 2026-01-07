from datetime import datetime
from pydantic import BaseModel

# -------------------------------------------------------------------
# Esquema base: campos comunes de la lectura
# -------------------------------------------------------------------
class LecturaBaseMQTT(BaseModel):

    ph: float
    temperatura: float
    turbidez: float
    tds: float
    class Config:
        # Para evitar que te manden campos raros que no existen
        extra = "forbid"
    
# -------------------------------------------------------------------
# Valores a ingresar a la base de datos
class LecturaBaseMSQL(BaseModel):
    id_dispositivo: int
    valor_ph: float
    valor_temperatura: float
    valor_turbidez: float
    valor_conductividad: float
    class Config:
        # Para evitar que te manden campos raros que no existen
        extra = "forbid"