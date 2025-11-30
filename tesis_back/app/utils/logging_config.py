import logging
import logging.config
from pathlib import Path

# Carpeta donde se guardarán los logs (tesis_back/logs)
LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def configure_logging() -> None:
    """
    Configura el sistema de logs para toda la API.
    - Consola (nivel INFO)
    - Archivo logs/app.log (nivel DEBUG)
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": str(LOGS_DIR / "app.log"),
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(logging_config)
