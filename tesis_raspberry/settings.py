from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    MQTT_B1_HOST: str
    MQTT_B1_PORT: int
    MQTT_B2_HOST: str
    MQTT_B2_PORT: int
    MQTT_TOPIC_SUB: str

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
    )