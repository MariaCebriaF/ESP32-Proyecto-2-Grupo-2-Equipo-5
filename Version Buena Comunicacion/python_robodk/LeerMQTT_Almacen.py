from robodk import robolink
import sys

RDK = robolink.Robolink()

carpeta_estacion = RDK.getParam("PATH_OPENSTATION")
if carpeta_estacion and carpeta_estacion not in sys.path:
    sys.path.append(carpeta_estacion)

import paho.mqtt.client as mqtt
import RobotController_Almacen as rc


BROKER = "broker.hivemq.com"
PORT = 1883
BASE_TOPIC = "giirob/pr2/grupo2equipo5"
ALMACEN_REGISTRO_TOPIC = BASE_TOPIC + "/almacen/registro"
ALMACEN_STATUS_TOPIC = BASE_TOPIC + "/almacen/status"


def on_message(mqttc, _obj, msg):
    payload = msg.payload.decode("utf-8")
    rc.handle_message(mqttc, msg.topic, payload, RDK, ALMACEN_STATUS_TOPIC)


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_message = on_message

mqttc.connect(BROKER, PORT, 60)
mqttc.subscribe(ALMACEN_REGISTRO_TOPIC, 0)
mqttc.publish(ALMACEN_STATUS_TOPIC, '{"estado":"robodk_listener_ready","origen":"robodk"}')

print("RoboDK escuchando MQTT:", ALMACEN_REGISTRO_TOPIC)
mqttc.loop_forever()

