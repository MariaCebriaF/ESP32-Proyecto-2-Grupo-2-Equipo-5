uint8_t currentLedMedicine = 0;
unsigned long requestCounter = 1;

uint8_t medicineIdFromType(const char* tipo);
void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad);
void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad, uint8_t gpio);
void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad, uint8_t gpio, const char* color);
void publishParacetamolRequest();
void publishIbuprofenoRequest();
void publishEnantyumRequest();
void printSerialHelp();
const char* colorFromMedicineId(uint8_t tipoId);
void setRgbLed(uint8_t red, uint8_t green, uint8_t blue);
void setRgbLedOff();
void setRgbLedError();
void setRgbLedWhite();
void setMedicineRgbLed(uint8_t tipoId);

struct MedicineRequest {
  uint8_t tipoId;
  const char* tipo;
  uint8_t cantidad;
  const char* color;
};

MedicineRequest demoRequests[] = {
  {1, "Paracetamol", 1, "verde"},
  {2, "Ibuprofeno", 1, "azul"},
  {3, "Enantyum", 1, "rojo"}
};

const uint8_t demoRequestCount = sizeof(demoRequests) / sizeof(demoRequests[0]);
uint8_t selectedRequest = 0;

const char* colorFromMedicineId(uint8_t tipoId) {
  if (tipoId == 1) {
    return "verde";
  }
  if (tipoId == 2) {
    return "azul";
  }
  if (tipoId == 3) {
    return "rojo";
  }
  return "";
}

void setRgbLed(uint8_t red, uint8_t green, uint8_t blue) {
  neopixelWrite(RGB_LED_PIN, red, green, blue);
}

void setRgbLedOff() {
  currentLedMedicine = 0;
  setRgbLed(0, 0, 0);
}

void setRgbLedError() {
  currentLedMedicine = 0;
  setRgbLed(RGB_LED_BRIGHTNESS, 0, 0);
}

void setRgbLedWhite() {
  currentLedMedicine = 0;
  setRgbLed(RGB_LED_BRIGHTNESS, RGB_LED_BRIGHTNESS, RGB_LED_BRIGHTNESS);
}

void setMedicineRgbLed(uint8_t tipoId) {
  if (currentLedMedicine == tipoId) {
    return;
  }

  currentLedMedicine = tipoId;

  if (tipoId == 1) {
    setRgbLed(0, RGB_LED_BRIGHTNESS, 0);
  } else if (tipoId == 2) {
    setRgbLed(0, 0, RGB_LED_BRIGHTNESS);
  } else if (tipoId == 3) {
    setRgbLed(RGB_LED_BRIGHTNESS, 0, 0);
  } else {
    setRgbLedOff();
  }
}

uint8_t medicineIdFromType(const char* tipo) {
  String normalized = String(tipo);
  normalized.trim();
  normalized.toLowerCase();

  if (normalized == "paracetamol") {
    return 1;
  }
  if (normalized == "ibuprofeno") {
    return 2;
  }
  if (normalized == "enantyum" || normalized == "amoxicilina") {
    return 3;
  }
  return 0;
}

void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad) {
  publishMedicineRequest(tipoId, tipo, cantidad, 0, colorFromMedicineId(tipoId));
}

void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad, uint8_t gpio) {
  publishMedicineRequest(tipoId, tipo, cantidad, gpio, colorFromMedicineId(tipoId));
}

void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad, uint8_t gpio, const char* color) {
  JsonDocument doc;
  String requestId = String("PED-") + String(requestCounter++);
  uint8_t resolvedTipoId = tipoId == 0 ? medicineIdFromType(tipo) : tipoId;
  const char* resolvedColor = strlen(color) > 0 ? color : colorFromMedicineId(resolvedTipoId);

  doc["id_pedido"] = requestId;
  doc["device_id"] = deviceID;
  doc["tipo_id"] = resolvedTipoId;
  doc["tipo"] = tipo;
  doc["cantidad"] = cantidad == 0 ? 1 : cantidad;
  if (strlen(resolvedColor) > 0) {
    doc["color"] = resolvedColor;
  }
  if (gpio > 0) {
    doc["gpio"] = gpio;
  }

  String payload;
  serializeJson(doc, payload);

  Serial.print("BOTON/PEDIDO -> tipo_id=");
  Serial.print(resolvedTipoId);
  Serial.print(" tipo=");
  Serial.print(tipo);
  Serial.print(" cantidad=");
  Serial.print(cantidad == 0 ? 1 : cantidad);
  if (strlen(resolvedColor) > 0) {
    Serial.print(" color=");
    Serial.print(resolvedColor);
  }
  if (gpio > 0) {
    Serial.print(" gpio=");
    Serial.print(gpio);
  }
  Serial.print(" topic=");
  Serial.println(PEDIDO_REQUEST_TOPIC);

  infoln("Publicando solicitud de medicamento:");
  infoln(payload);
  setMedicineRgbLed(resolvedTipoId);
  enviarMensajePorTopic(PEDIDO_REQUEST_TOPIC, payload);
}

void publishParacetamolRequest() {
  publishMedicineRequest(1, "Paracetamol", 1, BUTTON_PARACETAMOL_PIN, "verde");
}

void publishIbuprofenoRequest() {
  publishMedicineRequest(2, "Ibuprofeno", 1, BUTTON_IBUPROFENO_PIN, "azul");
}

void publishEnantyumRequest() {
  publishMedicineRequest(3, "Enantyum", 1, BUTTON_ENANTYUM_PIN, "rojo");
}

void publishSelectedDemoRequest() {
  MedicineRequest request = demoRequests[selectedRequest];
  publishMedicineRequest(request.tipoId, request.tipo, request.cantidad, 0, request.color);

  selectedRequest = (selectedRequest + 1) % demoRequestCount;
}

void processOrderStatus(String payload) {
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload);

  if (err) {
    warnln("No se pudo interpretar el estado del pedido como JSON.");
    infoln(payload);
    return;
  }

  const char* estado = doc["estado"] | "";
  const char* tipo = doc["tipo"] | "";
  const char* posicion = doc["posicion"] | "";
  const char* mensaje = doc["mensaje"] | "";
  uint8_t tipoId = doc["tipo_id"] | medicineIdFromType(tipo);

  info("Estado pedido: ");
  infoln(estado);

  if (strlen(posicion) > 0) {
    info("Posicion: ");
    infoln(posicion);
  }

  if (strlen(mensaje) > 0) {
    info("Mensaje: ");
    infoln(mensaje);
  }

  if (strcmp(estado, "preparando") == 0 || strcmp(estado, "entregado") == 0 || strcmp(estado, "conseguido") == 0) {
    setMedicineRgbLed(tipoId);
  } else if (strcmp(estado, "no_disponible") == 0 || strcmp(estado, "error") == 0 || strcmp(estado, "error_robot") == 0) {
    setRgbLedError();
  }
}

void processSerialCommand(String command) {
  command.trim();

  if (command.length() == 0) {
    return;
  }

  if (command == "HELP") {
    printSerialHelp();
    return;
  }

  if (command == "DEMO") {
    publishSelectedDemoRequest();
    return;
  }

  if (!command.startsWith("PED ")) {
    warnln("Comando no reconocido. Escribe HELP para ver el formato.");
    return;
  }

  command.remove(0, 4);

  int p1 = command.indexOf(' ');
  if (p1 < 0) {
    publishMedicineRequest(medicineIdFromType(command.c_str()), command.c_str(), 1);
    return;
  }

  String tipo = command.substring(0, p1);
  uint8_t cantidad = command.substring(p1 + 1).toInt();

  if (cantidad == 0) {
    cantidad = 1;
  }

  publishMedicineRequest(medicineIdFromType(tipo.c_str()), tipo.c_str(), cantidad);
}

void printSerialHelp() {
  infoln("Comandos disponibles:");
  infoln("  DEMO");
  infoln("  PED tipo cantidad");
  infoln("Ejemplo:");
  infoln("  PED Ibuprofeno 1");
}
