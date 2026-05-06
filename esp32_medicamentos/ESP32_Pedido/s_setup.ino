void on_setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  setInternalLed(0);
  printSerialHelp();
}
