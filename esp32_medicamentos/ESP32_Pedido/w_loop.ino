unsigned long lastButtonChange = 0;
uint8_t lastButtonState = !BUTTON_PRESSED;
const unsigned long debounceMs = 80;

void on_loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processSerialCommand(command);
  }

  uint8_t currentButtonState = digitalRead(BUTTON_PIN);
  unsigned long now = millis();

  if (currentButtonState != lastButtonState && now - lastButtonChange > debounceMs) {
    lastButtonChange = now;
    lastButtonState = currentButtonState;

    if (currentButtonState == BUTTON_PRESSED) {
      publishSelectedDemoRequest();
    }
  }
}
