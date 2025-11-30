from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    
    #Base de datos
    DB_HOST: str 
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    #MQTT
    MQTT_BROKER: str
    MQTT_PORT: int
    MQTT_USER: str
    MQTT_PASSWORD: str
    MQTT_TOPIC: str
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
    )

settings = Settings()
