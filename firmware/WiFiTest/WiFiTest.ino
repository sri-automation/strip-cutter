/*
  Wi-Fi test for the strip cutter's ESP8266 - nothing else runs: no app, no hotspot, no machine.
  It prints what the Wi-Fi chip does while it joins your network, so we can see why it fails.

  1. Put your network name and password in the two lines below. Best first test: a phone hotspot
     set to WPA2-Personal and 2.4 GHz, with the phone 1 m from the machine.
  2. DIP switches 5, 6, 7 ON (the others OFF). Upload with the same Tools settings as StripCutterWiFi
     (Generic ESP8266 Module, 4MB (FS:none OTA:~1019KB), 160 MHz).
  3. DIP switch 7 OFF (5 and 6 stay ON). Tools -> Serial Monitor, 115200 baud. Press the board's reset.
  4. Wait about 1.5 minutes until it prints RESULT, then copy everything in the Serial Monitor and send it.
  Afterwards load StripCutterWiFi again (DIP 5, 6, 7 ON), then DIP 1 + 2 ON for normal use.
*/
#include <ESP8266WiFi.h>
ADC_MODE(ADC_VCC);                       // lets the chip measure its own supply voltage

const char *WIFI_NAME = "YOUR_WIFI_NAME";
const char *WIFI_PASS = "YOUR_PASSWORD";

WiFiEventHandler hDisc, hConn, hIp;
volatile int lastReason = -1, discCount = 0;
volatile bool gotConn = false, gotIp = false;

const char *encName(uint8_t e) {
  switch (e) {
    case ENC_TYPE_NONE: return "open";
    case ENC_TYPE_WEP:  return "WEP";
    case ENC_TYPE_TKIP: return "WPA";
    case ENC_TYPE_CCMP: return "WPA2";
    case ENC_TYPE_AUTO: return "WPA/WPA2";
    default:            return "OTHER (WPA3 or enterprise - cannot be used)";
  }
}
const char *stName(int s) {
  switch (s) {
    case WL_IDLE_STATUS: return "idle"; case WL_NO_SSID_AVAIL: return "network not found";
    case WL_CONNECTED: return "connected"; case WL_CONNECT_FAILED: return "connect failed";
    case WL_CONNECTION_LOST: return "connection lost"; case WL_WRONG_PASSWORD: return "WRONG PASSWORD";
    case WL_DISCONNECTED: return "disconnected / trying"; default: return "?";
  }
}
const char *reasonName(int r) {
  switch (r) {
    case -1: return "none - the router never answered";
    case 2: return "auth expired (no reply or wrong password)";
    case 15: return "4-way handshake timeout (wrong password?)";
    case 201: return "network not found";
    case 202: return "authentication failed (password / WPA3)";
    case 203: return "association refused by the router";
    case 204: return "handshake timeout (wrong password?)";
    case 200: return "beacon timeout (signal lost)";
    default: return "see the list in ESP8266WiFiType.h";
  }
}

bool netHeard = false;
void scanList() {
  Serial.println(F("\n--- networks the chip hears ---"));
  int n = WiFi.scanNetworks(false, true);
  for (int i = 0; i < n; i++) {
    bool mine = WiFi.SSID(i) == WIFI_NAME;
    if (mine) netHeard = true;
    Serial.printf("%2d %-32s %4d dBm  ch %2d  %-9s %s%s\n", i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i),
                  encName(WiFi.encryptionType(i)), WiFi.BSSIDstr(i).c_str(), mine ? "   <-- yours" : "");
  }
  Serial.printf("%d networks. Yours (\"%s\"): %s\n", n, WIFI_NAME, netHeard ? "heard" : "NOT HEARD (name typed exactly? 2.4 GHz?)");
  WiFi.scanDelete();
}

bool tryJoin(const char *label, float txDbm, WiFiPhyMode_t phy) {
  Serial.printf("\n--- try: %s ---\n", label);
  WiFi.disconnect(); delay(300);
  WiFi.setPhyMode(phy);
  WiFi.setOutputPower(txDbm);
  lastReason = -1; discCount = 0; gotConn = false; gotIp = false;
  uint32_t t0 = millis(); int lastSt = -1; uint16_t minVcc = 9999;
  WiFi.begin(WIFI_NAME, WIFI_PASS);
  while (millis() - t0 < 25000) {
    uint16_t v = ESP.getVcc(); if (v < minVcc) minVcc = v;
    int st = WiFi.status();
    if (st != lastSt) { Serial.printf("%6lu ms  status %d = %s\n", millis() - t0, st, stName(st)); lastSt = st; }
    if (gotIp) {
      Serial.printf("CONNECTED after %lu ms: IP %s, signal %d dBm, channel %d\n", millis() - t0,
                    WiFi.localIP().toString().c_str(), WiFi.RSSI(), WiFi.channel());
      return true;
    }
    delay(50);
  }
  Serial.printf("NOT connected in 25 s. Associated with the router: %s. Radio drop events: %d, last reason %d = %s\n",
                gotConn ? "yes (but got no IP address)" : "no", discCount, lastReason, reasonName(lastReason));
  Serial.printf("Lowest supply voltage during the try: %.2f V\n", minVcc / 1000.0);
  return false;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println(F("\n\n=== Strip cutter Wi-Fi test ==="));
  Serial.printf("reset reason: %s\n", ESP.getResetReason().c_str());
  Serial.printf("chip id %06x, SDK %s, core %s\n", ESP.getChipId(), ESP.getSdkVersion(), ESP.getCoreVersion().c_str());
  uint32_t real = ESP.getFlashChipRealSize(), set = ESP.getFlashChipSize();
  Serial.printf("flash: chip has %u KB, Arduino IDE set to %u KB%s\n", real / 1024, set / 1024, real != set ? "   <-- DIFFERENT" : "");
  Serial.printf("supply voltage at the chip: %.2f V (should be 3.0 to 3.6)\n", ESP.getVcc() / 1000.0);
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(200);
  hDisc = WiFi.onStationModeDisconnected([](const WiFiEventStationModeDisconnected &e) { lastReason = e.reason; discCount++; });
  hConn = WiFi.onStationModeConnected([](const WiFiEventStationModeConnected &) { gotConn = true; });
  hIp = WiFi.onStationModeGotIP([](const WiFiEventStationModeGotIP &) { gotIp = true; });
  scanList();
  Serial.setDebugOutput(true);           // the Wi-Fi library's own messages ("state: 0 -> 2 ...") too
  bool ok = tryJoin("normal: full power, 802.11n", 20.5, WIFI_PHY_MODE_11N) ||
            tryJoin("low power 12 dBm (in case the supply sags when it transmits)", 12, WIFI_PHY_MODE_11N) ||
            tryJoin("802.11g only", 17, WIFI_PHY_MODE_11G);
  Serial.setDebugOutput(false);
  Serial.println(ok ? F("\nRESULT: the Wi-Fi chip CAN join this network.") : F("\nRESULT: it could NOT join in any of the 3 tries."));
  Serial.println(F("Copy everything above and send it."));
}

void loop() {}
