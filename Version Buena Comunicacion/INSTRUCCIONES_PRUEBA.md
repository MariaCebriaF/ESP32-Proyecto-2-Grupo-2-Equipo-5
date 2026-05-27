# Version Buena Comunicacion

Esta carpeta contiene la version preparada para probar la comunicacion MQTT con RoboDK usando identificadores numericos de medicamento.

## Identificadores

```text
1 = Paracetamol
2 = Ibuprofeno
3 = Enantyum
```

Los mensajes MQTT incluyen `tipo_id` para RoboDK y mantienen `tipo` como texto descriptivo.

## ESP32

Abrir en Arduino IDE:

```text
ESP32_Pedido/ESP32_Pedido.ino
ESP32_Almacenamiento/ESP32_Almacenamiento.ino
```

Topics principales:

```text
giirob/pr2/grupo2equipo5/pedido/request
giirob/pr2/grupo2equipo5/pedido/status
giirob/pr2/grupo2equipo5/almacen/registro
giirob/pr2/grupo2equipo5/almacen/status
```

## Puente Python

Desde esta carpeta:

```bash
cd python_integracion
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install robodk
ROBODK_MODE=real python mqtt_robodk_bridge.py
```

Para probar sin RoboDK real:

```bash
ROBODK_MODE=sim python mqtt_robodk_bridge.py
```

## RoboDK

Abrir:

```text
Entrega_7Mayo.rdk
```

El programa de pedidos usa el parametro `pedido_id`:

```text
1 -> Paracetamol
2 -> Ibuprofeno
3 -> Enantyum
```

