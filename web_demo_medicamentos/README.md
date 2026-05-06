# Web demo medicamentos

Panel React/Vite para demostrar la integracion entre ESP32-S3, MQTT, inventario y futura capa RoboDK.

## Arquitectura

- Frontend React en `src/`.
- Backend Node en `server/index.js`.
- El navegador no conoce las credenciales MQTT.
- El backend publica y escucha los mismos topics que las ESP32.
- Por defecto usa `broker.hivemq.com:1883`, broker publico sin usuario ni contrasena.

## Topics usados

```text
giirob/pr2/grupo2equipo5/almacen/registro
giirob/pr2/grupo2equipo5/almacen/status
giirob/pr2/grupo2equipo5/almacen/command
giirob/pr2/grupo2equipo5/pedido/request
giirob/pr2/grupo2equipo5/pedido/status
giirob/pr2/grupo2equipo5/pedido/command
```

## Puesta en marcha

```bash
npm install
npm run dev
```

Para usar otro broker con usuario y contrasena:

```bash
MQTT_URL=mqtt://mqtt.dsic.upv.es:1883 MQTT_USERNAME=giirob MQTT_PASSWORD=UPV2024 npm run dev
```

La web queda en:

```text
http://127.0.0.1:5173
```

La API local queda en:

```text
http://127.0.0.1:8787
```

## Usar el puente Python/PostgreSQL/RoboDK

Si se arranca `python_integracion/mqtt_robodk_bridge.py`, conviene delegar los pedidos reales en Python para evitar que Node responda tambien con la simulacion. Python consultara la base PostgreSQL que gestionamos desde pgAdmin:

```bash
PYTHON_BRIDGE_ENABLED=true npm run dev
```

Con broker de clase y puente Python:

```bash
MQTT_URL=mqtt://mqtt.dsic.upv.es:1883 MQTT_USERNAME=giirob MQTT_PASSWORD=UPV2024 PYTHON_BRIDGE_ENABLED=true npm run dev
```

## Uso

- `Alta de medicamento`: publica un JSON equivalente a la ESP32 de almacenamiento.
- `Solicitud de medicamento`: publica un JSON equivalente a la ESP32 de pedido.
- `Sincronizacion RoboDK`: envia `set_pos x y` al topic de comando de almacenamiento para ajustar el contador X/Y de la ESP32.
- `Eventos en vivo`: muestra mensajes MQTT publicados/recibidos.

Para la capa PostgreSQL/RoboDK real o simulada, ver `../python_integracion/README.md`.
