# ESP32 medicamentos - Grupo 2 Equipo 5

Este repositorio contiene dos sketches Arduino para la comunicación y las acciones de las ESP32s basados en lo visto en clase y previsto para cumplir con las especificadas de la tarea del desarrollo de software del proyecto `ESP32-S3-IoT-Device`.

## 1. ESP32_Almacenamiento

Su objetivo es el de registrar que un medicamento de tipo X se ha guardado en una posicion concreta.

Se publicará en el canal (mediante MQTT):

```text
giirob/pr2/grupo2equipo5/almacen/registro
```

Mensaje:

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

La posicion puede enviarse manualmente o generarse con un contador interno `X/Y`, pensado para ir sincronizado con la matriz de posiciones de RoboDK. Por defecto empieza en `X01-Y01`, avanza primero en `Y`, luego en `X`, y vuelve al inicio al llenar la matriz configurada en `Config.h`.

Esta ESP32 lee el contenido en:

```text
giirob/pr2/grupo2equipo5/almacen/status
giirob/pr2/grupo2equipo5/almacen/command
```

Comandos configurados para el monitor serie:

```text
HELP
DEMO
POS
SET_POS 2 1
REG_AUTO Ibuprofeno 847000100002 2027-08-15 1
REG Ibuprofeno X01-Y02 847000100002 2027-08-15 1
```

## 2. ESP32_Pedido

Su objetivo es el de solicitar al sistema un medicamento de tipo X.

En esta caso se comunica en el canal (otra vez mediante MQTT):

```text
giirob/pr2/grupo2equipo5/pedido/request
```

Mensaje:

```json
{
  "id_pedido": "PED-1",
  "device_id": "giirobpr2-grupo2equipo5-pedido",
  "tipo": "Ibuprofeno",
  "cantidad": 1
}
```

En este caso lee el contenido de los canales:

```text
giirob/pr2/grupo2equipo5/pedido/status
giirob/pr2/grupo2equipo5/pedido/command
```


# ESP32-Proyecto-2-Grupo-2-Equipo-5
