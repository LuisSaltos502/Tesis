import time
import paho.mqtt.client as mqtt
from settings import Settings


def main():
    settings = Settings()

    # --- Cliente B2 (broker central) ---
    client_b2 = mqtt.Client(client_id="bridge-b2")
    client_b2.connect(settings.MQTT_B2_HOST, settings.MQTT_B2_PORT, keepalive=60)
    client_b2.loop_start()

    # --- Callbacks B1 ---
    def on_connect_b1(client, userdata, flags, rc):
        if rc == 0:
            print(f"[B1] Conectado a {settings.MQTT_B1_HOST}:{settings.MQTT_B1_PORT}")
            print(f"[B1] Suscribiendo a: {settings.MQTT_TOPIC_SUB}")
            client.subscribe(settings.MQTT_TOPIC_SUB, qos=1)
        else:
            print(f"[B1] Error de conexión rc={rc}")

    def on_message_b1(client, userdata, msg):
        # Reenviar a B2 manteniendo el mismo tópico
        result = client_b2.publish(topic=msg.topic, payload=msg.payload, qos=1)
        # publish() es async; esperamos a que se encole
        result.wait_for_publish()
        #print(f"[BRIDGE] {msg.topic} -> B2 (qos=1)")

    # --- Cliente B1 (broker Raspberry) ---
    client_b1 = mqtt.Client(client_id="bridge-b1")
    client_b1.on_connect = on_connect_b1
    client_b1.on_message = on_message_b1

    client_b1.connect(settings.MQTT_B1_HOST, settings.MQTT_B1_PORT, keepalive=60)
    client_b1.loop_start()

    print("[INFO] Bridge corriendo. Ctrl+C para salir.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Cerrando...")
    finally:
        client_b1.loop_stop()
        client_b2.loop_stop()
        client_b1.disconnect()
        client_b2.disconnect()


if __name__ == "__main__":
    main()
