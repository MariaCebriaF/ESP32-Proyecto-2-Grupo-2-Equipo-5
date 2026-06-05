// COMM BAUDS
#define BAUDS 115200

#define LOGGER_ENABLED
#define LOG_LEVEL INFO

// DEVICE
#define DEVICE_GIIROB_PR2_ID "grupo2equipo5-pedido"

// WIFI
#define NET_SSID "RedPR2"
#define NET_PASSWD "megustalatortilla"

// MQTT
#define MQTT_SERVER_IP "broker.hivemq.com"
#define MQTT_SERVER_PORT 1883
// HiveMQ publico no necesita usuario ni contrasena.
// #define MQTT_USERNAME "giirob"
// #define MQTT_PASSWORD "UPV2024"

// Topics del escenario de pedido
#define BASE_TOPIC "giirob/pr2/grupo2equipo5"
#define PEDIDO_REQUEST_TOPIC BASE_TOPIC "/pedido/request"
#define PEDIDO_STATUS_TOPIC BASE_TOPIC "/pedido/status"
#define PEDIDO_COMMAND_TOPIC BASE_TOPIC "/pedido/command"

// IO
#ifndef RGB_BUILTIN
  #define RGB_BUILTIN 48
#endif

#define RGB_LED_PIN RGB_BUILTIN
#define RGB_LED_BRIGHTNESS 40
#define BUTTON_PARACETAMOL_PIN 18
#define BUTTON_IBUPROFENO_PIN 17
#define BUTTON_ENANTYUM_PIN 16

// El pulsador de las practicas suele cablearse con pull-up: pulsado = LOW.
#define BUTTON_PRESSED LOW
