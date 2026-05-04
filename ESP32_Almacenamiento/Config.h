// COMM BAUDS
#define BAUDS 115200

#define LOGGER_ENABLED
#define LOG_LEVEL INFO

// DEVICE
#define DEVICE_GIIROB_PR2_ID "grupo2equipo5-almacen"

// WIFI
#define NET_SSID "RedPR2"
#define NET_PASSWD "megustalatortilla"

// MQTT
#define MQTT_SERVER_IP "broker.hivemq.com"
#define MQTT_SERVER_PORT 1883
#define MQTT_USERNAME "giirob"
#define MQTT_PASSWORD "UPV2024"

// Topics del escenario de almacenamiento
#define BASE_TOPIC "giirob/pr2/grupo2equipo5"
#define ALMACEN_REGISTRO_TOPIC BASE_TOPIC "/almacen/registro"
#define ALMACEN_STATUS_TOPIC BASE_TOPIC "/almacen/status"
#define ALMACEN_COMMAND_TOPIC BASE_TOPIC "/almacen/command"
#define PRUEBA_TOPIC "prueba/esp32"

// IO
#define LED_BUILTIN 2
#define BUTTON_PIN 4

// El pulsador de las practicas suele cablearse con pull-up: pulsado = LOW.
#define BUTTON_PRESSED LOW

// Estanteria simulada. Debe coincidir con la matriz de posiciones usada en RoboDK.
#define RACK_MAX_X 4
#define RACK_MAX_Y 3
#define RACK_START_X 1
#define RACK_START_Y 1
