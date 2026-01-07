import time
import paho.mqtt.client as mqtt
from app.core.config import settings  
from app.utils.logging_config import configure_logging

configure_logging()

import logging
logger = logging.getLogger(__name__)


def main():
    client = mqtt.Client(client_id="tesis-mqtt-worker")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("[MQTT] Conectado a %s:%s", settings.MQTT_BROKER, settings.MQTT_PORT)
            logger.info("[MQTT] Suscrito a %s", settings.MQTT_TOPIC)
            client.subscribe(settings.MQTT_TOPIC, qos=1)
        else:
            logger.error("[MQTT] Error de conexión rc=%s", rc)

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="replace")
        except Exception:
            payload = str(msg.payload)
        logger.info("[MSG] topic=%s payload=%s", msg.topic, payload)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
    client.loop_start()

    logger.info("[INFO] Worker MQTT corriendo. Ctrl+C para salir.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n[INFO] Cerrando worker...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
