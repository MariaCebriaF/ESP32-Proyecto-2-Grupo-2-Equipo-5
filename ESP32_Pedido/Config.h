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
#define MQTT_USERNAME "giirob"
#define MQTT_PASSWORD "UPV2024"

// Topics del escenario de pedido
#define BASE_TOPIC "giirob/pr2/grupo2equipo5"
#define PEDIDO_REQUEST_TOPIC BASE_TOPIC "/pedido/request"
#define PEDIDO_STATUS_TOPIC BASE_TOPIC "/pedido/status"
#define PEDIDO_COMMAND_TOPIC BASE_TOPIC "/pedido/command"

// IO
#define LED_BUILTIN 2
#define BUTTON_PIN 4

// El pulsador de las practicas suele cablearse con pull-up: pulsado = LOW.
#define BUTTON_PRESSED LOW
