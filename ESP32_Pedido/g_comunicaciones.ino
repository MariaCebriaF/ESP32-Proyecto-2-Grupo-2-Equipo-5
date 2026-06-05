void suscribirseATopics() {
  mqtt_subscribe(PEDIDO_STATUS_TOPIC);
  mqtt_subscribe(PEDIDO_COMMAND_TOPIC);
}

void alRecibirMensajePorTopic(char* topic, String incomingMessage) {
  incomingMessage.trim();

  if (strcmp(topic, PEDIDO_STATUS_TOPIC) == 0) {
    infoln("Estado recibido del integrador:");
    infoln(incomingMessage);
    processOrderStatus(incomingMessage);
    return;
  }

  if (strcmp(topic, PEDIDO_COMMAND_TOPIC) == 0) {
    if (incomingMessage == "demo") {
      publishSelectedDemoRequest();
    } else if (incomingMessage == "led_on") {
      setRgbLedWhite();
    } else if (incomingMessage == "led_off") {
      setRgbLedOff();
    } else {
      warnln("Comando MQTT de pedido no reconocido.");
    }
  }
}

void enviarMensajePorTopic(const char* topic, String outgoingMessage) {
  mqtt_publish(topic, outgoingMessage);
}
