uint8_t ledStatus = 0;
unsigned long requestCounter = 1;

uint8_t medicineIdFromType(const char* tipo);
void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad);
void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad, uint8_t gpio);
void publishParacetamolRequest();
void publishIbuprofenoRequest();
void publishEnantyumRequest();
void printSerialHelp();

struct MedicineRequest {
  uint8_t tipoId;
  const char* tipo;
  uint8_t cantidad;
};

MedicineRequest demoRequests[] = {
  {1, "Paracetamol", 1},
  {2, "Ibuprofeno", 1},
  {3, "Enantyum", 1}
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
  publishMedicineRequest(tipoId, tipo, cantidad, 0);
}

void publishMedicineRequest(uint8_t tipoId, const char* tipo, uint8_t cantidad, uint8_t gpio) {
  JsonDocument doc;
  String requestId = String("PED-") + String(requestCounter++);
  uint8_t resolvedTipoId = tipoId == 0 ? medicineIdFromType(tipo) : tipoId;

  doc["id_pedido"] = requestId;
  doc["device_id"] = deviceID;
  doc["tipo_id"] = resolvedTipoId;
  doc["tipo"] = tipo;
  doc["cantidad"] = cantidad == 0 ? 1 : cantidad;
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
  publishMedicineRequest(1, "Paracetamol", 1, BUTTON_PARACETAMOL_PIN);
}

void publishIbuprofenoRequest() {
  publishMedicineRequest(2, "Ibuprofeno", 1, BUTTON_IBUPROFENO_PIN);
}

void publishEnantyumRequest() {
  publishMedicineRequest(3, "Enantyum", 1, BUTTON_ENANTYUM_PIN);
}

void publishSelectedDemoRequest() {
  MedicineRequest request = demoRequests[selectedRequest];
  publishMedicineRequest(request.tipoId, request.tipo, request.cantidad);

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
  } else if (strcmp(estado, "no_disponible") == 0 || strcmp(estado, "error") == 0 || strcmp(estado, "error_robot") == 0) {
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
