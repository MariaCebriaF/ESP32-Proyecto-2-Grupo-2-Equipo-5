uint8_t ledStatus = 0;
unsigned long eventCounter = 1;
uint8_t rackX = RACK_START_X;
uint8_t rackY = RACK_START_Y;

struct MedicineSlot {
  const char* tipo;
  const char* codBarras;
  const char* posicion;
  const char* caducidad;
  uint8_t cantidad;
};

MedicineSlot demoMedicines[] = {
  {"Paracetamol", "847000100001", "", "2027-05-01", 1},
  {"Ibuprofeno", "847000100002", "", "2027-08-15", 1},
  {"Enantyum", "847000100003", "", "2026-12-20", 1}
};

const uint8_t demoMedicineCount = sizeof(demoMedicines) / sizeof(demoMedicines[0]);
uint8_t selectedMedicine = 0;

void setInternalLed(uint8_t status) {
  if (ledStatus == status) {
    return;
  }

  ledStatus = status;
  digitalWrite(LED_BUILTIN, status ? HIGH : LOW);
}

void publishStorageEvent(const char* tipo, const char* codBarras, const char* posicion, const char* caducidad, uint8_t cantidad) {
  JsonDocument doc;
  String eventId = String("ALM-") + String(eventCounter++);

  doc["id_evento"] = eventId;
  doc["device_id"] = deviceID;
  doc["tipo"] = tipo;
  doc["cod_barras"] = codBarras;
  doc["posicion"] = posicion;
  doc["caducidad"] = caducidad;
  doc["cantidad"] = cantidad;

  String payload;
  serializeJson(doc, payload);

  infoln("Publicando registro de almacenamiento:");
  infoln(payload);
  enviarMensajePorTopic(ALMACEN_REGISTRO_TOPIC, payload);
}

void publishSelectedDemoMedicine() {
  MedicineSlot medicine = demoMedicines[selectedMedicine];
  String posicion = currentRackPosition();
  publishStorageEvent(medicine.tipo, medicine.codBarras, posicion.c_str(), medicine.caducidad, medicine.cantidad);
  advanceRackPosition();

  selectedMedicine = (selectedMedicine + 1) % demoMedicineCount;
}

String currentRackPosition() {
  char position[10];
  snprintf(position, sizeof(position), "X%02u-Y%02u", rackX, rackY);
  return String(position);
}

void advanceRackPosition() {
  rackY++;

  if (rackY > RACK_MAX_Y) {
    rackY = RACK_START_Y;
    rackX++;
  }

  if (rackX > RACK_MAX_X) {
    rackX = RACK_START_X;
  }

  info("Siguiente posicion simulada: ");
  infoln(currentRackPosition());
}

void setRackPosition(uint8_t x, uint8_t y) {
  if (x < RACK_START_X || x > RACK_MAX_X || y < RACK_START_Y || y > RACK_MAX_Y) {
    warnln("Posicion fuera de rango.");
    return;
  }

  rackX = x;
  rackY = y;

  info("Contador de estanteria ajustado a: ");
  infoln(currentRackPosition());
}

void publishStatus(const char* estado, const char* mensaje) {
  JsonDocument doc;
  doc["device_id"] = deviceID;
  doc["estado"] = estado;
  doc["mensaje"] = mensaje;

  String payload;
  serializeJson(doc, payload);
  enviarMensajePorTopic(ALMACEN_STATUS_TOPIC, payload);
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
    publishSelectedDemoMedicine();
    return;
  }

  if (command == "POS") {
    info("Posicion actual: ");
    infoln(currentRackPosition());
    return;
  }

  if (command.startsWith("SET_POS ")) {
    command.remove(0, 8);
    int separator = command.indexOf(' ');

    if (separator < 0) {
      warnln("Formato invalido. Usa: SET_POS x y");
      return;
    }

    uint8_t x = command.substring(0, separator).toInt();
    uint8_t y = command.substring(separator + 1).toInt();
    setRackPosition(x, y);
    return;
  }

  if (command.startsWith("REG_AUTO ")) {
    command.remove(0, 9);

    int p1 = command.indexOf(' ');
    int p2 = command.indexOf(' ', p1 + 1);
    int p3 = command.indexOf(' ', p2 + 1);

    if (p1 < 0 || p2 < 0 || p3 < 0) {
      warnln("Formato invalido. Usa: REG_AUTO tipo cod_barras caducidad cantidad");
      return;
    }

    String tipo = command.substring(0, p1);
    String codBarras = command.substring(p1 + 1, p2);
    String caducidad = command.substring(p2 + 1, p3);
    uint8_t cantidad = command.substring(p3 + 1).toInt();

    if (cantidad == 0) {
      cantidad = 1;
    }

    String posicion = currentRackPosition();
    publishStorageEvent(tipo.c_str(), codBarras.c_str(), posicion.c_str(), caducidad.c_str(), cantidad);
    advanceRackPosition();
    return;
  }

  if (!command.startsWith("REG ")) {
    warnln("Comando no reconocido. Escribe HELP para ver el formato.");
    return;
  }

  command.remove(0, 4);

  int p1 = command.indexOf(' ');
  int p2 = command.indexOf(' ', p1 + 1);
  int p3 = command.indexOf(' ', p2 + 1);
  int p4 = command.indexOf(' ', p3 + 1);

  if (p1 < 0 || p2 < 0 || p3 < 0 || p4 < 0) {
    warnln("Formato invalido. Usa: REG tipo posicion cod_barras caducidad cantidad");
    return;
  }

  String tipo = command.substring(0, p1);
  String posicion = command.substring(p1 + 1, p2);
  String codBarras = command.substring(p2 + 1, p3);
  String caducidad = command.substring(p3 + 1, p4);
  uint8_t cantidad = command.substring(p4 + 1).toInt();

  if (cantidad == 0) {
    cantidad = 1;
  }

  publishStorageEvent(tipo.c_str(), codBarras.c_str(), posicion.c_str(), caducidad.c_str(), cantidad);
}

void printSerialHelp() {
  infoln("Comandos disponibles:");
  infoln("  DEMO");
  infoln("  POS");
  infoln("  SET_POS x y");
  infoln("  REG_AUTO tipo cod_barras caducidad cantidad");
  infoln("  REG tipo posicion cod_barras caducidad cantidad");
  infoln("Ejemplo:");
  infoln("  SET_POS 2 1");
  infoln("  REG_AUTO Ibuprofeno 847000100002 2027-08-15 1");
  infoln("  REG Ibuprofeno A01-B02 847000100002 2027-08-15 1");
}
