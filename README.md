# PR2 - Sistema automatizado de medicamentos

Proyecto del Grupo 2 Equipo 5 para integrar ESP32-S3, MQTT, una demo web, PostgreSQL/pgAdmin y RoboDK en un escenario de farmacia automatizada.

Nota: este repositorio de GitHub contiene el firmware ESP32, la integracion Python/PostgreSQL, la demo web y los scripts Python de RoboDK usados por ahora en la estacion.

El objetivo del sistema es simular y demostrar un flujo completo:

1. Una ESP32 registra medicamentos almacenados en una posicion de estanteria.
2. Los eventos se publican por MQTT.
3. Una capa de integracion puede actualizar PostgreSQL y consultar el stock.
4. Otra ESP32 o la web solicita medicamentos.
5. El pedido se procesa en orden FIFO.
6. RoboDK se mueve a la posicion del medicamento o se simula el movimiento.
7. El sistema publica el estado del pedido por MQTT.
8. La web muestra inventario, pedidos, eventos, posiciones y datos de negocio simulados.

## Estructura del proyecto

```text
ESP32-Proyecto2/
├── esp32_medicamentos/
│   ├── ESP32_Almacenamiento/
│   ├── ESP32_Pedido/
│   └── README.md
├── python_integracion/
│   ├── mqtt_robodk_bridge.py
│   ├── db.py
│   ├── robodk_client.py
│   ├── seed_demo_db.py
│   ├── schema.sql
│   ├── requirements.txt
│   └── README.md
├── python_robodk/
│   ├── ProgramaClasificacion.py
│   ├── ApareceCaja.py
│   ├── AvanzaCaja.py
│   ├── AvanzaPick.py
│   ├── AvanzaPlace.py
│   ├── CintaPick.py
│   ├── Reset.py
│   └── ResetPick.py
├── web_demo_medicamentos/
│   ├── src/
│   ├── server/
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
├── todo_esp32_proyecto/
├── Unidades_Did_cticas*/
└── zips y PDFs de apoyo
```

## Arquitectura general

El proyecto queda dividido en cinco capas:

| Capa | Carpeta | Funcion |
| --- | --- | --- |
| Firmware ESP32 | `esp32_medicamentos/` | Publica altas y pedidos reales por MQTT desde placas ESP32. |
| Broker MQTT | externo | Conecta ESP32, web y Python mediante topics comunes. |
| Integracion Python | `python_integracion/` | Escucha MQTT, actualiza PostgreSQL, reserva stock y llama a RoboDK. |
| Demo web | `web_demo_medicamentos/` | Panel React/Vite con backend Node para visualizar y lanzar eventos MQTT. |
| RoboDK | `python_robodk/` y `python_integracion/robodk_client.py` | Simula o ejecuta movimientos del robot hacia posiciones de estanteria. |

Por defecto se usa el broker publico:

```text
mqtt://broker.hivemq.com:1883
```

Tambien esta preparado para usar el broker de clase:

```text
mqtt://mqtt.dsic.upv.es:1883
usuario: giirob
password: UPV2024
```

## Topics MQTT

Todos los componentes comparten el topic base:

```text
giirob/pr2/grupo2equipo5
```

Topics principales:

```text
giirob/pr2/grupo2equipo5/almacen/registro
giirob/pr2/grupo2equipo5/almacen/status
giirob/pr2/grupo2equipo5/almacen/command
giirob/pr2/grupo2equipo5/pedido
giirob/pr2/grupo2equipo5/pedido/request
giirob/pr2/grupo2equipo5/pedido/status
giirob/pr2/grupo2equipo5/pedido/command
giirob/pr2/grupo2equipo5/pedido/conseguido
giirob/pr2/grupo2equipo5/robodk/status
```

Notas importantes:

- `pedido/request` lo usa la ESP32 de pedido.
- `pedido` lo usa la web y tambien lo escucha Python.
- Python escucha ambos (`pedido` y `pedido/request`) para mantener compatibilidad.
- `pedido/conseguido` se publica cuando el robot ha procesado correctamente un pedido y hay que indicar a la ESP32 que el pedido esta conseguido.

## Flujo completo de almacenamiento

1. La ESP32 de almacenamiento, la web o un comando de prueba genera un JSON de alta.
2. El JSON se publica en:

```text
giirob/pr2/grupo2equipo5/almacen/registro
```

Ejemplo:

```json
{
  "id_evento": "ALM-1",
  "device_id": "giirobpr2-grupo2equipo5-almacen",
  "tipo": "Ibuprofeno",
  "cod_barras": "847000100002",
  "posicion": "X01-Y02",
  "caducidad": "2027-08-15",
  "cantidad": 1
}
```

3. La demo web recibe el evento y actualiza su inventario local.
4. Si esta arrancado el puente Python, Python registra el evento en PostgreSQL:
   - Busca el medicamento por `cod_barras` o por `nombre`.
   - Si ya existe, suma stock y actualiza `pos`, `caducidad`, `estado` y codigo de barras si procede.
   - Si no existe, inserta un nuevo registro en `Medicamento`.
5. Python publica el resultado en:

```text
giirob/pr2/grupo2equipo5/almacen/status
```

Estados posibles:

```text
registrado
duplicado
error
posicion_actual
posicion_ajustada
```

## Flujo completo de pedido

1. La ESP32 de pedido, la web o un comando de prueba solicita un medicamento.
2. El pedido se publica por MQTT.

Ejemplo:

```json
{
  "id_pedido": "PED-1",
  "device_id": "giirobpr2-grupo2equipo5-pedido",
  "tipo": "Ibuprofeno",
  "cantidad": 1
}
```

3. Si solo se usa la demo web, el backend Node simula el procesamiento:
   - Busca el medicamento en el inventario local.
   - Descuenta stock.
   - Publica `preparando`.
   - Espera 1,5 segundos.
   - Publica `completado`.
4. Si se usa `python_integracion/mqtt_robodk_bridge.py`, el procesamiento real lo hace Python:
   - Recibe el pedido.
   - Lo mete en una cola FIFO.
   - Publica `encolado`.
   - Consulta PostgreSQL.
   - Reserva stock usando bloqueo transaccional.
   - Escoge primero el medicamento disponible con caducidad mas proxima.
   - Descuenta stock.
   - Cambia `estado` a `agotado` si el stock queda a cero.
   - Registra una venta si el pedido trae `DNI` o `dni`.
   - Obtiene la posicion (`pos`) del medicamento.
   - Llama a RoboDK para mover el robot.
   - Publica el estado final.

Estados de pedido:

```text
encolado
preparando
completado
no_disponible
error
error_robot
conseguido
```

## Firmware ESP32

La carpeta `esp32_medicamentos/` contiene dos sketches separados para Arduino IDE.

### ESP32_Almacenamiento

Carpeta:

```text
esp32_medicamentos/ESP32_Almacenamiento/
```

Funcion:

- Representa la placa que registra medicamentos que entran en el almacen.
- Publica eventos de alta en `almacen/registro`.
- Mantiene un contador interno de estanteria.
- Puede avanzar automaticamente por posiciones `X/Y`.
- Puede sincronizar su contador desde la web mediante MQTT.
- Enciende el LED interno cuando recibe estado `registrado`.

Configuracion principal:

```cpp
#define DEVICE_GIIROB_PR2_ID "grupo2equipo5-almacen"
#define NET_SSID "RedPR2"
#define NET_PASSWD "megustalatortilla"
#define MQTT_SERVER_IP "broker.hivemq.com"
#define MQTT_SERVER_PORT 1883
#define BASE_TOPIC "giirob/pr2/grupo2equipo5"
#define RACK_MAX_X 4
#define RACK_MAX_Y 3
```

Posiciones:

- Empieza en `X01-Y01`.
- Avanza primero `Y`.
- Cuando supera `RACK_MAX_Y`, vuelve `Y` a 1 y sube `X`.
- Cuando supera `RACK_MAX_X`, vuelve al inicio.

Comandos por monitor serie:

```text
HELP
DEMO
POS
SET_POS 2 1
REG_AUTO Ibuprofeno 847000100002 2027-08-15 1
REG Ibuprofeno X01-Y02 847000100002 2027-08-15 1
```

Comandos por MQTT en `almacen/command`:

```text
demo
pos
set_pos 2 1
led_on
led_off
```

Boton:

- Usa `BUTTON_PIN 4`.
- Esta pensado con `INPUT_PULLUP`, por eso pulsado equivale a `LOW`.
- Al pulsar publica un medicamento de demo.

Medicamentos de demo:

```text
Paracetamol  847000100001  2027-05-01
Ibuprofeno   847000100002  2027-08-15
Amoxicilina  847000100003  2026-12-20
```

### ESP32_Pedido

Carpeta:

```text
esp32_medicamentos/ESP32_Pedido/
```

Funcion:

- Representa la placa que solicita medicamentos.
- Publica pedidos en `pedido/request`.
- Escucha estados en `pedido/status`.
- Permite pedir medicamentos con botones fisicos o por monitor serie.
- Enciende o apaga el LED interno segun el estado del pedido.

Configuracion principal:

```cpp
#define DEVICE_GIIROB_PR2_ID "grupo2equipo5-pedido"
#define NET_SSID "RedPR2"
#define NET_PASSWD "megustalatortilla"
#define MQTT_SERVER_IP "broker.hivemq.com"
#define MQTT_SERVER_PORT 1883
#define BASE_TOPIC "giirob/pr2/grupo2equipo5"
#define BUTTON_PARACETAMOL_PIN 18
#define BUTTON_IBUPROFENO_PIN 17
#define BUTTON_ENANTYUM_PIN 16
```

Botones:

```text
GPIO18 -> Paracetamol
GPIO17 -> Ibuprofeno
GPIO16 -> Enantyum
```

Comandos por monitor serie:

```text
HELP
DEMO
PED Ibuprofeno 1
```

Comandos por MQTT en `pedido/command`:

```text
demo
led_on
led_off
```

Estados recibidos:

- Si llega `preparando` o `entregado`, enciende el LED interno.
- Si llega `no_disponible` o `error`, apaga el LED interno.
- Imprime por serie el estado, la posicion y el mensaje recibidos.

## Demo web

Carpeta:

```text
web_demo_medicamentos/
```

La demo web tiene dos partes:

- Frontend React/Vite en `src/main.jsx` y `src/styles.css`.
- Backend Express/MQTT en `server/index.js`.

El navegador no se conecta directamente al broker MQTT. El frontend llama a la API local, y el backend publica/escucha MQTT. Esto evita meter credenciales MQTT en el navegador.

### Funciones de la web

La interfaz incluye:

- Dashboard de farmacia automatizada.
- Estado de conexion MQTT.
- Stock total.
- Alertas de stock bajo.
- Siguiente posicion de estanteria.
- Mapa de estanteria `X/Y`.
- Tabla de inventario.
- Alta de medicamento.
- Solicitud de medicamento.
- Sincronizacion del contador de estanteria con la ESP32.
- Eventos MQTT en vivo.
- Grafico de ventas simuladas.
- Simulador de rentabilidad mensual.
- Tabla de margen por producto.

### Backend Node

Archivo:

```text
web_demo_medicamentos/server/index.js
```

Mantiene un estado en memoria con:

```text
connected
pythonBridgeEnabled
baseTopic
topics
rack
inventory
events
```

Endpoints:

```text
GET  /api/state
POST /api/storage/register
POST /api/orders/request
POST /api/rack
```

`POST /api/storage/register`:

- Crea un evento `WEB-ALM-*`.
- Usa la posicion enviada o la posicion actual de estanteria.
- Actualiza inventario local.
- Publica en `almacen/registro`.
- Publica estado `registrado`.
- Avanza el contador si la posicion no se puso manualmente.

`POST /api/orders/request`:

- Crea un pedido `WEB-PED-*`.
- Publica en `pedido`.
- Si `PYTHON_BRIDGE_ENABLED` no esta activo, Node simula el pedido.
- Si `PYTHON_BRIDGE_ENABLED=true`, delega el procesamiento en Python.

`POST /api/rack`:

- Valida `x` e `y`.
- Actualiza el contador local.
- Publica `set_pos x y` en `almacen/command`.
- Sirve para sincronizar el contador de la web con la ESP32 de almacenamiento.

### Arrancar la web

```bash
cd web_demo_medicamentos
npm install
npm run dev
```

Servicios:

```text
Frontend: http://127.0.0.1:5173
API:      http://127.0.0.1:8787
```

Con broker de clase:

```bash
MQTT_URL=mqtt://mqtt.dsic.upv.es:1883 MQTT_USERNAME=giirob MQTT_PASSWORD=UPV2024 npm run dev
```

Con puente Python activado:

```bash
PYTHON_BRIDGE_ENABLED=true npm run dev
```

Con broker de clase y puente Python:

```bash
MQTT_URL=mqtt://mqtt.dsic.upv.es:1883 MQTT_USERNAME=giirob MQTT_PASSWORD=UPV2024 PYTHON_BRIDGE_ENABLED=true npm run dev
```

## Integracion Python, PostgreSQL y RoboDK

Carpeta:

```text
python_integracion/
```

Esta capa convierte los mensajes MQTT en acciones reales sobre base de datos y robot.

Archivos principales:

| Archivo | Funcion |
| --- | --- |
| `mqtt_robodk_bridge.py` | Servicio principal. Conecta MQTT, PostgreSQL y RoboDK. |
| `db.py` | Funciones de base de datos: validar esquema, registrar altas, reservar pedidos, seed e inventario. |
| `robodk_client.py` | Cliente RoboDK real/simulado, calculo de targets y posiciones de estanteria. |
| `seed_demo_db.py` | Inserta medicamentos de demo en PostgreSQL. |
| `schema.sql` | Referencia documental del esquema PostgreSQL usado. |
| `requirements.txt` | Dependencias Python. |

### Tablas esperadas

Python valida que existan estas tablas:

```text
Medicamento
Cliente
Venta
Caja_Grande
Cinta_Transportadora
Sensor
Robot
Herramienta
Contiene
```

La tabla mas importante para el flujo es `Medicamento`:

```text
id_medicamento
cod_barras
nombre
caducidad
descripcion
stock
estado
pos
precio_venta
seguro_SS
```

`Venta` se usa solo si el pedido trae `DNI` o `dni`. Ese DNI debe existir antes en `Cliente`, porque hay clave foranea.

No se crea tabla `Pedido`, porque el esquema actual no la incluye. Por eso los estados de pedido se comunican por MQTT.

### Instalar Python

```bash
cd python_integracion
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si se va a usar RoboDK real:

```bash
pip install robodk
```

### Configurar PostgreSQL

Python lee la conexion desde `DATABASE_URL`.

Ejemplo:

```bash
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/medicamentos'
```

Si no se define, usa por defecto:

```text
postgresql://postgres:postgres@localhost:5432/medicamentos
```

Inicializar medicamentos de demo:

```bash
python seed_demo_db.py
```

Medicamentos insertados por el seed:

```text
MED001 Paracetamol  X01-Y01 stock=3
MED002 Ibuprofeno   X01-Y02 stock=2
MED003 Amoxicilina  X02-Y01 stock=1
```

### Ejecutar puente Python

Modo simulacion RoboDK:

```bash
ROBODK_MODE=sim python mqtt_robodk_bridge.py
```

Con broker de clase:

```bash
MQTT_URL=mqtt://mqtt.dsic.upv.es:1883 MQTT_USERNAME=giirob MQTT_PASSWORD=UPV2024 ROBODK_MODE=sim python mqtt_robodk_bridge.py
```

Modo real RoboDK:

```bash
ROBODK_MODE=real python mqtt_robodk_bridge.py
```

Tambien acepta argumentos:

```bash
python mqtt_robodk_bridge.py --database-url postgresql://postgres:postgres@localhost:5432/medicamentos --mqtt-url mqtt://broker.hivemq.com:1883 --base-topic giirob/pr2/grupo2equipo5
```

## RoboDK

Hay dos partes relacionadas con RoboDK.

### Scripts originales de RoboDK

Carpeta:

```text
python_robodk/
```

Contiene scripts usados dentro de la estacion RoboDK:

| Script | Funcion |
| --- | --- |
| `ProgramaClasificacion.py` | Programa principal de clasificacion. Hace pick, calcula posiciones de estanteria y coloca cajas. |
| `ApareceCaja.py` | Crea/copia una caja visible en la cinta y limpia copias anteriores. |
| `AvanzaCaja.py` | Avanza la cinta principal. |
| `AvanzaPick.py` | Avanza la cinta de pick. |
| `AvanzaPlace.py` | Avanza la cinta asociada al place. |
| `CintaPick.py` | Avanza la cinta de cajas despaletizadas. |
| `Reset.py` | Resetea la cinta principal. |
| `ResetPick.py` | Resetea la cinta de pick. |

`ProgramaClasificacion.py` usa:

```text
Robot: UR3e Base - Clasificación
Herramienta: RobotiQ EPick Vacuum Gripper (1 Cup)
Frame: Sistema - Estantería
Targets: Paso, Target 2, Target 3, Place_base
```

Calcula posiciones desde `Place_base` con medidas de caja y huecos:

```text
ancho caja: 125 mm
fondo caja: 66 mm
gap: 30 mm
salto vertical/nivel: 215 mm
```

### Cliente RoboDK del puente Python

Archivo:

```text
python_integracion/robodk_client.py
```

Modos:

```text
ROBODK_MODE=sim   -> no conecta con RoboDK; devuelve movimiento simulado.
ROBODK_MODE=real  -> exige conexion real con RoboDK.
ROBODK_MODE=auto  -> intenta RoboDK y si no esta disponible simula.
```

Nombres por defecto:

```text
ROBODK_ROBOT_NAME='UR3e Base - Clasificación'
ROBODK_TOOL_NAME='RobotiQ EPick Vacuum Gripper (1 Cup)'
ROBODK_FRAME_NAME='Sistema - Estantería'
ROBODK_PLACE_BASE_TARGET='Place_base'
```

Funcionamiento:

1. Recibe una posicion desde PostgreSQL (`Medicamento.pos`).
2. Si la posicion coincide con un target real de RoboDK, mueve el robot a ese target.
3. Si la posicion tiene formato `X01-Y02`, calcula la pose desde `Place_base`.
4. Si no puede calcular ni encontrar target, devuelve error.

Alias incluidos:

```text
paso -> Paso
paso_1 -> Paso
paso_2 -> Target 2
paso_3 -> Target 3
place_base -> Place_base
```

Se pueden configurar targets con plantilla:

```bash
ROBODK_TARGET_TEMPLATE='POS_{position_clean}' python mqtt_robodk_bridge.py
```

Ejemplo:

```text
X01-Y01 -> POS_X01_Y01
```

Tambien se pueden definir alias sin tocar codigo:

```bash
ROBODK_TARGET_ALIASES='{"X01-Y01":"Mi target 1","X01-Y02":"Mi target 2"}' python mqtt_robodk_bridge.py
```

## Mensajes JSON principales

### Alta de almacenamiento

```json
{
  "id_evento": "ALM-1",
  "device_id": "giirobpr2-grupo2equipo5-almacen",
  "tipo": "Ibuprofeno",
  "cod_barras": "847000100002",
  "posicion": "X01-Y02",
  "caducidad": "2027-08-15",
  "cantidad": 1
}
```

Campos:

| Campo | Uso |
| --- | --- |
| `id_evento` | Identificador del evento. |
| `device_id` | Dispositivo que publica. |
| `tipo` / `nombre` | Nombre del medicamento. |
| `cod_barras` | Codigo usado para identificar medicamento existente. |
| `posicion` / `pos` | Posicion de estanteria o target RoboDK. |
| `caducidad` | Fecha de caducidad. |
| `cantidad` | Unidades que entran en stock. |
| `precio_venta` | Opcional para insertar nuevos medicamentos. |
| `seguro_SS` / `seguro_ss` | Opcional para insertar nuevos medicamentos. |

### Pedido

```json
{
  "id_pedido": "PED-1",
  "device_id": "giirobpr2-grupo2equipo5-pedido",
  "tipo": "Ibuprofeno",
  "cantidad": 1,
  "color": "azul"
}
```

Campos:

| Campo | Uso |
| --- | --- |
| `id_pedido` | Obligatorio para Python. |
| `device_id` | Dispositivo que publica. |
| `tipo` / `nombre` | Medicamento solicitado. |
| `cantidad` | Unidades solicitadas. |
| `color` | Opcional; si existe, se publica confirmacion LED en `pedido/conseguido`. |
| `DNI` / `dni` | Opcional; si existe, Python registra una fila en `Venta`. |

### Estado de pedido

```json
{
  "id_pedido": "PED-1",
  "estado": "completado",
  "tipo": "Ibuprofeno",
  "cantidad": 1,
  "posicion": "X01-Y02",
  "robot_mode": "sim",
  "mensaje": "Simulacion RoboDK: mover a X01-Y02",
  "origen": "python-db-robodk"
}
```

### Confirmacion para LED

```json
{
  "id_pedido": "PED-1",
  "estado": "conseguido",
  "tipo": "Ibuprofeno",
  "color": "azul",
  "posicion": "X01-Y02",
  "origen": "python-db-robodk"
}
```

## Puesta en marcha recomendada

### Opcion 1: solo demo web simulada

Sirve para demostrar MQTT, inventario, pedidos y dashboard sin PostgreSQL ni RoboDK.

```bash
cd web_demo_medicamentos
npm install
npm run dev
```

Abrir:

```text
http://127.0.0.1:5173
```

### Opcion 2: ESP32 + web

1. Cargar `ESP32_Almacenamiento` en una ESP32.
2. Cargar `ESP32_Pedido` en otra ESP32.
3. Arrancar la web.
4. Usar el mismo broker y el mismo `BASE_TOPIC`.
5. Pulsar botones o usar monitor serie.
6. Ver eventos en vivo en la web.

### Opcion 3: web + Python + PostgreSQL + RoboDK simulado

Terminal 1:

```bash
cd python_integracion
source .venv/bin/activate
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/medicamentos'
python seed_demo_db.py
ROBODK_MODE=sim python mqtt_robodk_bridge.py
```

Terminal 2:

```bash
cd web_demo_medicamentos
PYTHON_BRIDGE_ENABLED=true npm run dev
```

### Opcion 4: sistema completo con RoboDK real

1. Abrir RoboDK con la estacion correcta.
2. Comprobar que existen robot, herramienta, frame y targets con los nombres esperados.
3. Arrancar PostgreSQL.
4. Arrancar Python:

```bash
cd python_integracion
source .venv/bin/activate
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/medicamentos'
ROBODK_MODE=real python mqtt_robodk_bridge.py
```

5. Arrancar web con delegacion a Python:

```bash
cd web_demo_medicamentos
PYTHON_BRIDGE_ENABLED=true npm run dev
```

6. Usar ESP32 o web para publicar altas y pedidos.

## Variables de entorno

### MQTT

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `MQTT_URL` | `mqtt://broker.hivemq.com:1883` | Broker MQTT. |
| `MQTT_USERNAME` | vacio | Usuario MQTT si el broker lo requiere. |
| `MQTT_PASSWORD` | vacio | Password MQTT si el broker lo requiere. |
| `MQTT_BASE_TOPIC` | `giirob/pr2/grupo2equipo5` | Topic base compartido. |

### Web

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `PORT` | `8787` | Puerto del backend Express. |
| `PYTHON_BRIDGE_ENABLED` | `false` | Si es `true`, Node no simula pedidos y deja responder a Python. |

### Python/PostgreSQL

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/medicamentos` | Conexion PostgreSQL. |
| `DEFAULT_PRECIO_VENTA` | `0` | Precio usado al insertar medicamento nuevo si no llega precio. |
| `DEFAULT_SEGURO_SS` | `false` | Valor por defecto para `seguro_SS`. |

### RoboDK

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `ROBODK_MODE` | `auto` | `sim`, `real` o `auto`. |
| `ROBODK_ROBOT_NAME` | `UR3e Base - Clasificación` | Nombre del robot. |
| `ROBODK_TOOL_NAME` | `RobotiQ EPick Vacuum Gripper (1 Cup)` | Nombre de herramienta. |
| `ROBODK_FRAME_NAME` | `Sistema - Estantería` | Sistema de referencia. |
| `ROBODK_PLACE_BASE_TARGET` | `Place_base` | Target base de estanteria. |
| `ROBODK_TARGET_TEMPLATE` | `{position}` | Plantilla para targets. |
| `ROBODK_TARGET_ALIASES` | alias internos | JSON o lista `clave=target`. |

## Validaciones y protecciones que se han incluido

- Debounce de botones en las ESP32 para evitar dobles pulsaciones.
- Topics separados para alta, pedido, estado y comandos.
- Compatibilidad con `pedido` y `pedido/request`.
- Estado local de la web limitado a los ultimos 60 eventos.
- Dedupe en Node por `id_evento` e `id_pedido` para no procesar duplicados.
- Validacion de rango al sincronizar la estanteria desde la web.
- Validacion de esquema PostgreSQL al arrancar Python.
- Transacciones en PostgreSQL para reservar stock.
- `FOR UPDATE SKIP LOCKED` para evitar conflictos si hay pedidos simultaneos.
- Seleccion del medicamento por caducidad mas cercana.
- Cambio automatico a `agotado` cuando el stock llega a cero.
- Modo `sim` de RoboDK para poder demostrar sin estacion real.
- Modo `auto` para simular si RoboDK no esta disponible.
- Alias y plantillas para adaptar posiciones a nombres reales de targets.

## Relacion entre posicion, estanteria y RoboDK

El sistema usa posiciones con formato:

```text
X01-Y01
X01-Y02
X02-Y01
```

La ESP32 de almacenamiento y la web comparten el mismo contador `X/Y`. Python guarda esa posicion en `Medicamento.pos`. Luego RoboDK puede interpretarla de dos formas:

1. Como nombre de target real, si existe en la estacion.
2. Como posicion de estanteria calculada desde `Place_base`.

El calculo en Python usa:

```text
x_offset = (x - 1) * (125 + 30) + 125 / 2
y_offset = -(y - 1) * 215 + 66
```

Esto mantiene coherencia con la logica usada en `ProgramaClasificacion.py`.

## Como probar rapidamente

1. Arrancar la web:

```bash
cd web_demo_medicamentos
npm run dev
```

2. Abrir `http://127.0.0.1:5173`.
3. Ir a "Alta de medicamento".
4. Registrar un medicamento.
5. Ver que aparece en inventario y eventos.
6. Ir a "Solicitud de medicamento".
7. Solicitar el mismo medicamento.
8. Ver estados `preparando` y `completado`.
9. Revisar que el stock baja.

Para probar con Python:

1. Arrancar PostgreSQL.
2. Preparar `.venv`.
3. Ejecutar `python seed_demo_db.py`.
4. Ejecutar `ROBODK_MODE=sim python mqtt_robodk_bridge.py`.
5. Arrancar web con `PYTHON_BRIDGE_ENABLED=true`.
6. Solicitar un medicamento desde la web o desde la ESP32.

## Dependencias

### ESP32 / Arduino IDE

- Placa ESP32-S3 configurada en Arduino IDE.
- Librerias usadas por el esqueleto de clase, incluyendo WiFi, MQTT y ArduinoJson.
- Red WiFi configurada en `Config.h`.

### Web

- Node.js.
- npm.
- Dependencias declaradas en `web_demo_medicamentos/package.json`:
  - React
  - React DOM
  - Vite
  - Express
  - mqtt
  - concurrently
  - lucide-react

### Python

- Python 3.
- PostgreSQL accesible.
- Dependencias en `python_integracion/requirements.txt`.
- Paquete `robodk` solo si se usa modo real.

### RoboDK

- RoboDK instalado.
- Estacion abierta con los nombres esperados o variables de entorno adaptadas.

## Archivos auxiliares

- `web_demo_medicamentos.zip`, `python_integracion.zip` y `python_robodk.zip`: paquetes comprimidos de partes del proyecto.
- `demo-screenshot*.png`: capturas de la demo web.
- `Trabajo.pdf`, `PR2 - Trabajo Academico - Desarrollo SW_1.0.pdf`, `Unidades_Did_cticas*/`: material de apoyo y enunciados.
- `todo_esp32_proyecto/`: practicas, pruebas y codigo base previo.

## Resumen de lo implementado

Se ha construido una demostracion completa de sistema distribuido:

- Dos firmwares ESP32 separados: almacenamiento y pedido.
- Comunicacion MQTT con topics del grupo.
- Mensajes JSON normalizados para altas, pedidos, estados y confirmaciones.
- Backend web que publica y escucha MQTT.
- Frontend React para inventario, pedidos, eventos, estanteria y simulacion economica.
- Integracion Python con PostgreSQL.
- Uso del esquema existente de base de datos.
- Insercion y actualizacion de medicamentos.
- Reserva de pedidos con cola FIFO.
- Registro opcional de ventas si llega DNI.
- Cliente RoboDK real/simulado.
- Calculo de posiciones de estanteria desde `Place_base`.
- Compatibilidad con scripts y nombres existentes de RoboDK.
- Comandos por monitor serie y por MQTT para controlar las placas.
- Modo de demo sin hardware completo y modo de integracion real.
