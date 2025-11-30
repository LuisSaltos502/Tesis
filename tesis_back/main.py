import logging
from fastapi import FastAPI, Depends
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings, settings
from app.database.session import get_db_session
from app.utils.logging_config import configure_logging

# -------------------------------------------------
# Configuración global de logging
# -------------------------------------------------
configure_logging()
logger = logging.getLogger(__name__)


# -------------------------------------------------
# Validación adicional del archivo .env
# -------------------------------------------------
settings = Settings()
def validacion_env(settings: Settings) -> None:
    """
    Valida que ninguna variable cargada desde Settings sea None
    o un string vacío. Todas las variables son críticas, por lo tanto
    si alguna no tiene contenido se detiene la ejecución.
    """
    for name, value in settings.model_dump().items():
        if value is None:
            logger.critical("La variable de entorno %s es None.", name)
            raise RuntimeError(f"Variable crítica sin valor: {name}")

        if isinstance(value, str) and not value.strip():
            logger.critical("La variable de entorno %s está vacía o en blanco.", name)
            raise RuntimeError(f"Variable crítica vacía: {name}")

    logger.info("Todas las variables del .env tienen contenido válido.")


# -------------------------------------------------
# Carga de Settings con manejo explicito de errores
# -------------------------------------------------
try:
    
    validacion_env(settings)
    logger.info("Settings cargadas correctamente desde .env.")
except ValidationError as e:
    logger.critical("Error de validación al cargar Settings desde .env", exc_info=True)

    # Registro detallado de cada error específico de Pydantic
    for error in e.errors():
        field = ".".join(str(x) for x in error.get("loc", []))
        message = error.get("msg", "Error desconocido")
        type_error = error.get("type", "unknown")

        logger.critical(
            "Campo: '%s' - Mensaje: %s - Tipo: %s",
            field,
            message,
            type_error,
        )

    raise SystemExit("No es posible iniciar la aplicación debido a errores en .env.")
except Exception:
    logger.critical("Error inesperado al cargar Settings desde .env", exc_info=True)
    raise




# -------------------------------------------------
# Creación de la aplicación FastAPI
# -------------------------------------------------
app = FastAPI(
    title="Tesis Back API",
    version="1.0.0",
    description="API correspondiente al backend del proyecto de tesis."
)


# -------------------------------------------------
# Eventos de ciclo de vida
# -------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("Inicializando la aplicación Tesis Back API")

    safe_settings = settings.model_dump(exclude={"DB_PASSWORD", "MQTT_PASSWORD"})
    logger.debug("Configuraciones cargadas (sin exponer secretos): %s", safe_settings)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Finalizando la aplicación Tesis Back API")


# -------------------------------------------------
# Endpoint básico de verificación
# -------------------------------------------------
@app.get("/health")
async def health_check():
    logger.debug("Solicitud recibida: /health")
    return {
        "status": "ok",
        "db_host": settings.DB_HOST,
        "db_name": settings.DB_NAME,
    }

@app.get("/db-check")
async def db_check(session: AsyncSession = Depends(get_db_session)):
    logger.debug("Probando conexión a la base de datos")
    result = await session.execute(text("SELECT 1"))
    value= result.scalar_one()
    return {"status": "ok", "db_response": value}
