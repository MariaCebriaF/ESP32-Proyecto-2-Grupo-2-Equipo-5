void on_setup() {
  pinMode(RGB_LED_PIN, OUTPUT);
  pinMode(BUTTON_PARACETAMOL_PIN, INPUT_PULLUP);
  pinMode(BUTTON_IBUPROFENO_PIN, INPUT_PULLUP);
  pinMode(BUTTON_ENANTYUM_PIN, INPUT_PULLUP);

  setRgbLedOff();
  printSerialHelp();
}
