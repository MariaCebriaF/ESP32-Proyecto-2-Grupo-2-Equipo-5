void suscribirseATopics() {
  mqtt_subscribe(ALMACEN_COMMAND_TOPIC);
  mqtt_subscribe(ALMACEN_STATUS_TOPIC);
  mqtt_subscribe(PRUEBA_TOPIC);
}

void alRecibirMensajePorTopic(char* topic, String incomingMessage) {
  incomingMessage.trim();

  if (strcmp(topic, ALMACEN_STATUS_TOPIC) == 0) {
    infoln("Estado recibido del integrador:");
    infoln(incomingMessage);
    setInternalLed(incomingMessage.indexOf("registrado") >= 0 ? 1 : 0);
    return;
  }

  if (strcmp(topic, ALMACEN_COMMAND_TOPIC) == 0) {
    if (incomingMessage == "demo") {
      publishSelectedDemoMedicine();
    } else if (incomingMessage == "pos") {
      publishStatus("posicion_actual", currentRackPosition().c_str());
    } else if (incomingMessage.startsWith("set_pos ")) {
      incomingMessage.remove(0, 8);
      int separator = incomingMessage.indexOf(' ');

      if (separator < 0) {
        warnln("Formato MQTT invalido. Usa: set_pos x y");
        return;
      }

      uint8_t x = incomingMessage.substring(0, separator).toInt();
      uint8_t y = incomingMessage.substring(separator + 1).toInt();
      setRackPosition(x, y);
      publishStatus("posicion_ajustada", currentRackPosition().c_str());
    } else if (incomingMessage == "led_on") {
      setInternalLed(1);
    } else if (incomingMessage == "led_off") {
      setInternalLed(0);
    } else {
      warnln("Comando MQTT de almacenamiento no reconocido.");
    }
  }
}

void enviarMensajePorTopic(const char* topic, String outgoingMessage) {
  mqtt_publish(topic, outgoingMessage);
}
