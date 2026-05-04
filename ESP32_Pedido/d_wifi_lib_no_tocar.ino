#define WIFI_CONNECTION_TIMEOUT_SECONDS 15
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
  trace("MAC Address: ");
  traceln(WiFi.macAddress());

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
    WiFi.disconnect(false);
  }
}


