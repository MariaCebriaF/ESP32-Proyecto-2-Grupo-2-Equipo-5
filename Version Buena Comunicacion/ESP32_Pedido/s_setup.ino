void on_setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(BUTTON_PARACETAMOL_PIN, INPUT_PULLUP);
  pinMode(BUTTON_IBUPROFENO_PIN, INPUT_PULLUP);
  pinMode(BUTTON_ENANTYUM_PIN, INPUT_PULLUP);

  setInternalLed(0);
  printSerialHelp();
}
