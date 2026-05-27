uint8_t lastParacetamolState = !BUTTON_PRESSED;
uint8_t lastIbuprofenoState = !BUTTON_PRESSED;
uint8_t lastEnantyumState = !BUTTON_PRESSED;

unsigned long lastParacetamolChange = 0;
unsigned long lastIbuprofenoChange = 0;
unsigned long lastEnantyumChange = 0;

const unsigned long debounceMs = 80;

void on_loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processSerialCommand(command);
  }

  checkParacetamolButton();
  checkIbuprofenoButton();
  checkEnantyumButton();
}

void checkParacetamolButton() {
  uint8_t currentState = digitalRead(BUTTON_PARACETAMOL_PIN);
  unsigned long now = millis();

  if (currentState != lastParacetamolState && now - lastParacetamolChange > debounceMs) {
    lastParacetamolChange = now;
    lastParacetamolState = currentState;

    if (currentState == BUTTON_PRESSED) {
      Serial.println("PULSADO GPIO18 -> Paracetamol");
      publishParacetamolRequest();
    }
  }
}

void checkIbuprofenoButton() {
  uint8_t currentState = digitalRead(BUTTON_IBUPROFENO_PIN);
  unsigned long now = millis();

  if (currentState != lastIbuprofenoState && now - lastIbuprofenoChange > debounceMs) {
    lastIbuprofenoChange = now;
    lastIbuprofenoState = currentState;

    if (currentState == BUTTON_PRESSED) {
      Serial.println("PULSADO GPIO17 -> Ibuprofeno");
      publishIbuprofenoRequest();
    }
  }
}

void checkEnantyumButton() {
  uint8_t currentState = digitalRead(BUTTON_ENANTYUM_PIN);
  unsigned long now = millis();

  if (currentState != lastEnantyumState && now - lastEnantyumChange > debounceMs) {
    lastEnantyumChange = now;
    lastEnantyumState = currentState;

    if (currentState == BUTTON_PRESSED) {
      Serial.println("PULSADO GPIO16 -> Enantyum");
      publishEnantyumRequest();
    }
  }
}
