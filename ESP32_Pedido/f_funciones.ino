uint8_t ledStatus = 0;
unsigned long requestCounter = 1;

void publishMedicineRequest(const char* tipo, uint8_t cantidad);
void publishMedicineRequest(const char* tipo, uint8_t cantidad, uint8_t gpio);
void publishParacetamolRequest();
void publishIbuprofenoRequest();
void publishEnantyumRequest();
void printSerialHelp();

struct MedicineRequest {
  const char* tipo;
  uint8_t cantidad;
};

MedicineRequest demoRequests[] = {
  {"Paracetamol", 1},
  {"Ibuprofeno", 1},
  {"Enantyum", 1}
};

const uint8_t demoRequestCount = sizeof(demoRequests) / sizeof(demoRequests[0]);
uint8_t selectedRequest = 0;

void setInternalLed(uint8_t status) {
  if (ledStatus == status) {
    return;
  }

  ledStatus = status;
  digitalWrite(LED_BUILTIN, status ? HIGH : LOW);
}

void publishMedicineRequest(const char* tipo, uint8_t cantidad) {
  publishMedicineRequest(tipo, cantidad, 0);
}

void publishMedicineRequest(const char* tipo, uint8_t cantidad, uint8_t gpio) {
  JsonDocument doc;
  String requestId = String("PED-") + String(requestCounter++);

  doc["id_pedido"] = requestId;
  doc["device_id"] = deviceID;
  doc["tipo"] = tipo;
  doc["cantidad"] = cantidad == 0 ? 1 : cantidad;
  if (gpio > 0) {
    doc["gpio"] = gpio;
  }

  String payload;
  serializeJson(doc, payload);

  Serial.print("BOTON/PEDIDO -> tipo=");
  Serial.print(tipo);
  Serial.print(" cantidad=");
  Serial.print(cantidad == 0 ? 1 : cantidad);
  if (gpio > 0) {
    Serial.print(" gpio=");
    Serial.print(gpio);
  }
  Serial.print(" topic=");
  Serial.println(PEDIDO_REQUEST_TOPIC);

  infoln("Publicando solicitud de medicamento:");
  infoln(payload);
  enviarMensajePorTopic(PEDIDO_REQUEST_TOPIC, payload);
}

void publishParacetamolRequest() {
  publishMedicineRequest("Paracetamol", 1, BUTTON_PARACETAMOL_PIN);
}

void publishIbuprofenoRequest() {
  publishMedicineRequest("Ibuprofeno", 1, BUTTON_IBUPROFENO_PIN);
}

void publishEnantyumRequest() {
  publishMedicineRequest("Enantyum", 1, BUTTON_ENANTYUM_PIN);
}

void publishSelectedDemoRequest() {
  MedicineRequest request = demoRequests[selectedRequest];
  publishMedicineRequest(request.tipo, request.cantidad);

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
  const char* posicion = doc["posicion"] | "";
  const char* mensaje = doc["mensaje"] | "";

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

  if (strcmp(estado, "preparando") == 0 || strcmp(estado, "entregado") == 0) {
    setInternalLed(1);
  } else if (strcmp(estado, "no_disponible") == 0 || strcmp(estado, "error") == 0) {
    setInternalLed(0);
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
    publishMedicineRequest(command.c_str(), 1);
    return;
  }

  String tipo = command.substring(0, p1);
  uint8_t cantidad = command.substring(p1 + 1).toInt();

  if (cantidad == 0) {
    cantidad = 1;
  }

  publishMedicineRequest(tipo.c_str(), cantidad);
}

void printSerialHelp() {
  infoln("Comandos disponibles:");
  infoln("  DEMO");
  infoln("  PED tipo cantidad");
  infoln("Ejemplo:");
  infoln("  PED Ibuprofeno 1");
}
