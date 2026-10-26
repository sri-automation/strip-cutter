/*
  Strip cutter v5 - Wi-Fi module sketch (runs on the ESP8266 of the Uno+WiFi board)

  What it does
    - Joins the strongest of up to 8 saved Wi-Fi networks. If the network drops, it looks again
      and joins whichever saved network is best at that moment. While the machine is idle and the
      signal is weak it checks every 5 minutes for a clearly stronger access point.
    - No saved network in reach for 30 s (or none saved yet): opens the hotspot "StripCutter-Setup"
      (password = machine password, default "stripcutter"). Join it with a phone and the control page
      opens by itself; add your networks there.
    - Serves the control app at http://stripcutter.local (or the address shown on the machine's
      screen). The app talks to this module over a WebSocket on port 81.
    - Optional cloud link (MQTT over TLS, e.g. a free HiveMQ Cloud cluster), so the app works from
      anywhere in the world. Commands from the cloud must be signed with the machine password.
    - Passes lines between the app and the ATmega: one line every 100 ms so the ATmega never misses
      one, "stop" lines at once. Tells the ATmega its Wi-Fi state every 5 s for the screen.
    - Never waits long for the network: a phone that goes out of range is dropped instead of holding
      everything up, and the cloud is (re)connected only while the machine is idle (while it cuts, at
      most one try a minute). The machine itself never needs Wi-Fi to run or to stop.
    - Firmware update over Wi-Fi: Arduino IDE network port (machine password), only while the
      machine is idle.
    - Wi-Fi details for the machine's screen (Wi-Fi & remote -> Wi-Fi details): the state, why the
      last join failed (password refused, not in range, no answer, no address ...), every saved
      network with its signal, and the networks in range. The module looks at every access point
      it hears and always keeps the saved ones, even where more than 24 networks are around.

  Arduino IDE settings (Tools menu)
    Board: "Generic ESP8266 Module"   Flash size: "4MB (FS:none OTA:~1019KB)"   CPU: 160 MHz
    Upload: DIP switches 5, 6, 7 ON (others OFF), press the board's reset if the upload does not start.
    Then: 5, 6, 7 OFF and 1, 2 ON for normal use (ESP8266 <-> ATmega).

  Libraries: "WebSockets" by Markus Sattler (2.7.x), "PubSubClient" by Nick O'Leary (2.8).
  The rest comes with the ESP8266 board package (3.1.x).

  Never print debug text on Serial: Serial is the line to the ATmega.
*/

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>
#include <DNSServer.h>
#include <ArduinoOTA.h>
#include <WebSocketsServer.h>
#include <PubSubClient.h>
#include <WiFiClientSecureBearSSL.h>
#include <EEPROM.h>
#include <time.h>
#include <new>
#include "core.h"
#include "certs.h"
#include "app_gz.h"

EspCfg cfg;
NetState net;

// WebSocket server that can tell how much a client's send buffer can take, so a phone that went
// quiet never makes us wait (the library would block for seconds on a full buffer)
class SafeWS : public WebSocketsServer {
 public:
  explicit SafeWS(uint16_t port) : WebSocketsServer(port) {}
  int room(uint8_t n) {
    if (n >= WEBSOCKETS_SERVER_CLIENT_MAX) return 0;
    WSclient_t *c = &_clients[n];
    if (!clientIsConnected(c) || !c->tcp) return 0;
    return c->tcp->availableForWrite();
  }
  void drop(uint8_t n) {                 // hang up at once: no close frame, no waiting for unsent data
    if (n < WEBSOCKETS_SERVER_CLIENT_MAX && _clients[n].tcp) _clients[n].tcp->abort();
  }
};

ESP8266WebServer http(80);
SafeWS ws(81);
DNSServer dns;
BearSSL::WiFiClientSecure *tls = nullptr;     // made only when the cloud is switched on
PubSubClient *mqtt = nullptr;
BearSSL::X509List *roots = nullptr;

const IPAddress AP_IP(192, 168, 4, 1);
char topicIn[80], topicOut[80], topicState[80], topicOnline[80];

bool mqttUp() { return mqtt && mqtt->connected(); }

// ---------------- glue for core.h ----------------
uint32_t hwMillis() { return millis(); }
uint32_t hwRandom() { return RANDOM_REG32; }
void hwToAvr(const char *line) { Serial.print(line); Serial.print('\n'); }

uint8_t kickMask = 0, dropMask = 0;      // kick = polite close (after a reply), drop = hang up
uint8_t slowCount[MAX_WS];

static char cloudOut[900];
static size_t cloudOutLen = 0;
void flushCloud() {
  if (cloudOutLen && mqttUp()) mqtt->publish(topicOut, (const uint8_t *)cloudOut, cloudOutLen, false);
  cloudOutLen = 0;
}

static bool roomFor(uint8_t id, size_t n) {      // waits at most 150 ms for the client's buffer
  uint32_t t0 = millis();
  while (ws.room(id) < (int)n + 16) {
    if (millis() - t0 > 150) return false;
    delay(2);                                    // lets the network stack send and take acks
  }
  return true;
}

void hwToClient(uint8_t id, const char *text) {
  size_t n = strlen(text);
  if (id < MAX_WS) {
    if (!roomFor(id, n)) { if (++slowCount[id] >= 3) dropMask |= 1 << id; return; }   // not taking data: drop it (it gets a fresh snapshot on reconnect)
    slowCount[id] = 0;
    ws.sendTXT(id, text);
    return;
  }
  if (id != CLOUD_ID) return;
  if (cloudOutLen + n + 1 > sizeof(cloudOut)) flushCloud();
  if (n + 1 > sizeof(cloudOut)) { if (mqttUp()) mqtt->publish(topicOut, (const uint8_t *)text, n, false); return; }
  if (cloudOutLen) cloudOut[cloudOutLen++] = '\n';
  memcpy(cloudOut + cloudOutLen, text, n); cloudOutLen += n;
}
void hwCloudState(const char *text) { if (mqttUp()) mqtt->publish(topicState, (const uint8_t *)text, strlen(text), true); }
void hwSaveCfg() { EEPROM.put(0, cfg); EEPROM.commit(); }

// actions asked for by core.h (done in loop(), never inside a callback)
bool wantScan = false, wantJoin = false, wantAp = false, wantCloud = false;
uint8_t scanClient = 255;
uint32_t restartAt = 0;
void hwAction(uint8_t what, uint8_t id) {
  switch (what) {
    case A_KICK: if (id < MAX_WS) kickMask |= 1 << id; break;
    case A_SCAN: wantScan = true; scanClient = id; break;
    case A_JOIN: wantJoin = true; break;
    case A_AP: wantAp = true; break;
    case A_CLOUD: wantCloud = true; break;
    case A_RESTART: case A_NAME: restartAt = millis() + 800; break;
  }
}

// ---------------- Wi-Fi: best saved network, setup hotspot ----------------
enum { W_DOWN, W_JOINING, W_UP };
// what the radio says while joining: why it dropped, and whether it got as far as associating
WiFiEventHandler evDisc, evConn;
volatile uint16_t discReason = 0;
volatile bool assoc = false;
bool joinEnc = false;                    // the network being joined is locked (needs a password)
uint8_t wst = W_DOWN;
int8_t wNet = -1;
uint32_t wNext = 0, wJoinStart = 0, wDownSince = 0, roamNext = 0;
bool scanning = false;
uint32_t scanStartedAt = 0;
uint8_t scanWhy = 0, scanStuck = 0;      // scanWhy: 1 join, 2 roam, 4 an app asked
bool apOn = false, apManual = false;
uint32_t apOffAt = 0;

void netShow() {                         // what the ATmega's screen and the apps see
  wd.phase = wst == W_UP ? P_UP : wst == W_JOINING ? P_JOIN : scanning ? P_SCAN : P_DOWN;
  if (wst == W_UP) wd.ch = WiFi.channel();
  bool showAp = apOn && (apManual || wst != W_UP);
  net.apOn = apOn;
  net.apClients = apOn ? WiFi.softAPgetStationNum() : 0;
  if (wst == W_UP) net.rssi = WiFi.RSSI();
  if (showAp) {
    net.st = 3; strcpy(net.ip, "192.168.4.1"); strcpy(net.ssid, AP_NAME);
  } else if (wst == W_UP) {
    net.st = 2;
    strncpy(net.ip, WiFi.localIP().toString().c_str(), 15); net.ip[15] = 0;
    strncpy(net.ssid, WiFi.SSID().c_str(), 32); net.ssid[32] = 0;
  } else { net.st = 1; net.ip[0] = 0; net.ssid[0] = 0; net.rssi = 0; }
  net.heap = ESP.getFreeHeap();
}

// the hotspot is switched only between scans (changing the Wi-Fi mode during a scan can lose it)
void apStart(uint32_t minutes, bool manual) {
  if (!apOn) {
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAPConfig(AP_IP, AP_IP, IPAddress(255, 255, 255, 0));
    WiFi.softAP(AP_NAME, cfg.key);
    dns.setErrorReplyCode(DNSReplyCode::NoError);
    dns.start(53, "*", AP_IP);
    apOn = true;
  }
  apManual = manual || apManual;
  apOffAt = minutes ? millis() + minutes * 60000UL : 0;
  netShow();
}

void apStop() {
  if (!apOn) return;
  dns.stop();
  WiFi.softAPdisconnect(true);
  WiFi.mode(WIFI_STA);
  apOn = false; apManual = false; apOffAt = 0;
  netShow();
}

void startScan(uint8_t why) {
  scanWhy |= why;
  if (scanning) return;
  WiFi.scanDelete();
  if (WiFi.scanNetworks(true, false) == WIFI_SCAN_FAILED) { scanWhy = 0; wNext = millis() + 5000; return; }
  scanning = true; scanStartedAt = millis();
}

void beginJoin(int k, const ScanItem &it) {
  discReason = 0; assoc = false; joinEnc = it.enc;
  coreDiagJoin(k);
  WiFi.begin(cfg.nets[k].ssid, cfg.nets[k].pass, it.ch, it.bssid, true);
  wst = W_JOINING; wNet = k; wJoinStart = millis();
}

void joinBest(const ScanItem *items, int n) {
  int k, i = corePickNet(items, n, &k);
  if (i < 0) { wNext = millis() + (apOn && net.apClients ? 60000 : 15000); return; }
  beginJoin(k, items[i]);
}

// how a join ended, from the Wi-Fi status and the last reason the radio gave
uint8_t joinResult(wl_status_t s, bool timedOut) {
  if (wNet >= 0 && !cfg.nets[wNet].pass[0] && joinEnc) return R_NEEDPASS;
  if (s == WL_WRONG_PASSWORD) return R_PASS;
  switch (discReason) {
    case WIFI_DISCONNECT_REASON_NO_AP_FOUND: return R_NOTSEEN;
    case WIFI_DISCONNECT_REASON_AUTH_EXPIRE: case WIFI_DISCONNECT_REASON_MIC_FAILURE:
    case WIFI_DISCONNECT_REASON_4WAY_HANDSHAKE_TIMEOUT: case WIFI_DISCONNECT_REASON_HANDSHAKE_TIMEOUT:
    case WIFI_DISCONNECT_REASON_802_1X_AUTH_FAILED: case WIFI_DISCONNECT_REASON_AUTH_FAIL: return R_PASS;
    case WIFI_DISCONNECT_REASON_BEACON_TIMEOUT: return R_NOANSWER;
    case WIFI_DISCONNECT_REASON_AUTH_LEAVE: case WIFI_DISCONNECT_REASON_ASSOC_EXPIRE: case WIFI_DISCONNECT_REASON_ASSOC_TOOMANY:
    case WIFI_DISCONNECT_REASON_NOT_AUTHED: case WIFI_DISCONNECT_REASON_NOT_ASSOCED: case WIFI_DISCONNECT_REASON_ASSOC_NOT_AUTHED:
    case WIFI_DISCONNECT_REASON_IE_INVALID: case WIFI_DISCONNECT_REASON_GROUP_CIPHER_INVALID: case WIFI_DISCONNECT_REASON_PAIRWISE_CIPHER_INVALID:
    case WIFI_DISCONNECT_REASON_AKMP_INVALID: case WIFI_DISCONNECT_REASON_UNSUPP_RSN_IE_VERSION: case WIFI_DISCONNECT_REASON_INVALID_RSN_IE_CAP:
    case WIFI_DISCONNECT_REASON_CIPHER_SUITE_REJECTED: case WIFI_DISCONNECT_REASON_ASSOC_FAIL: return R_REFUSED;
    default: break;
  }
  if (s == WL_NO_SSID_AVAIL) return R_NOTSEEN;
  if (timedOut) return assoc ? R_NOIP : (discReason ? R_FAIL : R_NOANSWER);
  return R_FAIL;
}

void onUp() {
  wst = W_UP;
  coreNetOk(wNet);
  coreDiagJoin(wNet); coreDiagResult(wNet, R_OK, 0);
  roamNext = millis() + 300000;
  if (apOn && !apManual) apOffAt = millis() + 180000;   // keep the hotspot 3 more minutes so the phone sees the new address
  static bool timeSet = false;
  if (!timeSet) { configTime(0, 0, "pool.ntp.org", "time.google.com", "time.cloudflare.com"); timeSet = true; }
  netShow();
}

void onDown() {
  wst = W_DOWN; wDownSince = millis(); wNext = millis() + 300;
  if (mqttUp()) mqtt->disconnect();
  coreCloudUp(false);
  netShow();
}

void scanFinished(int n) {
  // keep at most 24 access points: the saved networks first, then the strongest others. (Where many
  // networks are around, the radio's list is not in signal order, so a saved one could be lost.)
  int total = n > 0 ? n : 0;
  if (n > 100) n = 100;
  uint8_t ord[100], sv[100]; int8_t rs[100]; int m = 0;
  for (int i = 0; i < n; i++) { rs[i] = WiFi.RSSI(i); sv[i] = findNet(WiFi.SSID(i).c_str()) >= 0; ord[m++] = i; }
  for (int a = 1; a < m; a++)
    for (int b = a; b > 0; b--) {
      uint8_t x = ord[b], y = ord[b - 1];
      if (!(sv[x] > sv[y] || (sv[x] == sv[y] && rs[x] > rs[y]))) break;
      ord[b] = y; ord[b - 1] = x;
    }
  int keep = m < 24 ? m : 24, k = 0;
  ScanItem *items = new (std::nothrow) ScanItem[keep > 0 ? keep : 1];
  if (items) {
    for (int j = 0; j < keep; j++) {
      int i = ord[j];
      String s = WiFi.SSID(i);
      strncpy(items[k].ssid, s.c_str(), 32); items[k].ssid[32] = 0;
      items[k].rssi = rs[i]; items[k].enc = WiFi.encryptionType(i) != ENC_TYPE_NONE; items[k].ch = WiFi.channel(i);
      memcpy(items[k].bssid, WiFi.BSSID(i), 6);
      k++;
    }
  }
  WiFi.scanDelete();
  if (items) coreDiagScan(items, k, total);
  scanning = false; scanStuck = 0;
  uint8_t why = scanWhy; scanWhy = 0;
  if (!items) { wNext = millis() + 5000; return; }       // out of memory: try again later
  if (why & 4) { coreScanDone(scanClient, items, k); scanClient = 255; }
  if ((why & 1) && wst == W_DOWN) joinBest(items, k);
  if ((why & 2) && wst == W_UP) {
    int best, idx = corePickNet(items, k, &best);
    // a clearly stronger access point (same network name or another saved one)
    if (idx >= 0 && memcmp(items[idx].bssid, WiFi.BSSID(), 6) != 0 && coreShouldRoam(WiFi.RSSI(), items[idx].rssi)) {
      WiFi.disconnect(); onDown();
      beginJoin(best, items[idx]);
    }
  }
  delete[] items;
}

void wifiTick() {
  uint32_t now = millis();
  bool up = WiFi.status() == WL_CONNECTED;
  if (scanning) {
    int n = WiFi.scanComplete();
    if (n >= 0 || n == WIFI_SCAN_FAILED) scanFinished(n);
    else if (now - scanStartedAt > 30000) {              // the scan never reported back
      WiFi.scanDelete(); scanning = false; scanWhy = 0; wNext = now + 2000;
      if (++scanStuck >= 2 && coreMachineIdle()) restartAt = now + 500;   // Wi-Fi stuck: restart this module (the machine is not affected)
    }
  }
  switch (wst) {
    case W_DOWN:
      if (!apOn && !scanning && (cfg.nNets == 0 || now - wDownSince > 30000)) apStart(0, false);
      if (!scanning && cfg.nNets && (int32_t)(now - wNext) >= 0) startScan(1);
      break;
    case W_JOINING: {
      wl_status_t s = WiFi.status();
      bool timedOut = now - wJoinStart > 15000;
      if (up) onUp();
      else if (timedOut || s == WL_CONNECT_FAILED || s == WL_WRONG_PASSWORD) {
        coreDiagResult(wNet, joinResult(s, timedOut), discReason);
        coreNetFailed(wNet); WiFi.disconnect(); wst = W_DOWN; wNext = now + 500;
      }
      break;
    }
    case W_UP:
      if (!up) { coreDiagResult(wNet, R_LOST, discReason); onDown(); }
      else if ((int32_t)(now - roamNext) >= 0) {
        roamNext = now + 300000;
        if (WiFi.RSSI() < -70 && coreMachineIdle() && !scanning) startScan(2);
      }
      break;
  }
  if (apOn && apOffAt && (int32_t)(now - apOffAt) >= 0 && !scanning) {
    apManual = false; apOffAt = 0;
    if (wst == W_UP) apStop();                   // not connected: the hotspot stays
  }
  if (wantAp && !scanning) { wantAp = false; apStart(10, true); }
  if (wantScan && wst != W_JOINING) { wantScan = false; startScan(4); }     // a scan would break a join in progress
  if (wantJoin && wst != W_JOINING) { wantJoin = false; if (wst == W_DOWN) startScan(1); }
}

// ---------------- cloud (MQTT over TLS) ----------------
uint32_t cloudNext = 0, cloudBackoff = 5000, lastBusyTry = 0;
bool mflnChecked = false, mflnOk = false;
static char pendingIn[1000];
static int pendingLen = -1;

void setCloud(uint8_t st, const char *err) {
  net.cloud = st;
  strncpy(net.cloudErr, err, sizeof(net.cloudErr) - 1); net.cloudErr[sizeof(net.cloudErr) - 1] = 0;
}

void cloudRetryLater(const char *why) {
  setCloud(1, why);
  cloudNext = millis() + cloudBackoff;
  cloudBackoff = cloudBackoff < 60000 ? cloudBackoff * 2 : 120000;
}

void onMqtt(char *topic, byte *payload, unsigned int len) {
  // keep a copy and handle it after loop() returns: the library's buffer is reused when we publish
  if (strcmp(topic, topicIn) || len >= sizeof(pendingIn) || pendingLen >= 0) return;
  memcpy(pendingIn, payload, len); pendingIn[len] = 0; pendingLen = (int)len;
}

void makeTopics() {
  char id[40]; snprintf(id, sizeof(id), "%s-%s", cfg.name, net.chip);
  snprintf(topicIn, sizeof(topicIn), "stripcutter/%s/in", id);
  snprintf(topicOut, sizeof(topicOut), "stripcutter/%s/out", id);
  snprintf(topicState, sizeof(topicState), "stripcutter/%s/state", id);
  snprintf(topicOnline, sizeof(topicOnline), "stripcutter/%s/online", id);
}

void cloudDisconnect() {
  if (mqttUp()) { mqtt->publish(topicOnline, "0", true); mqtt->disconnect(); }   // a clean goodbye sends no last will, so say it
  coreCloudUp(false);
}

void cloudTick() {
  uint32_t now = millis();
  if (wantCloud) { wantCloud = false; cloudDisconnect(); mflnChecked = false; cloudNext = now; cloudBackoff = 5000; }
  if (!cfg.cloudOn || !cfg.cloudHost[0]) { if (mqttUp()) cloudDisconnect(); setCloud(0, ""); return; }
  if (wst != W_UP) { coreCloudUp(false); setCloud(1, "waiting for Wi-Fi"); return; }
  if (mqttUp()) {
    mqtt->loop();
    if (pendingLen >= 0) { int n = pendingLen; coreCloudText(pendingIn, n); pendingLen = -1; }
    flushCloud();
    return;
  }
  if (net.cloud == 2) { coreCloudUp(false); setCloud(1, "connection lost, trying again"); cloudNext = now + 2000; }
  if ((int32_t)(now - cloudNext) < 0) return;
  // connecting blocks for a second or two: do it while the machine is idle and nothing waits
  // for the ATmega; while it cuts, at most one try a minute
  bool idle = coreMachineIdle() && coreQueueEmpty();
  if (!idle) { if (now - lastBusyTry < 60000) return; lastBusyTry = now; }
  if (cfg.cloudVerify && time(nullptr) < 1700000000) {
    setCloud(1, "waiting for the clock (NTP); turn off the certificate check if this stays");
    cloudNext = now + 2000; return;
  }
  IPAddress ip;                                   // name lookup with a short limit; the result is cached for the connect
  if (!WiFi.hostByName(cfg.cloudHost, ip, 2000)) { cloudRetryLater("server name not found"); return; }
  if (!tls) {
    tls = new (std::nothrow) BearSSL::WiFiClientSecure();
    if (tls) mqtt = new (std::nothrow) PubSubClient(*tls);
    if (!tls || !mqtt) { delete tls; tls = nullptr; mqtt = nullptr; cloudRetryLater("not enough memory"); return; }
    mqtt->setCallback(onMqtt);
    mqtt->setBufferSize(1400);
    mqtt->setKeepAlive(60);
  }
  if (cfg.cloudVerify) {
    if (!roots) {
      char *pem = (char *)malloc(sizeof(ROOT_X1) > sizeof(ROOT_X2) ? sizeof(ROOT_X1) : sizeof(ROOT_X2));
      BearSSL::X509List *r = pem ? new (std::nothrow) BearSSL::X509List() : nullptr;
      if (r) { strcpy_P(pem, ROOT_X1); r->append(pem); strcpy_P(pem, ROOT_X2); r->append(pem); roots = r; }
      free(pem);
      if (!roots) { cloudRetryLater("not enough memory"); return; }
    }
    tls->setTrustAnchors(roots);
  } else tls->setInsecure();
  if (!mflnChecked && idle) { mflnOk = BearSSL::WiFiClientSecure::probeMaxFragmentLength(cfg.cloudHost, cfg.cloudPort, 1024); mflnChecked = true; }
  int rx = mflnOk ? 1024 : 8192;
  if (ESP.getFreeHeap() < (uint32_t)rx + 13000 || ESP.getMaxFreeBlockSize() < (uint32_t)rx + 1000) { cloudRetryLater("not enough memory for the secure link"); return; }
  tls->setBufferSizes(rx, mflnOk ? 1024 : 512);
  tls->setTimeout(3000);
  makeTopics();
  mqtt->setServer(cfg.cloudHost, cfg.cloudPort);   // by name: the server needs it to pick the right certificate
  mqtt->setSocketTimeout(3);
  char cid[48]; snprintf(cid, sizeof(cid), "sc-%s-%s", cfg.name, net.chip);
  bool ok = mqtt->connect(cid, cfg.cloudUser[0] ? cfg.cloudUser : nullptr, cfg.cloudPass[0] ? cfg.cloudPass : nullptr,
                          topicOnline, 1, true, "0", true);
  if (ok) {
    mqtt->subscribe(topicIn, 0);
    mqtt->publish(topicOnline, "1", true);
    setCloud(2, "");
    coreCloudUp(true);
    cloudBackoff = 5000;
  } else {
    char e[64] = "";
    int st = mqtt->state();
    if (st == 4 || st == 5) strcpy(e, "user name or password refused");
    else if (tls->getLastSSLError(e, sizeof(e)) == 0) snprintf(e, sizeof(e), "no answer from the server (%d)", st);
    mflnChecked = false;                          // check again next time: this may have been a network hiccup
    cloudRetryLater(e);
  }
}

// ---------------- web page and WebSocket ----------------
bool fromHotspot() { return http.client().localIP() == AP_IP; }

bool ourHost() {
  String h = http.hostHeader();
  int c = h.indexOf(':'); if (c >= 0) h = h.substring(0, c);
  if (h == "192.168.4.1" || h == WiFi.localIP().toString()) return true;
  String local = String(cfg.name) + ".local";
  return h.equalsIgnoreCase(local) || h.equalsIgnoreCase(cfg.name);
}

void toPortal() { http.sendHeader("Location", "http://192.168.4.1/", true); http.send(302, "text/plain", ""); }

void sendApp() {
  if (apOn && fromHotspot() && !ourHost()) { toPortal(); return; }   // phones on the hotspot: open the page
  if (http.header("If-None-Match") == "\"" APP_ETAG "\"") { http.send(304); return; }   // the phone already has this page
  http.sendHeader("ETag", "\"" APP_ETAG "\"");
  http.sendHeader("Content-Encoding", "gzip");
  http.sendHeader("Cache-Control", "no-cache");
  http.send_P(200, "text/html", (const char *)APP_GZ, APP_GZ_LEN);
}

void notFound() {
  if (apOn && fromHotspot() && !ourHost()) { toPortal(); return; }
  http.send(404, "text/plain", "not here - open http://" + String(cfg.name) + ".local/");
}

// WebSocket logins only from pages of this machine (or the app file on a PC)
bool okOrigin(String name, String value) {
  if (!name.equalsIgnoreCase("Origin")) return true;
  if (value.length() == 0 || value == "null" || value.startsWith("file:")) return true;
  int s = value.indexOf("://");
  String h = s >= 0 ? value.substring(s + 3) : value;
  int e = h.indexOf('/'); if (e >= 0) h = h.substring(0, e);
  e = h.indexOf(':'); if (e >= 0) h = h.substring(0, e);
  h.toLowerCase();
  String nm = String(cfg.name);
  return h == "192.168.4.1" || h == WiFi.localIP().toString() || h == "localhost" || h == "127.0.0.1" || h == nm || h.startsWith(nm + ".");
}

void onWs(uint8_t num, WStype_t type, uint8_t *payload, size_t len) {
  switch (type) {
    case WStype_CONNECTED: if (num < MAX_WS) slowCount[num] = 0; coreClientConnected(num); break;
    case WStype_DISCONNECTED: coreClientGone(num); break;
    case WStype_TEXT: coreClientText(num, (const char *)payload, len); break;
    default: break;
  }
}

// ---------------- setup and loop ----------------
void setup() {
  Serial.setRxBufferSize(1024);
  Serial.begin(115200);
  Serial.setDebugOutput(false);

  EEPROM.begin(sizeof(EspCfg) + 8);
  EEPROM.get(0, cfg);
  if (!cfgValid(cfg)) { cfgDefaults(cfg); cfgStore(); }
  memset(&net, 0, sizeof(net));
  snprintf(net.chip, sizeof(net.chip), "%06x", ESP.getChipId() & 0xFFFFFF);

  WiFi.persistent(false);
  WiFi.setAutoReconnect(false);
  evDisc = WiFi.onStationModeDisconnected([](const WiFiEventStationModeDisconnected &e) { discReason = e.reason; });
  evConn = WiFi.onStationModeConnected([](const WiFiEventStationModeConnected &) { assoc = true; });
  WiFi.mode(WIFI_STA);
  WiFi.hostname(cfg.name);
  WiFi.setSleepMode(WIFI_NONE_SLEEP);
  coreInit();                            // after the radio is on: its random numbers make the nonces
  wDownSince = millis();
  netShow();
  if (cfg.nNets) startScan(1); else apStart(0, false);

  http.collectHeaders("If-None-Match");
  http.on("/", sendApp);
  http.on("/index.html", sendApp);
  http.onNotFound(notFound);
  http.begin();

  ws.onEvent(onWs);
  ws.onValidateHttpHeader(okOrigin, nullptr, 0);
  ws.enableHeartbeat(5000, 3000, 2);     // drops phones that went away within about 15 s
  ws.begin();

  ArduinoOTA.setHostname(cfg.name);
  ArduinoOTA.setPassword(cfg.key);
  ArduinoOTA.begin(true);                // also starts mDNS: http://<name>.local
  MDNS.addService("http", "tcp", 80);
}

void loop() {
  for (int i = 0; i < 256 && Serial.available(); i++) coreAvrByte(Serial.read());
  wifiTick();
  if (apOn) dns.processNextRequest();
  http.handleClient();
  ws.loop();
  cloudTick();
  if (coreMachineIdle()) ArduinoOTA.handle();     // no firmware upload while the machine cuts (it would block the stop lines)
  MDNS.update();

  static uint32_t lastShow = 0;
  if (millis() - lastShow > 1000) { lastShow = millis(); netShow(); }
  coreTick();
  flushCloud();

  if (dropMask) { for (uint8_t i = 0; i < MAX_WS; i++) if (dropMask & (1 << i)) ws.drop(i); dropMask = 0; }
  if (kickMask) { for (uint8_t i = 0; i < MAX_WS; i++) if (kickMask & (1 << i)) ws.disconnect(i); kickMask = 0; }
  if (restartAt && (int32_t)(millis() - restartAt) >= 0) { cloudDisconnect(); delay(100); ESP.restart(); }
}
