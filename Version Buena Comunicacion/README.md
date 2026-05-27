# GESTIÓN DE DATOS PARA LA INDUSTRIA  
## DISEÑO DE UNA SOLUCIÓN DE INTEGRACIÓN EN EL ÁMBITO DE UNA FÁBRICA

---

## MIEMBROS DEL EQUIPO

- Javier Baena Martín  
- Adriana Baghdasaryan Hovnatanyan  
- María Fátima Cebriá Fernández  
- Tessa Martínez Botella  
- Leyre Vidal Colomer  

---

# ÍNDICE

1. [Introducción](#1-introducción)  
2. [Arquitectura general de integración](#2-arquitectura-general-de-integración)  
3. [Escenario de integración 1: solicitud de medicamento con ESP32_Pedido](#3-escenario-de-integración-1-solicitud-de-medicamento-con-esp32_pedido)  
   - 3.1 [Descripción del escenario](#31-descripción-del-escenario)  
   - 3.2 [Participantes](#32-participantes)  
   - 3.3 [Integración mediante MQTT](#33-integración-mediante-mqtt)  
   - 3.4 [Canales de estado y control](#34-canales-de-estado-y-control)  
   - 3.5 [Flujo de funcionamiento](#35-flujo-de-funcionamiento)  
   - 3.6 [Montaje físico de la ESP32_Pedido](#36-montaje-físico-de-la-esp32_pedido)  
4. [Escenario de integración 2: registro de almacenamiento mediante ESP32_Almacenamiento](#4-escenario-de-integración-2-registro-de-almacenamiento-mediante-esp32_almacenamiento)  
   - 4.1 [Descripción del escenario](#41-descripción-del-escenario)  
   - 4.2 [Participantes](#42-participantes)  
   - 4.3 [Integración mediante MQTT](#43-integración-mediante-mqtt)  
   - 4.4 [Canales de estado y control](#44-canales-de-estado-y-control)  
   - 4.5 [Flujo de funcionamiento](#45-flujo-de-funcionamiento)  
5. [Base de datos](#5-base-de-datos)  
6. [Integración con RoboDK](#6-integración-con-robodk)  
7. [Justificación de Programación Avanzada y Gestión de Datos](#7-justificación-de-programación-avanzada-y-gestión-de-datos)  
   - 7.1 [Relación con PRA](#71-relación-con-pra)  
   - 7.2 [Relación con GDI](#72-relación-con-gdi)  
8. [Pruebas de funcionamiento](#8-pruebas-de-funcionamiento)  
9. [Conclusiones](#9-conclusiones)  

---

# 1. Introducción

Este documento recoge los escenarios de integración planteados para la celda robotizada de clasificación y almacenamiento de medicamentos desarrollada en el proyecto.

La idea de partida es una celda simulada en RoboDK, formada por dos robots colaborativos UR3e, cintas transportadoras, sensores y una estantería de almacenamiento. El objetivo general de esta celda es automatizar parte del proceso de clasificación de cajitas de medicamentos, desde que llegan al sistema hasta que se colocan en la posición correspondiente.

En este trabajo se amplía esa propuesta incorporando una parte de integración entre distintos elementos del sistema. Para ello se utilizan dos sketches basados en ESP32-S3, comunicación mediante MQTT, programas desarrollados en Python, una base de datos gestionada desde pgAdmin, RoboDK y una demo web. Con esta integración se busca que los distintos componentes puedan intercambiar información entre sí y coordinar el proceso de forma ordenada.

El programa Python actúa como elemento central de la integración, recibe los mensajes MQTT enviados por las ESP32-S3, consulta o actualiza la base de datos y permite relacionar esta información con la simulación de RoboDK.

La solución se ha dividido en dos escenarios:

- **ESP32_Pedido**: encargado de solicitar medicamentos mediante botones físicos.
- **ESP32_Almacenamiento**: encargado de registrar medicamentos almacenados en posiciones concretas de la estantería.

Para las pruebas se han utilizado tres medicamentos:

- Ibuprofeno  
- Paracetamol  
- Enantyum  

La simulación considera una caja grande formada por 18 unidades, repartidas en 6 unidades de cada medicamento.

Además, se incluye una demo web que permite probar altas, pedidos, inventario y eventos MQTT sin depender siempre de las placas físicas.

---

# 2. Arquitectura general de integración

La solución propuesta se basa en la comunicación entre varios elementos:

- ESP32_Pedido  
- ESP32_Almacenamiento  
- Broker MQTT  
- Programa Python  
- PostgreSQL  
- RoboDK  
- Demo web  

Las ESP32-S3 no se conectan directamente ni a la base de datos ni a RoboDK. Su función principal es publicar mensajes MQTT en los *topics* definidos para cada escenario.

El programa Python recibe esos mensajes, los interpreta y ejecuta la acción correspondiente.

## Flujo principal

### Solicitud de medicamento

1. La ESP32_Pedido publica un mensaje MQTT.
2. Python consulta PostgreSQL.
3. Se verifica stock disponible.
4. Se reserva el medicamento.
5. Se obtiene la posición.
6. Se envía la orden a RoboDK.

### Registro de almacenamiento

1. La ESP32_Almacenamiento publica un mensaje MQTT.
2. Python actualiza PostgreSQL.
3. Se incrementa stock.
4. Se actualiza posición, estado y caducidad.

RoboDK representa visualmente:

- Aparición de cajas
- Movimiento de cintas
- Clasificación de medicamentos

---

# 3. Escenario de integración 1: solicitud de medicamento con ESP32_Pedido

## 3.1. Descripción del escenario

En este escenario se utiliza la ESP32_Pedido para solicitar medicamentos mediante botones físicos conectados a una ESP32-S3.

Cada botón está asociado a:

- Un medicamento
- Un color

Cuando el usuario pulsa un botón:

1. Se genera automáticamente un pedido.
2. La ESP32 envía un mensaje MQTT.
3. Python recibe la solicitud.
4. PostgreSQL verifica stock disponible.
5. Se reserva el medicamento.
6. RoboDK utiliza la posición obtenida para la simulación.

Los pedidos se procesan mediante una cola FIFO implementada en Python.

---

## 3.2. Participantes

- ESP32_Pedido  
- Broker MQTT  
- Programa Python controlador  
- PostgreSQL  
- Botones físicos  
- LED RGB  
- RoboDK  

---

## 3.3. Integración mediante MQTT

### Topic de solicitud

```text
giirob/pr2/grupo2equipo5/pedido/request
```

### Mensaje JSON

```json
{
  "id_pedido": "11-azul-123456",
  "device_id": "giirobpr2-11",
  "tipo": "Ibuprofeno",
  "cantidad": 1,
  "color": "azul",
  "gpio": 17
}
```

### Topic de estado

```text
giirob/pr2/grupo2equipo5/pedido/status
```

### Respuesta JSON

```json
{
  "id_pedido": "11-azul-123456",
  "estado": "preparando",
  "tipo": "Ibuprofeno",
  "cantidad": 1,
  "color": "azul",
  "posicion": "X01-Y02",
  "mensaje": "Pedido reservado; enviando RoboDK a X01-Y02",
  "origen": "python-db-robodk"
}
```

### Topic de confirmación

```text
giirob/pr2/grupo2equipo5/pedido/conseguido
```

### Confirmación JSON

```json
{
  "id_pedido": "11-azul-123456",
  "estado": "conseguido",
  "tipo": "Ibuprofeno",
  "color": "azul",
  "posicion": "X01-Y02"
}
```

---

## 3.4. Canales de estado y control

```text
giirob/pr2/grupo2equipo5/pedido/status
giirob/pr2/grupo2equipo5/pedido/command
giirob/pr2/grupo2equipo5/pedido/conseguido
```

---

## 3.5. Flujo de funcionamiento

1. El usuario pulsa un botón.
2. La ESP32 identifica el medicamento.
3. Se genera el pedido.
4. Se publica el mensaje MQTT.
5. Python recibe el mensaje.
6. El pedido entra en una cola FIFO.
7. PostgreSQL verifica stock.
8. Se reserva el medicamento.
9. Se obtiene la posición.
10. RoboDK realiza la simulación.
11. Python publica el estado.
12. Se publica la confirmación final.
13. La ESP32 activa el LED RGB correspondiente.

---

## 3.6. Montaje físico de la ESP32_Pedido

El montaje físico utiliza:

- ESP32-S3
- Protoboard
- Pulsadores
- Resistencias
- LEDs RGB

Cada botón se conecta a un GPIO específico y representa un medicamento concreto.

> **Figura 1.** Montaje físico de la ESP32_Pedido sobre protoboard.

---

# 4. Escenario de integración 2: registro de almacenamiento mediante ESP32_Almacenamiento

## 4.1. Descripción del escenario

Este escenario registra medicamentos almacenados en posiciones concretas de la estantería.

La ESP32-S3 envía:

- Tipo de medicamento
- Código de barras
- Posición
- Caducidad
- Cantidad

Ejemplo de posición:

```text
X01-Y02
```

Python actualiza PostgreSQL:

- Incrementa stock
- Actualiza posición
- Actualiza estado
- Actualiza caducidad

---

## 4.2. Participantes

- ESP32_Almacenamiento  
- Broker MQTT  
- Programa Python  
- PostgreSQL  
- RoboDK  

---

## 4.3. Integración mediante MQTT

### Topic principal

```text
giirob/pr2/grupo2equipo5/almacen/registro
```

### Mensaje JSON

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

### Topic de estado

```text
giirob/pr2/grupo2equipo5/almacen/status
```

### Respuesta JSON

```json
{
  "id_evento": "ALM-1",
  "estado": "registrado",
  "tipo": "Ibuprofeno",
  "posicion": "X01-Y02",
  "origen": "python-db"
}
```

---

## 4.4. Canales de estado y control

```text
giirob/pr2/grupo2equipo5/almacen/status
giirob/pr2/grupo2equipo5/almacen/command
```

---

## 4.5. Flujo de funcionamiento

1. Se registra un medicamento.
2. La ESP32 genera el mensaje MQTT.
3. El broker distribuye el mensaje.
4. Python interpreta los datos.
5. PostgreSQL busca el medicamento.
6. Se actualiza stock y posición.
7. Python publica el estado.
8. Los datos quedan disponibles en PostgreSQL.

---

# 5. Base de datos

La base de datos utilizada es PostgreSQL y se gestiona mediante pgAdmin.

## Tablas principales

- Medicamento
- Cliente
- Venta
- Caja_Grande
- Cinta_Transportadora
- Sensor
- Robot
- Herramienta
- Contiene

La tabla más importante es:

## Medicamento

Campos principales:

- id_medicamento
- cod_barras
- nombre
- caducidad
- stock
- estado
- pos
- precio_venta
- seguro_SS

## Ejemplo de actualización SQL

```sql
UPDATE Medicamento
SET stock = stock + 1,
    pos = 'X01-Y02',
    estado = 'almacenado'
WHERE nombre = 'Ibuprofeno';
```

---

# 6. Integración con RoboDK

La integración se realiza mediante scripts Python asociados a la estación RoboDK.

## Elementos utilizados

### Robot

- UR3e Base - Clasificación

### Herramienta

- RobotiQ EPick Vacuum Gripper (1 Cup)

### Targets

- Place_base
- Paso
- Target 2
- Target 3

---

## Parámetros de colocación

```python
ancho_caja = 125
fondo_caja = 66
alto_caja = 62.5
gap = 30
dx = ancho_caja + gap
dz = 215
```

La matriz de almacenamiento tiene:

- 3 columnas
- 2 filas
- 3 niveles

Total:

```text
3 x 2 x 3 = 18 posiciones
```

---

## Scripts principales

- ApareceCaja.py
- AvanzaCaja.py
- CintaPick.py
- AvanzaPick.py
- AvanzaPlace.py
- ProgramaClasificacion.py
- Reset.py
- ResetPick.py

---

## Modos de funcionamiento

### Simulación

```text
ROBODK_MODE=sim
```

### Real

```text
ROBODK_MODE=real
```

---

# 7. Justificación de Programación Avanzada y Gestión de Datos

## 7.1. Relación con PRA

Se utilizan conceptos de Programación Avanzada:

- Tablas hash
- Colas FIFO
- Programación modular
- Comunicación asíncrona
- Programación basada en eventos

## Tabla hash en Python

```python
posiciones = {
    "Ibuprofeno": ["X01-Y01", "X01-Y02"],
    "Paracetamol": ["X02-Y01", "X02-Y02"],
    "Enantyum": ["X03-Y01", "X03-Y02"]
}
```

La cola FIFO permite procesar los pedidos en orden de llegada.

Los mensajes JSON se interpretan en Python como diccionarios.

---

## 7.2. Relación con GDI

La Gestión de Datos se basa en PostgreSQL.

La base de datos permite:

- Mantener inventario
- Gestionar stock
- Consultar posiciones
- Actualizar estados
- Mantener trazabilidad

## Ejemplo SQL

```sql
UPDATE Medicamento
SET stock = stock - 1
WHERE nombre = 'Ibuprofeno';
```

## Consulta SQL

```sql
SELECT nombre, stock, pos
FROM Medicamento
WHERE nombre = 'Ibuprofeno';
```

---

# 8. Pruebas de funcionamiento

## Pasos previos

1. Ejecutar el programa de despaletizado.
2. Ejecutar ProgramaClasificacion.py.
3. Iniciar PostgreSQL.
4. Ejecutar el programa Python MQTT.
5. Abrir RoboDK.
6. Conectar ESP32-S3.
7. Ejecutar MQTTX.
8. Utilizar la demo web.

---

## Verificaciones realizadas

- Comunicación MQTT correcta
- Actualización automática en PostgreSQL
- Funcionamiento de la cola FIFO
- Recepción de mensajes JSON
- Simulación robótica en RoboDK
- Funcionamiento del LED RGB
- Integración ESP32 ↔ Python ↔ PostgreSQL ↔ RoboDK

Durante las pruebas se utilizó:

```text
broker.hivemq.com
```

---

# 9. Conclusiones

Con este proyecto se ha conseguido integrar distintos elementos hardware y software dentro de una misma solución de automatización.

Se han conectado:

- ESP32-S3
- MQTT
- Python
- PostgreSQL
- RoboDK

Las pruebas permitieron validar:

- Envío y recepción de mensajes MQTT
- Actualización automática de PostgreSQL
- Simulación robótica en RoboDK
- Gestión de inventario
- Integración IoT

Además, se aplicaron conceptos de:

- Programación Avanzada
- Gestión de Datos
- Comunicación asíncrona
- Bases de datos relacionales

Aunque todavía existen algunos problemas de sincronización entre MQTT y RoboDK, el sistema funciona correctamente de forma general y demuestra una integración funcional entre comunicación IoT, gestión de datos y simulación robótica.
