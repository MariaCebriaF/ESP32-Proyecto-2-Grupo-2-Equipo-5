#define WIFI_CONNECTION_TIMEOUT_SECONDS 30
#define WIFI_RECONNECT_INTERVAL_MS 10000

// Usamos comunicaciones TLS/SSL si se define el certificado raíz CA
#ifdef SSL_ROOT_CA
  WiFiClientSecure espWifiClient;
#else
  WiFiClient espWifiClient;
#endif

const char* wifiSSID = NET_SSID;
const char* wifiPasswd = NET_PASSWD;
unsigned long lastWifiReconnectAttempt = 0;

void wifi_loop() {
  if (WiFi.isConnected()) {
    return;
  }

  if (WiFi.status() == WL_IDLE_STATUS) {
    return;
  }

  if (millis() - lastWifiReconnectAttempt > WIFI_RECONNECT_INTERVAL_MS) {
    wifi_reconnect(WIFI_CONNECTION_TIMEOUT_SECONDS);
  }
}

void wifi_connect() {

  delay(10);

  WiFi.mode(WIFI_STA); //Optional
  WiFi.persistent(false);
  WiFi.setSleep(false);
  trace("MAC Address: ");
  traceln(WiFi.macAddress());
  wifi_scan_networks();

#ifdef SSL_ROOT_CA
  // Set Root CA certificate
  espWifiClient.setCACert(SSL_ROOT_CA);
  traceln("Enabling TLS/SSL Communications ...");
#endif

#ifdef SSL_CLIENT_CERTIFICATE
  espWifiClient.setCertificate(SSL_CLIENT_CERTIFICATE);
  espWifiClient.setPrivateKey(SSL_CLIENT_PRIVATE_KEY);
  traceln("Allowing SSL validation with Client Certificate");
#endif

  wifi_reconnect(WIFI_CONNECTION_TIMEOUT_SECONDS);

}

void wifi_reconnect(uint retries) {
  lastWifiReconnectAttempt = millis();

  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  WiFi.disconnect(true);
  delay(500);

  info("Connecting to WiFi SSID: ");
  infoln(wifiSSID);
  WiFi.begin(wifiSSID, wifiPasswd);

  uint8_t r = 0;
  while (WiFi.status() != WL_CONNECTED && r<retries ) {
    r++;
    delay(1000);
    trace(".");
  }
  traceln("");

  if ( WiFi.isConnected() ) {
    infoln("-=- Connected to the WiFi network");
    info("Local ESP32 IP: ");
    infoln(WiFi.localIP().toString());
  } else {
    errorln("-X- Cannot connect to the WiFi newtwork");
    error("WiFi status code: ");
    errorln(WiFi.status());
    error("WiFi status text: ");
    errorln(wifi_status_text(WiFi.status()));
    WiFi.disconnect(false);
  }
}

void wifi_scan_networks() {
  infoln("Scanning WiFi networks...");
  int networkCount = WiFi.scanNetworks();

  if (networkCount <= 0) {
    warnln("No WiFi networks found.");
    return;
  }

  for (int i = 0; i < networkCount; i++) {
    info("  SSID: ");
    info(WiFi.SSID(i));
    info(" | RSSI: ");
    info(WiFi.RSSI(i));
    info(" | Channel: ");
    infoln(WiFi.channel(i));
  }
}

const char* wifi_status_text(wl_status_t status) {
  switch (status) {
    case WL_IDLE_STATUS:
      return "WL_IDLE_STATUS";
    case WL_NO_SSID_AVAIL:
      return "WL_NO_SSID_AVAIL: no se encuentra el SSID";
    case WL_SCAN_COMPLETED:
      return "WL_SCAN_COMPLETED";
    case WL_CONNECTED:
      return "WL_CONNECTED";
    case WL_CONNECT_FAILED:
      return "WL_CONNECT_FAILED: posible contrasena incorrecta o autenticacion incompatible";
    case WL_CONNECTION_LOST:
      return "WL_CONNECTION_LOST";
    case WL_DISCONNECTED:
      return "WL_DISCONNECTED";
    default:
      return "UNKNOWN";
  }
}

