/*
 * PR2 - Grupo 2 Equipo 5
 * ESP32-S3 de solicitud de medicamentos.
 *
 * Publica por MQTT que se quiere dispensar un medicamento de tipo X.
 */
#include "Config.h"

#include <WiFi.h>
#ifdef SSL_ROOT_CA
  #include <WiFiClientSecure.h>
#endif
#include <PubSubClient.h>
#include <ArduinoJson.h>

String deviceID = String("giirobpr2-") + String(DEVICE_GIIROB_PR2_ID);

void setup() {
#ifdef LOGGER_ENABLED
  Serial.begin(BAUDS);
  delay(1000);
  Serial.println();
#endif

  wifi_connect();
  mqtt_connect(deviceID);
  suscribirseATopics();
  on_setup();
}

void loop() {
  wifi_loop();
  mqtt_loop();
  on_loop();
}
