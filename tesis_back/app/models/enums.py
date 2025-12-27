from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    usuario = "usuario"
    operador = "operador"
    
class DeviceRole(str, Enum):
    sensor = "prototipo_esp32"
    gateway = "raspberry_pi_gateway"

class OrigenRole(str, Enum):
    simulado = "simulado"
    real = "fisico"