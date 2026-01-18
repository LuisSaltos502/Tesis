import json
import time
import random
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

# ---------- NO REGISTRADOS (los que ya tenías) ----------
MAC_GW = "AA:BB:CC:DD:EE:FF"
SENSOR_A = "11:22:33:44:55:66"
SENSOR_B = "77:88:99:AA:BB:CC"

TOPIC_A = f"gateways/{MAC_GW}/sensors/{SENSOR_A}/telemetry"
TOPIC_B = f"gateways/{MAC_GW}/sensors/{SENSOR_B}/telemetry"

# ---------- REGISTRADOS (los nuevos) ----------
MAC_GW_REG = "02:AA:11:7C:3D:90"
SENSOR_REG_A = "02:BB:22:6E:4F:A1"
SENSOR_REG_B = "02:CC:33:5A:8B:D2"

TOPIC_REG_A = f"gateways/{MAC_GW_REG}/sensors/{SENSOR_REG_A}/telemetry"
TOPIC_REG_B = f"gateways/{MAC_GW_REG}/sensors/{SENSOR_REG_B}/telemetry"

INTERVAL_SECONDS = 2   # cada cuánto manda (aprox)
ANOMALY_PROB = 0.15    # probabilidad de enviar dato "malo" (15%) ajustada
ANOMALY_PERSIST_TIME = 60  # minutos que el dato anómalo persistirá

def build_payload(sensor_name: str, anomaly_persist_time: int) -> dict:
    # valores base "normales"
    ph = round(random.uniform(6.8, 7.8), 2)
    temp = round(random.uniform(22.0, 28.0), 1)
    turb = round(random.uniform(0.5, 2.5), 2)
    tds = round(random.uniform(30.0, 90.0), 1)

    # simular una anomalía que persista durante el intervalo de prueba (60 minutos)
    if random.random() < ANOMALY_PROB:
        anomaly_type = random.choice(["turb", "tds", "ph_low", "ph_high"])
        if anomaly_type == "turb":
            turb = round(random.uniform(5.0, 9.0), 2)     # >= 5 dispara
        elif anomaly_type == "tds":
            tds = round(random.uniform(110.0, 200.0), 1)  # > 100 dispara
        elif anomaly_type == "ph_low":
            ph = round(random.uniform(5.5, 6.4), 2)       # < 6.5 dispara
        elif anomaly_type == "ph_high":
            ph = round(random.uniform(8.1, 9.0), 2)       # > 8.0 dispara

    # Persistencia de anomalía: si la anomalía persiste por el tiempo configurado, se mantiene hasta 60 minutos.
    if anomaly_persist_time > 0:
        turb = round(random.uniform(5.0, 9.0), 2)  # para turbidez > 5
        tds = round(random.uniform(110.0, 200.0), 1)  # para TDS > 100

    return {
        "ph": ph,
        "temperatura": temp,
        "turbidez": turb,
        "tds": tds,
    }

def on_connect(client, userdata, flags, rc):
    print(f"[SIM] Conectado rc={rc}")

def main():
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print("[SIM] Publicando continuamente en 4 topics (2 NO registrados + 2 registrados). Ctrl+C para salir.")
    try:
        while True:
            # --------- NO REGISTRADOS ----------
            payload_a = build_payload("A-NO-REG", ANOMALY_PERSIST_TIME)
            client.publish(TOPIC_A, json.dumps(payload_a), qos=1)
            print(f"[NO-REG A] {TOPIC_A} -> {payload_a}")

            payload_b = build_payload("B-NO-REG", ANOMALY_PERSIST_TIME)
            client.publish(TOPIC_B, json.dumps(payload_b), qos=1)
            print(f"[NO-REG B] {TOPIC_B} -> {payload_b}")

            # --------- REGISTRADOS ----------
            payload_ra = build_payload("A-REG", ANOMALY_PERSIST_TIME)
            client.publish(TOPIC_REG_A, json.dumps(payload_ra), qos=1)
            print(f"[REG A] {TOPIC_REG_A} -> {payload_ra}")

            payload_rb = build_payload("B-REG", ANOMALY_PERSIST_TIME)
            client.publish(TOPIC_REG_B, json.dumps(payload_rb), qos=1)
            print(f"[REG B] {TOPIC_REG_B} -> {payload_rb}")

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[SIM] Saliendo...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
