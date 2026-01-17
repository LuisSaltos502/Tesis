import time
import paho.mqtt.client as mqtt
import json
import asyncio
import threading
from datetime import datetime, timedelta
from collections import deque
from app.core.config import settings
from app.utils.logging_config import configure_logging
from app.schemas.lecturas import LecturaBaseMQTT
from sqlalchemy import select
from app.models.enums import DeviceRole
from app.models.dispositivos import dispositivos
from pydantic import ValidationError
from app.database.session import AsyncSessionLocal
configure_logging()

import logging
logger = logging.getLogger(__name__)


def main():
    # buffers en memoria
    realtime_buffer = {}   # sensor_key -> deque[(ts, telemetry_dict)]
    hourly_acc = {}        # sensor_key -> {"hour_start": dt, "sum": {...}, "count": int}
    alert_state = {}       # sensor_key -> {"is_anomalous": bool, "last_email_at": dt|None, "last_reasons": list[str]}

    client = mqtt.Client(client_id="", protocol=mqtt.MQTTv311)  # auto-generate client ID

    loop = asyncio.new_event_loop()
    queue = None  # se asignará dentro del hilo

    # -----------------------------
    # Helpers (Paso 1)
    # -----------------------------
    def sensor_key(mac_gw: str, mac_esp: str) -> str:
        return f"{mac_gw}/{mac_esp}"

    def hour_floor(dt: datetime) -> datetime:
        return dt.replace(minute=0, second=0, microsecond=0)

    def check_anomaly(telemetry: dict) -> list[str]:
        reasons = []
        ph = telemetry.get("ph")
        turb = telemetry.get("turbidez")
        tds = telemetry.get("tds")
        # temperatura es informativa, no genera alerta

        if ph is not None:
            if ph < settings.PH_MIN:
                reasons.append(f"pH bajo ({ph} < {settings.PH_MIN})")
            elif ph > settings.PH_MAX:
                reasons.append(f"pH alto ({ph} > {settings.PH_MAX})")

        if turb is not None and turb >= settings.TURB_MAX:
            reasons.append(f"Turbidez alta ({turb} >= {settings.TURB_MAX})")

        if tds is not None and tds > settings.TDS_MAX:
            reasons.append(f"TDS alto ({tds} > {settings.TDS_MAX})")

        return reasons

    def update_realtime_buffer(key: str, ts: datetime, telemetry: dict):
        dq = realtime_buffer.get(key)
        if dq is None:
            dq = deque()
            realtime_buffer[key] = dq

        dq.append((ts, telemetry))

        # limpiar > 10 minutos
        cutoff = ts - timedelta(minutes=10)
        while dq and dq[0][0] < cutoff:
            dq.popleft()

    def update_hourly_acc(key: str, ts: datetime, telemetry: dict):
        current_hour = hour_floor(ts)

        acc = hourly_acc.get(key)
        if acc is None:
            hourly_acc[key] = {
                "hour_start": current_hour,
                "sum": {"ph": 0.0, "temperatura": 0.0, "turbidez": 0.0, "tds": 0.0},
                "count": 0,
            }
            acc = hourly_acc[key]

        # si cambió la hora, “flush” del promedio anterior (por ahora solo log)
        if acc["hour_start"] != current_hour:
            prev_hour = acc["hour_start"]
            count = acc["count"]
            if count > 0:
                avg = {k: (acc["sum"][k] / count) for k in acc["sum"].keys()}
                logger.info("[HOUR FLUSH] sensor=%s hour_start=%s avg=%s count=%s", key, prev_hour, avg, count)
            else:
                logger.info("[HOUR FLUSH] sensor=%s hour_start=%s (sin datos)", key, prev_hour)

            # reset para nueva hora
            hourly_acc[key] = {
                "hour_start": current_hour,
                "sum": {"ph": 0.0, "temperatura": 0.0, "turbidez": 0.0, "tds": 0.0},
                "count": 0,
            }
            acc = hourly_acc[key]

        # acumular (solo si existen valores)
        # Nota: tu schema siempre trae los 4, pero igual dejamos defensivo
        for field in ("ph", "temperatura", "turbidez", "tds"):
            v = telemetry.get(field)
            if v is not None:
                acc["sum"][field] += float(v)

        acc["count"] += 1

    def apply_alert_logic(key: str, ts: datetime, telemetry: dict):
        reasons = check_anomaly(telemetry)
        is_anomalous_now = len(reasons) > 0

        st = alert_state.get(key)
        if st is None:
            st = {"is_anomalous": False, "last_email_at": None, "last_reasons": []}
            alert_state[key] = st

        cooldown = timedelta(minutes=settings.ALERT_COOLDOWN_MINUTES)

        # normal -> anómalo
        if (not st["is_anomalous"]) and is_anomalous_now:
            st["is_anomalous"] = True
            st["last_email_at"] = ts  # aquí simulamos que “se envió”
            st["last_reasons"] = reasons
            logger.warning("[ALERT NEW] sensor=%s ts=%s reasons=%s telemetry=%s", key, ts, reasons, telemetry)
            return

        # anómalo -> sigue anómalo
        if st["is_anomalous"] and is_anomalous_now:
            last = st["last_email_at"]
            if last is None or (ts - last) >= cooldown:
                st["last_email_at"] = ts  # simulamos “recordatorio”
                st["last_reasons"] = reasons
                logger.warning("[ALERT REMINDER] sensor=%s ts=%s reasons=%s telemetry=%s", key, ts, reasons, telemetry)
            else:
                # opcional: debug para no spamear logs
                st["last_reasons"] = reasons
                logger.info("[ALERT STILL] sensor=%s ts=%s reasons=%s (cooldown activo)", key, ts, reasons)
            return

        # anómalo -> recuperado
        if st["is_anomalous"] and (not is_anomalous_now):
            st["is_anomalous"] = False
            st["last_email_at"] = None
            prev_reasons = st["last_reasons"]
            st["last_reasons"] = []
            logger.info("[ALERT RECOVERED] sensor=%s ts=%s prev_reasons=%s", key, ts, prev_reasons)
            return

        # normal -> normal (no hacer nada)

    # -----------------------------
    # Consumer async (Paso 1)
    # -----------------------------
    async def consumer():
        logger.info("[CONSUMER] Iniciado")
        
        
        while True:
            item = await queue.get()  # queue ya existe dentro del loop
            try:
                ts = datetime.now()
                key = sensor_key(item["mac_gw"], item["mac_esp"])
                telemetry = item["telemetry"]

                update_realtime_buffer(key, ts, telemetry)
                update_hourly_acc(key, ts, telemetry)
                apply_alert_logic(key, ts, telemetry)

            except Exception as e:
                logger.exception("[CONSUMER] Error procesando item=%s err=%s", item, e)
            finally:
                queue.task_done()

    # -----------------------------
    # Loop thread
    # -----------------------------
    def start_loop():
        nonlocal queue
        asyncio.set_event_loop(loop)
        queue = asyncio.Queue()

        #  Paso 1: arrancar consumer dentro del loop
        loop.create_task(consumer())

        loop.run_forever()

    threading.Thread(target=start_loop, daemon=True).start()

    # -----------------------------
    # MQTT callbacks
    # -----------------------------
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
                if queue is None:
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
