# Integracion Python: PostgreSQL, MQTT y RoboDK

Este puente conecta las ESP32 con la base PostgreSQL que veis en pgAdmin y con RoboDK.

## Tablas usadas

El programa usa vuestro esquema existente:

- `Medicamento`: consulta y actualiza `stock`, `estado` y `pos`.
- `Venta`: registra una venta si el pedido MQTT trae `DNI` o `dni`.
- `Cliente`: solo se usa indirectamente por la clave foranea de `Venta`.

No crea una tabla `Pedido`, porque no existe en vuestro modelo. El estado del pedido se comunica por MQTT en `pedido/status`.

## Flujo

1. La ESP32 de almacen publica en `giirob/pr2/grupo2equipo5/almacen/registro`.
2. Python busca el medicamento por `cod_barras` o por `nombre`.
3. Si existe, suma stock y actualiza `pos`, `caducidad` y `estado`.
4. Si no existe, inserta una fila nueva en `Medicamento`.
5. La ESP32 de pedido publica en `giirob/pr2/grupo2equipo5/pedido/request`.
6. Python busca en `Medicamento` por `nombre`/`tipo`, comprueba stock y reserva.
7. Python descuenta stock, cambia `estado` a `agotado` si queda a cero y obtiene `pos`.
8. Python pide a RoboDK que vaya al target correspondiente a `pos`.
9. Python publica `preparando`, `completado`, `no_disponible` o `error_robot` en MQTT.

## Mensajes MQTT esperados

Alta de medicamento:

```json
{
  "id_medicamento": "MED002",
  "tipo_id": 2,
  "tipo": "Ibuprofeno",
  "cod_barras": "847000100002",
  "posicion": "X01-Y02",
  "caducidad": "2027-08-15",
  "cantidad": 1,
  "precio_venta": 4.1,
  "seguro_SS": true
}
```

Pedido:

```json
{
  "id_pedido": "PED-1",
  "tipo_id": 2,
  "tipo": "Ibuprofeno",
  "cantidad": 1
}
```

Si quereis registrar tambien la venta:

```json
{
  "id_pedido": "PED-1",
  "DNI": "12345678A",
  "tipo_id": 2,
  "tipo": "Ibuprofeno",
  "cantidad": 1
}
```

Ese `DNI` debe existir antes en `Cliente`, porque `Venta.DNI` tiene clave foranea.

## Identificadores de medicamento para RoboDK

El puente prioriza el entero `tipo_id` para mandar la orden a RoboDK y deja `tipo` como texto descriptivo:

```text
1 = Paracetamol
2 = Ibuprofeno
3 = Enantyum
```

Si un mensaje antiguo solo trae `tipo`, Python sigue convirtiendo el nombre al ID correspondiente.

## Conexion PostgreSQL

pgAdmin es la interfaz visual; Python se conecta al servidor con `DATABASE_URL`:

```bash
export DATABASE_URL='postgresql://usuario:password@localhost:5432/nombre_base'
```

Ejemplo local:

```bash
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/medicamentos'
```

## Instalacion

```bash
cd python_integracion
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si vas a usar RoboDK real:

```bash
pip install robodk
```

## Ejecutar

Modo simulacion de RoboDK:

```bash
ROBODK_MODE=sim python mqtt_robodk_bridge.py
```

Con el broker de clase:

```bash
MQTT_URL=mqtt://mqtt.dsic.upv.es:1883 MQTT_USERNAME=giirob MQTT_PASSWORD=UPV2024 ROBODK_MODE=sim python mqtt_robodk_bridge.py
```

RoboDK real:

```bash
ROBODK_MODE=real ROBODK_ROBOT_NAME=robot_pedidos python mqtt_robodk_bridge.py
```

## Targets de RoboDK

Por defecto busca un target con el mismo nombre que `Medicamento.pos`:

```text
X01-Y01
X01-Y02
X02-Y01
```

Si en RoboDK se llaman `POS_X01_Y01`, usa:

```bash
ROBODK_TARGET_TEMPLATE='POS_{position_clean}' python mqtt_robodk_bridge.py
```

`{position}` conserva `X01-Y01`; `{position_clean}` cambia guiones por guion bajo.
