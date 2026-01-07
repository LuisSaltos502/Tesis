import time
import paho.mqtt.client as mqtt
import json
import asyncio
import threading
from app.core.config import settings  
from app.utils.logging_config import configure_logging
from app.schemas.lecturas import LecturaBaseMQTT, LecturaBaseMSQL
from pydantic import ValidationError
configure_logging()

import logging
logger = logging.getLogger(__name__)


def main():
    client = mqtt.Client(client_id="", protocol=mqtt.MQTTv311) #auto-generate client ID
    loop = asyncio.new_event_loop()
    queue = None  # se asignará dentro del hilo
    
    def start_loop():
        nonlocal queue
        asyncio.set_event_loop(loop)
        queue = asyncio.Queue()
        loop.run_forever()
    threading.Thread(target=start_loop, daemon=True).start()
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("[MQTT] Conectado a %s:%s", settings.MQTT_BROKER, settings.MQTT_PORT)
            logger.info("[MQTT] Suscrito a %s", settings.MQTT_TOPIC)
            client.subscribe(settings.MQTT_TOPIC, qos=1)
        else:
            logger.error("[MQTT] Error de conexión rc=%s", rc)

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="strict")
            data = json.loads(payload)
            # Validación Pydantic v2
            tele = LecturaBaseMQTT.model_validate(data)
            parts = msg.topic.split("/")
            # esperado: ["gateways", "<mac_gw>", "sensors", "<mac_esp>", "telemetry"]
            if len(parts) != 5 or parts[0] != "gateways" or parts[2] != "sensors" or parts[4] != "telemetry":
                logger.warning("[MQTT] Topic inválido: %s", msg.topic)
                return
            mac_gw = parts[1]
            mac_esp = parts[3]
            logger.info("[MQTT] Extraído mac_gw=%s mac_esp=%s", mac_gw, mac_esp)
            
            item = {
                "mac_gw": mac_gw,
                "mac_esp": mac_esp,
                "topic": msg.topic,
                "telemetry": tele.model_dump(),
            }
            def _put():
                if queue is  None:
                    logger.warning("[MQTT] cola no lista aún, descartando mensaje topic=%s", msg.topic)
                    return
                queue.put_nowait(item)
                logger.info("[MQTT] Encolado topic=%s", item["topic"])
            loop.call_soon_threadsafe(_put)
                

        except UnicodeDecodeError as e:
            logger.warning("[MQTT] Payload no es UTF-8 válido. topic=%s err=%s", msg.topic, e)
            return

        except json.JSONDecodeError as e:
            logger.warning("[MQTT] JSON inválido. topic=%s payload=%r err=%s", msg.topic, payload, e)
            return

        except ValidationError as e:
            logger.warning("[MQTT] Payload no cumple schema. topic=%s payload=%r err=%s", msg.topic, payload, e)
            return
        
        # Si llegó aquí: es válido
        logger.info("[MQTT] OK topic=%s data=%s", msg.topic, tele.model_dump())



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
