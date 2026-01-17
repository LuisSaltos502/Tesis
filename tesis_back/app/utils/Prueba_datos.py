import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

MAC_GW = "AA:BB:CC:DD:EE:FF"
SENSOR_A = "11:22:33:44:55:66"
SENSOR_B = "77:88:99:AA:BB:CC"

TOPIC_A = f"gateways/{MAC_GW}/sensors/{SENSOR_A}/telemetry"
TOPIC_B = f"gateways/{MAC_GW}/sensors/{SENSOR_B}/telemetry"

INTERVAL_SECONDS = 2  # cada cuánto manda cada sensor (aprox)
ANOMALY_PROB = 0.15   # probabilidad de enviar un dato "malo" en cada envío (15%)

def build_payload(sensor_name: str) -> dict:
    # valores base "normales"
    ph = round(random.uniform(6.8, 7.8), 2)
    temp = round(random.uniform(22.0, 28.0), 1)
    turb = round(random.uniform(0.5, 2.5), 2)
    tds = round(random.uniform(30.0, 90.0), 1)

    # a veces meter anomalías para probar alertas
    if random.random() < ANOMALY_PROB:
        anomaly_type = random.choice(["turb", "tds", "ph_low", "ph_high"])
        if anomaly_type == "turb":
            turb = round(random.uniform(5.0, 9.0), 2)     # >= 5 dispara
        elif anomaly_type == "tds":
            tds = round(random.uniform(110.0, 200.0), 1)  # >100 dispara
        elif anomaly_type == "ph_low":
            ph = round(random.uniform(5.5, 6.4), 2)       # <6.5 dispara
        elif anomaly_type == "ph_high":
            ph = round(random.uniform(8.1, 9.0), 2)       # >8.0 dispara

    return {
        "ph": ph,
        "temperatura": temp,
        "turbidez": turb,
        "tds": tds,
        # Nota: no mandamos timestamp porque tu worker usa datetime.now() del servidor
        # "ts": datetime.now().isoformat()
    }

def on_connect(client, userdata, flags, rc):
    print(f"[SIM] Conectado rc={rc}")

def main():
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print("[SIM] Publicando continuamente en 2 sensores. Ctrl+C para salir.")
    try:
        while True:
            payload_a = build_payload("A")
            client.publish(TOPIC_A, json.dumps(payload_a), qos=1)
            print(f"[A] {TOPIC_A} -> {payload_a}")

            payload_b = build_payload("B")
            client.publish(TOPIC_B, json.dumps(payload_b), qos=1)
            print(f"[B] {TOPIC_B} -> {payload_b}")

            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n[SIM] Saliendo...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
