// core.h - Strip cutter Wi-Fi module: everything that does not touch the radio.
//
// The sketch (StripCutterWiFi.ino) owns Wi-Fi, the web server, the WebSocket server and the
// cloud link, and hands every byte to these functions. The same file is compiled on a PC for
// the tests, so it is plain C++ without Arduino String.
//
// Lines between the app and this module
//   app -> module   "$..." is for this module (see espCommand). Anything else is passed to the
//                   ATmega, which only obeys framed lines "@CMD*HH" (the app frames them).
//   module -> app   every line from the ATmega as it is, plus "$..." lines from this module:
//                   $HELLO nonce name version   $AUTH ok|bad   $W {wifi status}   $L {saved settings}
//                   $N [scan]   $OK text   $ERR text   $NONCE n   $SNAP 1 ... $SNAP 0 (state replay)
//   Local app login: $AUTH<tab>hex(HMAC-SHA256(password, "auth:" + nonce))[0..31]
//   Cloud commands are signed: first line "$SIG<tab>nonce<tab>seq<tab>mac", then the lines,
//   mac = hex(HMAC-SHA256(password, nonce + "\t" + seq + "\n" + lines))[0..31]. The nonce comes
//   from the module ($W), so an old message cannot be replayed and no clock is needed.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

#define ESP_VERSION "1.0"
#define MAX_NETS 8
#define MAX_WS 5                     // WebSocket clients (the library's limit on the ESP8266)
#define CLOUD_ID 9                   // client number used for the cloud link
#define LINE_MAX 200
#define AVR_LINE_MAX 60              // the ATmega's line buffer is 64
#define DEFAULT_NAME "stripcutter"
#define DEFAULT_KEY "stripcutter"
#define AP_NAME "StripCutter-Setup"

struct Net { char ssid[33]; char pass[65]; };
struct EspCfg {
  uint32_t magic;
  char name[25];                     // http://<name>.local
  char key[33];                      // machine password: app login, setup hotspot, firmware update
  uint8_t nNets;
  Net nets[MAX_NETS];
  uint8_t cloudOn, cloudVerify;
  char cloudHost[65];
  uint16_t cloudPort;
  char cloudUser[49];
  char cloudPass[65];
  uint32_t sum;
};
const uint32_t CFG_MAGIC = 0x57C10002;

struct NetState {                    // filled in by the sketch
  uint8_t st;                        // 1 looking, 2 connected, 3 setup hotspot
  int8_t rssi;
  char ip[16];
  char ssid[33];
  uint8_t cloud;                     // 0 off, 1 trying / problem, 2 online
  char cloudErr[64];
  uint8_t apOn, apClients;
  uint32_t heap;
  char chip[7];                      // chip id, 6 hex digits
};

struct ScanItem { char ssid[33]; int8_t rssi; uint8_t enc, ch; uint8_t bssid[6]; };

extern EspCfg cfg;
extern NetState net;

// ---- supplied by the sketch (or the PC test harness) ----
uint32_t hwMillis();
uint32_t hwRandom();
void hwToAvr(const char *line);                  // one line to the ATmega, newline added
void hwToClient(uint8_t id, const char *text);   // to one WebSocket client, or the cloud (CLOUD_ID); may hold several lines
void hwCloudState(const char *text);             // retained cloud snapshot
void hwSaveCfg();
enum { A_SCAN, A_JOIN, A_RESTART, A_CLOUD, A_AP, A_KICK, A_NAME };
void hwAction(uint8_t what, uint8_t id);

// =====================================================================================
// SHA-256 and HMAC (small, so the module and the tests use the very same code)
struct Sha256 { uint32_t h[8]; uint8_t buf[64]; uint64_t len; uint8_t n; };
static const uint32_t SHA_K[64] = {
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2 };
static inline uint32_t shaRor(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static void shaBlock(Sha256 *s, const uint8_t *p) {
  uint32_t w[64];
  for (int i = 0; i < 16; i++) w[i] = (uint32_t)p[i * 4] << 24 | (uint32_t)p[i * 4 + 1] << 16 | (uint32_t)p[i * 4 + 2] << 8 | p[i * 4 + 3];
  for (int i = 16; i < 64; i++) {
    uint32_t s0 = shaRor(w[i - 15], 7) ^ shaRor(w[i - 15], 18) ^ (w[i - 15] >> 3);
    uint32_t s1 = shaRor(w[i - 2], 17) ^ shaRor(w[i - 2], 19) ^ (w[i - 2] >> 10);
    w[i] = w[i - 16] + s0 + w[i - 7] + s1;
  }
  uint32_t a = s->h[0], b = s->h[1], c = s->h[2], d = s->h[3], e = s->h[4], f = s->h[5], g = s->h[6], h = s->h[7];
  for (int i = 0; i < 64; i++) {
    uint32_t t1 = h + (shaRor(e, 6) ^ shaRor(e, 11) ^ shaRor(e, 25)) + ((e & f) ^ (~e & g)) + SHA_K[i] + w[i];
    uint32_t t2 = (shaRor(a, 2) ^ shaRor(a, 13) ^ shaRor(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
    h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
  }
  s->h[0] += a; s->h[1] += b; s->h[2] += c; s->h[3] += d; s->h[4] += e; s->h[5] += f; s->h[6] += g; s->h[7] += h;
}
static void shaInit(Sha256 *s) {
  static const uint32_t H0[8] = { 0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19 };
  memcpy(s->h, H0, sizeof(H0)); s->len = 0; s->n = 0;
}
static void shaAdd(Sha256 *s, const void *d, size_t n) {
  const uint8_t *p = (const uint8_t *)d;
  s->len += n;
  while (n--) { s->buf[s->n++] = *p++; if (s->n == 64) { shaBlock(s, s->buf); s->n = 0; } }
}
static void shaEnd(Sha256 *s, uint8_t out[32]) {
  uint64_t bits = s->len * 8;
  uint8_t b = 0x80; shaAdd(s, &b, 1);
  b = 0; while (s->n != 56) shaAdd(s, &b, 1);
  uint8_t lb[8]; for (int i = 0; i < 8; i++) lb[i] = (uint8_t)(bits >> (56 - 8 * i));
  shaAdd(s, lb, 8);
  for (int i = 0; i < 8; i++) { out[i * 4] = s->h[i] >> 24; out[i * 4 + 1] = s->h[i] >> 16; out[i * 4 + 2] = s->h[i] >> 8; out[i * 4 + 3] = s->h[i]; }
}
// HMAC-SHA256 of a + b (two pieces, so nothing has to be copied together)
static void hmac256(const char *key, const void *a, size_t an, const void *b, size_t bn, uint8_t out[32]) {
  uint8_t k[64]; memset(k, 0, 64);
  size_t kl = strlen(key);
  Sha256 s;
  if (kl > 64) { shaInit(&s); shaAdd(&s, key, kl); shaEnd(&s, k); } else memcpy(k, key, kl);
  uint8_t pad[64], inner[32];
  for (int i = 0; i < 64; i++) pad[i] = k[i] ^ 0x36;
  shaInit(&s); shaAdd(&s, pad, 64); shaAdd(&s, a, an); if (bn) shaAdd(&s, b, bn); shaEnd(&s, inner);
  for (int i = 0; i < 64; i++) pad[i] = k[i] ^ 0x5c;
  shaInit(&s); shaAdd(&s, pad, 64); shaAdd(&s, inner, 32); shaEnd(&s, out);
}
static void hex32(const uint8_t *mac, char *out) {       // first 16 bytes as 32 hex digits
  static const char HX[] = "0123456789abcdef";
  for (int i = 0; i < 16; i++) { out[i * 2] = HX[mac[i] >> 4]; out[i * 2 + 1] = HX[mac[i] & 15]; }
  out[32] = 0;
}
static bool sameText(const char *a, const char *b) {     // compares without stopping early
  size_t la = strlen(a), lb = strlen(b);
  uint8_t d = la != lb;
  for (size_t i = 0; i < la && i < lb; i++) d |= a[i] ^ b[i];
  return d == 0;
}

// =====================================================================================
// settings
static uint32_t cfgSum(const EspCfg &c) {
  const uint8_t *p = (const uint8_t *)&c;
  uint32_t h = 2166136261u;
  for (size_t i = 0; i < offsetof(EspCfg, sum); i++) { h ^= p[i]; h *= 16777619u; }
  return h;
}
static void cfgDefaults(EspCfg &c) {
  memset(&c, 0, sizeof(c));
  c.magic = CFG_MAGIC;
  strcpy(c.name, DEFAULT_NAME);
  strcpy(c.key, DEFAULT_KEY);
  c.cloudPort = 8883;
  c.cloudVerify = 1;
}
static bool cfgValid(const EspCfg &c) { return c.magic == CFG_MAGIC && c.sum == cfgSum(c) && c.nNets <= MAX_NETS && strlen(c.key) >= 8; }
static void cfgStore() { cfg.sum = cfgSum(cfg); hwSaveCfg(); }

// =====================================================================================
// state
static bool authed[MAX_WS], present[MAX_WS];
static char helloNonce[MAX_WS][17];
static uint32_t joinedAt[MAX_WS];
static bool cloudUp = false;
static uint8_t badAuth = 0; static uint32_t badAuthAt = 0;

// what the ATmega said last (sent to every app that connects)
static const char CACHE_TAGS[] = "BCSPTMF";          // #B version, #C settings, #S state, #P count, #T knife, #M timing, #F test feeds
#define NCACHE 7
static char cacheLine[NCACHE][110];
static char lastNote[LINE_MAX];                        // last NOTE / STOPPED / LOCKED / NOT STARTED line
static uint32_t avrSeenAt = 0, avrBootAt = 0, lastProbe = 0;
static bool avrEver = false;

// lines waiting to go to the ATmega, one every 100 ms so its 64-byte buffer never overflows
#define QN 12
static char txq[QN][AVR_LINE_MAX + 4];
static uint8_t qHead = 0, qCount = 0;
static uint32_t lastTx = 0;
#define TX_GAP_MS 100

// Wi-Fi status line for the ATmega's screen
static char lastIKey[120];
static uint32_t lastI = 0, lastW = 0;

// cloud replay protection
static char nonceCur[17], noncePrev[17];
static uint32_t nonceAt = 0; static uint8_t nonceUses = 0;
#define NSEEN 128
static uint32_t seenMac[NSEEN]; static uint8_t seenPos = 0;
static uint32_t lastSnap = 0, lastNonceReply = 0; static bool snapDirty = true;

// joining: networks that just failed wait a while
static uint32_t failUntil[MAX_NETS];

// =====================================================================================
// small helpers
static uint32_t nowMs() { return hwMillis(); }

static size_t jsonEsc(char *d, size_t room, const char *s) {   // writes a JSON string body, returns length
  size_t n = 0;
  for (; *s && n + 7 < room; s++) {
    uint8_t c = (uint8_t)*s;
    if (c == '"' || c == '\\') { d[n++] = '\\'; d[n++] = c; }
    else if (c < 32) n += snprintf(d + n, room - n, "\\u%04x", c);
    else d[n++] = c;
  }
  d[n] = 0;
  return n;
}

static void frameCmd(char *out, size_t room, const char *cmd) {   // "@cmd*HH"
  uint8_t x = 0;
  for (const char *p = cmd; *p; p++) x ^= (uint8_t)*p;
  snprintf(out, room, "@%s*%02X", cmd, x);
}

static void newNonce() {
  strcpy(noncePrev, nonceCur);
  snprintf(nonceCur, sizeof(nonceCur), "%08lx%08lx", (unsigned long)hwRandom(), (unsigned long)hwRandom());
  nonceAt = nowMs(); nonceUses = 0;
  snapDirty = true;
}

static void sendTo(uint8_t id, const char *text) {
  if (id == CLOUD_ID) { if (cloudUp) hwToClient(CLOUD_ID, text); }
  else if (id < MAX_WS && authed[id]) hwToClient(id, text);
}
static void sendAll(const char *text) {
  for (uint8_t i = 0; i < MAX_WS; i++) if (authed[i]) hwToClient(i, text);
  if (cloudUp) hwToClient(CLOUD_ID, text);
}
static bool anyone() {
  for (uint8_t i = 0; i < MAX_WS; i++) if (authed[i]) return true;
  return cloudUp;
}

// =====================================================================================
// status texts
static char outBuf[1250];

static const char *wJson() {
  char ssid[72], err[100], name[52];
  jsonEsc(ssid, sizeof(ssid), net.ssid);
  jsonEsc(err, sizeof(err), net.cloudErr);
  jsonEsc(name, sizeof(name), cfg.name);
  long avrAge = avrEver ? (long)((nowMs() - avrSeenAt) / 1000) : -1;
  static char b[560];
  snprintf(b, sizeof(b),
           "$W {\"st\":%u,\"ssid\":\"%s\",\"rssi\":%d,\"ip\":\"%s\",\"cloud\":%u,\"cerr\":\"%s\",\"name\":\"%s\",\"cid\":\"%s-%s\","
           "\"ver\":\"" ESP_VERSION "\",\"up\":%lu,\"heap\":%lu,\"avr\":%ld,\"ap\":%u,\"apc\":%u,\"nonce\":\"%s\"}",
           net.st, ssid, net.rssi, net.ip, net.cloud, err, name, cfg.name, net.chip,
           (unsigned long)(nowMs() / 1000), (unsigned long)net.heap, avrAge, net.apOn, net.apClients, nonceCur);
  return b;
}

static const char *lJson() {
  size_t n = snprintf(outBuf, sizeof(outBuf), "$L {\"name\":\"");
  n += jsonEsc(outBuf + n, sizeof(outBuf) - n, cfg.name);
  n += snprintf(outBuf + n, sizeof(outBuf) - n, "\",\"cid\":\"%s-%s\",\"keyDefault\":%d,\"nets\":[", cfg.name, net.chip, strcmp(cfg.key, DEFAULT_KEY) == 0);
  for (uint8_t i = 0; i < cfg.nNets; i++) {
    n += snprintf(outBuf + n, sizeof(outBuf) - n, "%s\"", i ? "," : "");
    n += jsonEsc(outBuf + n, sizeof(outBuf) - n, cfg.nets[i].ssid);
    n += snprintf(outBuf + n, sizeof(outBuf) - n, "\"");
  }
  n += snprintf(outBuf + n, sizeof(outBuf) - n, "],\"max\":%d,\"cloud\":{\"on\":%u,\"verify\":%u,\"host\":\"", MAX_NETS, cfg.cloudOn, cfg.cloudVerify);
  n += jsonEsc(outBuf + n, sizeof(outBuf) - n, cfg.cloudHost);
  n += snprintf(outBuf + n, sizeof(outBuf) - n, "\",\"port\":%u,\"user\":\"", cfg.cloudPort);
  n += jsonEsc(outBuf + n, sizeof(outBuf) - n, cfg.cloudUser);
  snprintf(outBuf + n, sizeof(outBuf) - n, "\",\"hasPass\":%d}}", cfg.cloudPass[0] != 0);
  return outBuf;
}

static const char *snapText() {               // everything a new app needs to draw the machine
  size_t n = snprintf(outBuf, sizeof(outBuf), "$SNAP 1\n");
  for (uint8_t i = 0; i < NCACHE; i++)
    if (cacheLine[i][0]) n += snprintf(outBuf + n, sizeof(outBuf) - n, "%s\n", cacheLine[i]);
  if (lastNote[0]) n += snprintf(outBuf + n, sizeof(outBuf) - n, "%.150s\n", lastNote);
  snprintf(outBuf + n, sizeof(outBuf) - n, "%s\n$SNAP 0", wJson());
  return outBuf;
}

// the Wi-Fi line for the machine's screen: I<state>,<rssi>,<ip>,<ssid>,<cloud>
static void buildI(char *payload, size_t room) {
  char ss[21]; uint8_t k = 0;
  for (const char *p = net.ssid; *p && k < 20; p++) {
    char c = *p;
    if (c == ',') c = '.'; else if ((uint8_t)c < 32 || (uint8_t)c > 126) c = '?';
    ss[k++] = c;
  }
  ss[k] = 0;
  snprintf(payload, room, "I%u,%d,%s,%s,%u", net.st, net.rssi, net.ip, ss, net.cloud);
}

// =====================================================================================
// to the ATmega
static void queueAvr(const char *line) {
  if (qCount >= QN) return;
  strncpy(txq[(qHead + qCount) % QN], line, AVR_LINE_MAX);
  txq[(qHead + qCount) % QN][AVR_LINE_MAX] = 0;
  qCount++;
}
static bool isStop(const char *l) { return strcmp(l, "!") == 0 || strncmp(l, "@!*", 3) == 0; }
static bool isStopTop(const char *l) { return strncmp(l, "@X*", 3) == 0 || strncmp(l, "@x*", 3) == 0; }

static void appLineToAvr(uint8_t id, const char *line) {
  size_t n = strlen(line);
  if (n > AVR_LINE_MAX) { sendTo(id, "$ERR line too long"); return; }
  for (size_t i = 0; i < n; i++) if ((uint8_t)line[i] < 32 || (uint8_t)line[i] > 126) { sendTo(id, "$ERR not text"); return; }
  if (isStop(line)) { qCount = 0; hwToAvr(line); lastTx = nowMs(); return; }      // stop now: at once, drop the rest
  if (isStopTop(line)) { hwToAvr(line); lastTx = nowMs(); return; }                // stop at the top: at once
  if (qCount >= QN) { sendTo(id, "$ERR busy, send again"); return; }
  queueAvr(line);
}

// =====================================================================================
// commands for this module
static bool goodName(const char *s) {
  size_t n = strlen(s);
  if (n < 1 || n > 24 || s[0] == '-' || s[n - 1] == '-') return false;
  for (; *s; s++) if (!((*s >= 'a' && *s <= 'z') || (*s >= '0' && *s <= '9') || *s == '-')) return false;
  return true;
}
static char *field(char *&p) {                 // next tab-separated field
  if (!p) return (char *)"";
  char *f = p, *t = strchr(p, '\t');
  if (t) { *t = 0; p = t + 1; } else p = 0;
  return f;
}
static int findNet(const char *ssid) {
  for (uint8_t i = 0; i < cfg.nNets; i++) if (strcmp(cfg.nets[i].ssid, ssid) == 0) return i;
  return -1;
}

static void espCommand(uint8_t id, char *line) {
  char *p = strchr(line, '\t');
  if (p) *p++ = 0;
  const char *c = line + 1;
  char msg[120];
  if (!strcmp(c, "W")) sendTo(id, wJson());
  else if (!strcmp(c, "L")) sendTo(id, lJson());
  else if (!strcmp(c, "PING")) sendTo(id, "$PONG");
  else if (!strcmp(c, "SNAP")) sendTo(id, snapText());
  else if (!strcmp(c, "SCAN")) hwAction(A_SCAN, id);
  else if (!strcmp(c, "JOIN")) { sendTo(id, "$OK looking for the best saved network"); hwAction(A_JOIN, id); }
  else if (!strcmp(c, "AP")) { sendTo(id, "$OK setup hotspot " AP_NAME " opens for 10 minutes"); hwAction(A_AP, id); }
  else if (!strcmp(c, "RESTART")) { sendTo(id, "$OK the Wi-Fi module restarts now"); hwAction(A_RESTART, id); }
  else if (!strcmp(c, "ADD")) {
    char *ssid = field(p), *pass = field(p);
    size_t sl = strlen(ssid), pl = strlen(pass);
    if (sl < 1 || sl > 32) { sendTo(id, "$ERR the network name must be 1 to 32 characters"); return; }
    if (pl && (pl < 8 || pl > 64)) { sendTo(id, "$ERR a Wi-Fi password is 8 to 64 characters (empty for an open network)"); return; }
    int i = findNet(ssid);
    if (i < 0) {
      if (cfg.nNets >= MAX_NETS) { sendTo(id, "$ERR the list is full (8). Delete one first."); return; }
      i = cfg.nNets++;
    }
    strcpy(cfg.nets[i].ssid, ssid); strcpy(cfg.nets[i].pass, pass);
    failUntil[i] = 0;
    cfgStore();
    snprintf(msg, sizeof(msg), "$OK saved %s", ssid); sendTo(id, msg);
    sendAll(lJson());
    if (net.st != 2) hwAction(A_JOIN, id);
  }
  else if (!strcmp(c, "DEL")) {
    char *ssid = field(p);
    int i = findNet(ssid);
    if (i < 0) { sendTo(id, "$ERR not in the list"); return; }
    for (uint8_t k = i; k + 1 < cfg.nNets; k++) { cfg.nets[k] = cfg.nets[k + 1]; failUntil[k] = failUntil[k + 1]; }
    cfg.nNets--;
    memset(&cfg.nets[cfg.nNets], 0, sizeof(Net));
    cfgStore();
    snprintf(msg, sizeof(msg), "$OK removed %s", ssid); sendTo(id, msg);
    sendAll(lJson());
  }
  else if (!strcmp(c, "CLOUD")) {           // $CLOUD on verify host port user pass   (pass "*" = keep)
    char *on = field(p), *ver = field(p), *host = field(p), *port = field(p), *user = field(p), *pass = field(p);
    long pt = atol(port);
    if (strlen(host) > 64 || strlen(user) > 48 || strlen(pass) > 64 || pt < 1 || pt > 65535) { sendTo(id, "$ERR cloud settings too long or bad port"); return; }
    if (*on == '1' && !*host) { sendTo(id, "$ERR the cloud needs a server name"); return; }
    cfg.cloudOn = *on == '1'; cfg.cloudVerify = *ver != '0';
    strcpy(cfg.cloudHost, host); cfg.cloudPort = (uint16_t)pt; strcpy(cfg.cloudUser, user);
    if (strcmp(pass, "*")) strcpy(cfg.cloudPass, pass);
    cfgStore();
    sendTo(id, cfg.cloudOn ? "$OK cloud settings saved, connecting" : "$OK cloud switched off");
    sendAll(lJson());
    hwAction(A_CLOUD, id);
  }
  else if (!strcmp(c, "NAME")) {
    char *nm = field(p);
    for (char *q = nm; *q; q++) *q = tolower(*q);
    if (!goodName(nm)) { sendTo(id, "$ERR name: 1 to 24 of a-z, 0-9 and -"); return; }
    strcpy(cfg.name, nm);
    cfgStore();
    snprintf(msg, sizeof(msg), "$OK name saved: http://%s.local - the Wi-Fi module restarts", nm); sendTo(id, msg);
    hwAction(A_NAME, id);
  }
  else if (!strcmp(c, "KEY")) {             // $KEY old new
    char *old = field(p), *nw = field(p);
    if (!sameText(old, cfg.key)) { sendTo(id, "$ERR the old password is wrong"); return; }
    size_t n = strlen(nw);
    if (n < 8 || n > 32) { sendTo(id, "$ERR the new password must be 8 to 32 characters"); return; }
    for (const char *q = nw; *q; q++) if ((uint8_t)*q < 33 || (uint8_t)*q > 126) { sendTo(id, "$ERR use letters, digits and signs, no spaces"); return; }
    strcpy(cfg.key, nw);
    cfgStore();
    sendTo(id, "$OK password changed - the Wi-Fi module restarts so the hotspot and updates use it too");
    sendAll(lJson());
    hwAction(A_RESTART, id);
  }
  else { snprintf(msg, sizeof(msg), "$ERR unknown: %.40s", c); sendTo(id, msg); }
}

static void clientLine(uint8_t id, char *line) {
  if (line[0] == '$') { espCommand(id, line); return; }
  appLineToAvr(id, line);
}

// =====================================================================================
// lines from the ATmega
static void avrLine(char *line) {
  uint32_t now = nowMs();
  avrSeenAt = now; avrEver = true;
  if (line[0] == '$') {                      // for this module, from the machine's screen menu
    if (!strcmp(line, "$AP")) hwAction(A_AP, 255);
    else if (!strcmp(line, "$FORGET")) {
      uint8_t on = cfg.cloudOn, ver = cfg.cloudVerify; char h[65], u[49], pw[65]; uint16_t pt = cfg.cloudPort;
      strcpy(h, cfg.cloudHost); strcpy(u, cfg.cloudUser); strcpy(pw, cfg.cloudPass);
      char nm[25]; strcpy(nm, cfg.name);
      cfgDefaults(cfg);                      // networks and password go; name and cloud stay
      strcpy(cfg.name, nm); cfg.cloudOn = on; cfg.cloudVerify = ver; strcpy(cfg.cloudHost, h); strcpy(cfg.cloudUser, u); strcpy(cfg.cloudPass, pw); cfg.cloudPort = pt;
      cfgStore();
      hwAction(A_RESTART, 255);
    }
    return;
  }
  if (line[0] == '#' && line[1] && (line[2] == ' ' || line[2] == 0)) {
    const char *t = strchr(CACHE_TAGS, line[1]);
    if (t) { strncpy(cacheLine[t - CACHE_TAGS], line, 109); cacheLine[t - CACHE_TAGS][109] = 0; snapDirty = true; }
    if (line[1] == 'B') { avrBootAt = now; lastNote[0] = 0; cacheLine[6][0] = 0; }
    if (line[1] == 'S' && (!strcmp(line + 3, "MEASURE") || !strcmp(line + 3, "FEEDTEST") || !strcmp(line + 3, "CUT") || !strcmp(line + 3, "JOG") || !strcmp(line + 3, "WATCH")))
      lastNote[0] = 0;                       // a new job: the last note is old news
  } else if (!strncmp(line, "NOTE:", 5) || !strncmp(line, "STOPPED", 7) || !strncmp(line, "NOT STARTED", 11) || !strncmp(line, "LOCKED", 6) || !strncmp(line, "FAULT", 5)) {
    strncpy(lastNote, line, LINE_MAX - 1); lastNote[LINE_MAX - 1] = 0; snapDirty = true;
  }
  sendAll(line);
}

static char avrBuf[LINE_MAX]; static uint16_t avrLen = 0; static bool avrBad = false;

// =====================================================================================
// public part, called by the sketch
void coreInit() {
  memset(authed, 0, sizeof(authed)); memset(present, 0, sizeof(present));
  memset(cacheLine, 0, sizeof(cacheLine)); lastNote[0] = 0;
  nonceCur[0] = 0; newNonce(); newNonce();
  lastIKey[0] = 0;
}

void coreAvrByte(char c) {
  if (c == '\n' || c == '\r') {
    if (avrLen && !avrBad) { avrBuf[avrLen] = 0; avrLine(avrBuf); }
    avrLen = 0; avrBad = false;
    return;
  }
  if ((uint8_t)c < 32 || (uint8_t)c > 126) { avrBad = true; return; }   // noise
  if (avrLen < LINE_MAX - 1) avrBuf[avrLen++] = c; else avrBad = true;
}

void coreClientConnected(uint8_t id) {
  if (id >= MAX_WS) return;
  present[id] = true; authed[id] = false; joinedAt[id] = nowMs();
  snprintf(helloNonce[id], sizeof(helloNonce[id]), "%08lx%08lx", (unsigned long)hwRandom(), (unsigned long)hwRandom());
  char b[80]; snprintf(b, sizeof(b), "$HELLO %s %s " ESP_VERSION, helloNonce[id], cfg.name);
  hwToClient(id, b);
}
void coreClientGone(uint8_t id) { if (id < MAX_WS) { present[id] = false; authed[id] = false; } }

static void splitLines(uint8_t id, const char *data, size_t len) {
  char line[LINE_MAX]; size_t n = 0;
  for (size_t i = 0; i <= len; i++) {
    char c = i < len ? data[i] : '\n';
    if (c == '\n' || c == '\r') { if (n) { line[n] = 0; clientLine(id, line); n = 0; } continue; }
    if ((uint8_t)c < 32 && c != '\t') continue;
    if (n < LINE_MAX - 1) line[n++] = c;
  }
}

void coreClientText(uint8_t id, const char *data, size_t len) {
  if (id >= MAX_WS) return;
  if (!authed[id]) {                         // the first line must be the login
    char got[40] = "";
    if (len > 6 && !strncmp(data, "$AUTH\t", 6)) { size_t k = len - 6; if (k > 39) k = 39; memcpy(got, data + 6, k); got[k] = 0; char *e = strpbrk(got, "\r\n"); if (e) *e = 0; }
    uint32_t now = nowMs();
    if (badAuth >= 5 && now - badAuthAt < 15000) { hwToClient(id, "$AUTH wait"); hwAction(A_KICK, id); return; }
    uint8_t mac[32]; char want[33];
    hmac256(cfg.key, "auth:", 5, helloNonce[id], strlen(helloNonce[id]), mac);
    hex32(mac, want);
    if (got[0] && sameText(got, want)) {
      authed[id] = true; badAuth = 0;
      hwToClient(id, "$AUTH ok");
      hwToClient(id, snapText());
      hwToClient(id, lJson());
      const char *nl = (const char *)memchr(data, '\n', len);
      if (nl) splitLines(id, nl + 1, len - (nl + 1 - data));
    } else {
      if (now - badAuthAt > 60000) badAuth = 0;
      badAuth++; badAuthAt = now;
      hwToClient(id, "$AUTH bad");
      hwAction(A_KICK, id);
    }
    return;
  }
  splitLines(id, data, len);
}

// a message from the cloud: "$SIG\tnonce\tseq\tmac\n" + lines
void coreCloudText(const char *data, size_t len) {
  if (!cloudUp) return;
  const char *nl = (const char *)memchr(data, '\n', len);
  uint32_t now = nowMs();
  char head[100];
  size_t hl = nl ? (size_t)(nl - data) : len;
  if (hl >= sizeof(head) || strncmp(data, "$SIG\t", 5)) return;      // not ours: ignore quietly
  memcpy(head, data, hl); head[hl] = 0;
  char *p = head + 5;
  char *nonce = field(p), *seq = field(p), *mac = field(p);
  bool fresh = !strcmp(nonce, nonceCur) || (noncePrev[0] && !strcmp(nonce, noncePrev) && now - nonceAt < 120000);
  if (!fresh) {
    if (now - lastNonceReply > 1000) { char b[40]; snprintf(b, sizeof(b), "$NONCE %s", nonceCur); hwToClient(CLOUD_ID, b); lastNonceReply = now; }
    return;
  }
  const char *body = nl ? nl + 1 : data + len;
  size_t bl = len - (body - data);
  char pre[60]; int pl = snprintf(pre, sizeof(pre), "%s\t%s\n", nonce, seq);
  uint8_t m[32]; char want[33];
  hmac256(cfg.key, pre, pl, body, bl, m);
  hex32(m, want);
  if (!sameText(mac, want)) {
    if (now - lastNonceReply > 1000) { hwToClient(CLOUD_ID, "$AUTH bad"); lastNonceReply = now; }
    return;
  }
  uint32_t tag = (uint32_t)m[0] << 24 | (uint32_t)m[1] << 16 | (uint32_t)m[2] << 8 | m[3];
  for (uint8_t i = 0; i < NSEEN; i++) if (seenMac[i] == tag) return;             // already done once
  seenMac[seenPos] = tag; seenPos = (seenPos + 1) % NSEEN;
  splitLines(CLOUD_ID, body, bl);
  if (++nonceUses >= 48) newNonce();
}

void coreCloudUp(bool up) {
  cloudUp = up;
  if (up) { snapDirty = true; lastSnap = 0; }
}

void coreScanDone(uint8_t id, const ScanItem *it, int n) {
  // strongest first, one entry per name
  int order[24]; int k = 0;
  for (int i = 0; i < n && k < 24; i++) {
    if (!it[i].ssid[0]) continue;
    int dup = -1;
    for (int j = 0; j < k; j++) if (!strcmp(it[order[j]].ssid, it[i].ssid)) dup = j;
    if (dup >= 0) { if (it[i].rssi > it[order[dup]].rssi) order[dup] = i; continue; }
    order[k++] = i;
  }
  for (int a = 1; a < k; a++) for (int b = a; b > 0 && it[order[b]].rssi > it[order[b - 1]].rssi; b--) { int t = order[b]; order[b] = order[b - 1]; order[b - 1] = t; }
  if (k > 16) k = 16;
  size_t m = snprintf(outBuf, sizeof(outBuf), "$N [");
  for (int j = 0; j < k; j++) {
    const ScanItem &s = it[order[j]];
    m += snprintf(outBuf + m, sizeof(outBuf) - m, "%s{\"s\":\"", j ? "," : "");
    m += jsonEsc(outBuf + m, sizeof(outBuf) - m, s.ssid);
    m += snprintf(outBuf + m, sizeof(outBuf) - m, "\",\"r\":%d,\"e\":%u,\"k\":%d}", s.rssi, s.enc ? 1 : 0, findNet(s.ssid) >= 0);
  }
  snprintf(outBuf + m, sizeof(outBuf) - m, "]");
  if (id == 255) sendAll(outBuf); else sendTo(id, outBuf);
}

// best saved network in a scan: index into the scan, and the saved network in *netIdx (-1 = none)
int corePickNet(const ScanItem *it, int n, int *netIdx) {
  int best = -1; *netIdx = -1;
  uint32_t now = nowMs();
  for (int i = 0; i < n; i++) {
    int k = findNet(it[i].ssid);
    if (k < 0 || (failUntil[k] && (int32_t)(failUntil[k] - now) > 0)) continue;
    if (best < 0 || it[i].rssi > it[best].rssi) { best = i; *netIdx = k; }
  }
  return best;
}
void coreNetFailed(int k) { if (k >= 0 && k < MAX_NETS) failUntil[k] = nowMs() + 60000; }
void coreNetOk(int k) { if (k >= 0 && k < MAX_NETS) failUntil[k] = 0; }
bool coreShouldRoam(int8_t cur, int8_t best) { return cur < -70 && best >= cur + 8; }
bool coreQueueEmpty() { return qCount == 0; }
bool coreMachineIdle() { return !cacheLine[2][0] || !strcmp(cacheLine[2], "#S IDLE") || !strcmp(cacheLine[2], "#S FAULT"); }

// call often
void coreTick() {
  uint32_t now = nowMs();
  // 1. paced lines to the ATmega
  if (qCount && now - lastTx >= TX_GAP_MS) { hwToAvr(txq[qHead]); qHead = (qHead + 1) % QN; qCount--; lastTx = now; }
  // 2. the Wi-Fi line for the machine's screen: on a change (at most every 2 s) and every 5 s
  char payload[120], key[120];
  buildI(payload, sizeof(payload));
  snprintf(key, sizeof(key), "%u,%s,%s,%u", net.st, net.ip, net.ssid, net.cloud);
  bool changed = strcmp(key, lastIKey) != 0;
  if (((changed && now - lastI >= 2000) || now - lastI >= 5000) && qCount < QN - 2) {
    char fr[AVR_LINE_MAX + 4]; frameCmd(fr, sizeof(fr), payload);
    queueAvr(fr);
    strcpy(lastIKey, key); lastI = now;
  }
  // 3. ask the ATmega for its status when nobody knows it (never in its first 5 s: that would cancel an auto start)
  bool needC = !cacheLine[1][0];
  bool quiet = !avrEver || now - avrSeenAt > 60000;
  if ((needC || quiet) && anyone() && now > 5000 && (!avrBootAt || now - avrBootAt > 5000) && now - lastProbe > (needC ? 10000u : 60000u)) {
    queueAvr("?"); lastProbe = now;
  }
  // 4. Wi-Fi status to the apps every 10 s
  if (now - lastW >= 10000) { lastW = now; if (anyone()) sendAll(wJson()); }
  // 5. logins that never came (30 s, so idle sockets cannot fill all slots)
  for (uint8_t i = 0; i < MAX_WS; i++) if (present[i] && !authed[i] && now - joinedAt[i] > 30000) { present[i] = false; hwAction(A_KICK, i); }
  // 6. cloud: new nonce every 5 minutes, snapshot on change (at most every 3 s) and every minute
  if (now - nonceAt > 300000) newNonce();
  if (cloudUp && ((snapDirty && now - lastSnap >= 3000) || now - lastSnap >= 60000 || !lastSnap)) {
    hwCloudState(snapText()); lastSnap = now ? now : 1; snapDirty = false;
  }
}
