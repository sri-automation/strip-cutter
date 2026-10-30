/*
  Strip cutter - version 5: machine controller with its own screen and buttons (HMI)
  Board: Uno + WiFi (ATmega328P + ESP8266). This sketch runs on the ATmega328P.

  Pins
    D2  -> TB6600 DIR+          D3 -> TB6600 PUL+          (DIR- and PUL- to GND)
    D4  <- limit switch to GND  (pressed = knife at the top)          [was D9]
    D5  -> relay IN for the wiper motor (0 V = motor ON)              [was D10]
    D6  -> optional buzzer (+), active buzzer, other leg to GND
    A0  <- STOP / BACK button   A1 <- UP button   A2 <- DOWN button   A3 <- OK / START button
           (arrow-key front panel v2: LEFT = A0, UP = A1, DOWN = A2, RIGHT = A3)
           (each button between the pin and GND, no resistors needed)
    TFT 1.8" ST7735:  SCK D13, SDA D11, A0/DC D9, RESET D8, CS D10, LED 3.3 V, VCC 5 V, GND
    D0/D1 = serial: to the ESP8266 (DIP 1+2 ON) or to the PC over USB (DIP 3+4 ON)

  Buttons
    Home screen:  hold OK = start cutting    UP / DOWN = menu
    While cutting: STOP = stop after this piece (knife parks at the top), STOP again = stop now
                   UP / DOWN = feed 10 ms later / earlier
    Menus: UP / DOWN move, OK chooses, STOP goes back. Values: hold UP / DOWN to go faster.
    Wi-Fi & remote -> Wi-Fi details: UP / DOWN page (now, saved networks, in range),
                   OK = try the saved networks again, STOP = back.

  Serial (115200): commands must be framed as  @COMMAND*HH  where HH is the XOR of the command
  characters in hex (for example @G*47). This keeps random characters - like the Wi-Fi module's
  start-up messages - from ever starting the machine. A plain "?" or "!" line is also accepted.
    G start   X stop at the top   ! stop now   + / - feed timing 10 ms later / earlier while running
    K one cut and park   H park   W watch the switch   ? status
    L length mm   Q stop at count   S speed mm/s   A accel mm/s2   O offset ms   T test rhythm ms
    N set count (N0 = reset)   U length factor   V length offset mm
    Parking:  D switch-off lead ms   E nudge ms (1-100)   P wait before the first nudge ms   B pause between nudges ms
    F / Fn feed test   C feed until X   R roller one turn   J jog mm   Z default settings
    I wifi status from the ESP8266: I<state>,<rssi>,<ip>,<ssid>,<cloud>
  Lines this sketch sends that start with $ are for the Wi-Fi module:  $AP open the setup hotspot,
  $FORGET forget the saved networks and reset the machine password (both from the Wi-Fi & remote menu),
  $WD<page>[F] send the rows of the Wi-Fi details page, $WJ try the saved networks again now.
  The module answers with framed rows  Y<row><colour><text>  that this sketch only draws.
  Status lines start with #:  #B version  #S state  #P count total  #F test feeds  #C settings
                              #O offset  #M timing  #T knife at top  #A auto start  #K park  #R remote
*/

#include <EEPROM.h>

// ---------------- fixed settings ----------------
const float STEPS_PER_MM = 17.44;   // 1600 steps/rev on a 29.2 mm roller (use U and V to correct the length)
const float START_SPEED  = 20.0;    // mm per second
const bool  FEED_DIR     = LOW;     // change to HIGH if the net runs backwards
const float OPEN_PART    = 0.30;    // part of one turn in which the knife is safely open for feeding
const unsigned int LEAVE_TIMEOUT_MS = 2000;
const unsigned int CUT_TIMEOUT_MS   = 4000;
const long  STEPS_PER_REV = 1600;   // TB6600 microstep setting
const bool  LIMIT_PRESSED = LOW;    // switch connects pin 4 to GND when pressed
const byte  COUNT_SAVE_EVERY = 5;   // while running, the count is written to memory every 5 pieces (and at every stop)
const byte  MAX_NUDGES = 80;
const unsigned int PULSE_US = 8;
#define VERSION_TEXT "5.3"

// ---------------- settings kept in EEPROM ----------------
struct Cfg {
  float    pieceMm;    // L
  uint32_t target;     // Q  stop when the count reaches this (0 = no limit)
  float    speed;      // S
  float    accel;      // A
  int16_t  offsetMs;   // O
  uint16_t testMs;     // T
  float    lenK;       // U  net fed = lenK x length + lenC
  float    lenC;       // V
  int16_t  leadMs;     // D  park: switch off this long before the top (learnt)
  uint16_t creepMs;    // E  park: one nudge
  int16_t  kLagMs;     // extra time of the first turn from rest
  uint16_t turnMs;     // learnt: one turn
  uint16_t gapMs;      // learnt: knife leaving the top -> arriving again
  uint8_t  remote;     // 1 = the PC / phone app may start and change things, 0 = watch only
  uint8_t  autoStart;  // 1 = start by itself 3 s after power-up
  uint8_t  tftType;    // screen board type 0..2
  uint8_t  tftFlip;    // screen turned 180 degrees
  uint16_t waitMs;     // P  park: wait after the switch-off before the first nudge (the knife must have stopped)
  uint16_t pauseMs;    // B  park: wait after each nudge
};
const Cfg DEFAULTS = { 70.0, 0, 1000.0, 6000.0, 20, 2000, 1.1494, -5.86, 60, 25, 30, 0, 0, 1, 0, 0, 0, 800, 300 };   // auto start is off until chosen on the screen
const byte CFG_OLD = sizeof(Cfg) - 4;   // settings saved by 5.1 had no P and B
Cfg cfg;

const uint16_t MAGIC = 0x5C05;
const int CFG_ADDR = 0;
const int CNT_ADDR = 128;            // piece count: a ring of slots so no cell wears out
const byte CNT_SLOTS = 64;
struct CntSlot { uint32_t count; uint32_t total; uint32_t seq; byte crc; byte mark; };   // 14 bytes on the Uno

// ---------------- pins ----------------
const byte PIN_DIR = 2, PIN_PUL = 3, PIN_LIMIT = 4, PIN_RELAY = 5, PIN_BUZZ = 6;
#ifdef __AVR__
  #define PUL_HIGH()  (PORTD |= _BV(3))
  #define PUL_LOW()   (PORTD &= ~_BV(3))
  #define LIMIT_RAW() ((PIND & _BV(4)) ? HIGH : LOW)
#else
  #define PUL_HIGH()  digitalWrite(PIN_PUL, HIGH)
  #define PUL_LOW()   digitalWrite(PIN_PUL, LOW)
  #define LIMIT_RAW() digitalRead(PIN_LIMIT)
#endif

// states, as sent in "#S" and shown on the screen
enum { ST_IDLE, ST_MEASURE, ST_RUN, ST_FEEDTEST, ST_CUT, ST_PARK, ST_JOG, ST_WATCH, ST_FAULT };
const char STN0[] PROGMEM = "IDLE", STN1[] PROGMEM = "MEASURE", STN2[] PROGMEM = "RUN", STN3[] PROGMEM = "FEEDTEST",
           STN4[] PROGMEM = "CUT", STN5[] PROGMEM = "PARK", STN6[] PROGMEM = "JOG", STN7[] PROGMEM = "WATCH", STN8[] PROGMEM = "FAULT";
const char *const STNAMES[] PROGMEM = { STN0, STN1, STN2, STN3, STN4, STN5, STN6, STN7, STN8 };

bool running = false, stopAsked = false, abortAsked = false;
byte curState = ST_IDLE;
uint32_t made = 0, total = 0;         // pieces made (resettable) and all pieces ever (kept)
uint32_t savedMade = 0, cntSeq = 0;
int cntSlot = -1;
unsigned int testMade = 0;
double wantSteps = 0;
long doneSteps = 0;
float rateNow = 0;                    // pieces per minute while running
unsigned long feedPlanMs = 0, feedRealMs = 0, openMs = 0;
const __FlashStringHelper *faultMsg = 0, *noteMsg = 0;

// Wi-Fi status, as told by the ESP8266
byte wifiState = 0;                   // 0 = no word from the Wi-Fi module, 1 = looking, 2 = connected, 3 = setup hotspot
int8_t wifiRssi = 0;
byte cloudState = 0;                  // 0 = off, 1 = connecting, 2 = online
char wifiIp[16] = "", wifiSsid[21] = "";
unsigned long wifiSeen = 0;

// screen and buttons (hmi.h)
void quickKeys();
void abortNow();
void uiDirty(byte what);
void uiDraw();
void uiStateChanged();
void uiBusyButtons();
void uiSetup();
void uiIdle();
bool uiAutoStartWait();
void uiSplashEnd();
void wifiDetail(const char *p);
#define D_HEAD  0x01
#define D_COUNT 0x02
#define D_INFO  0x04
#define D_ALL   0xFF

// ---------------- memory ----------------
byte crc8(const byte *p, byte n) {
  byte c = 0;
  while (n--) { c ^= *p++; for (byte i = 0; i < 8; i++) c = (c & 0x80) ? (byte)((c << 1) ^ 0x07) : (byte)(c << 1); }
  return c;
}

void saveCfg() {                         // EEPROM.put only writes the bytes that changed
  EEPROM.put(CFG_ADDR, MAGIC);
  EEPROM.put(CFG_ADDR + 2, cfg);
  EEPROM.update(CFG_ADDR + 2 + sizeof(Cfg), crc8((const byte *)&cfg, sizeof(Cfg)));
}

bool cfgSane(const Cfg &c) {
  return c.pieceMm >= 5 && c.pieceMm <= 2000 && c.speed >= 30 && c.speed <= 2000 && c.accel >= 500 && c.accel <= 30000 &&
         c.offsetMs >= -500 && c.offsetMs <= 500 && c.testMs >= 200 && c.lenK >= 0.5 && c.lenK <= 1.5 &&
         c.lenC >= -50 && c.lenC <= 50 && c.leadMs >= -100 && c.leadMs <= 400 && c.creepMs >= 1 && c.creepMs <= 100 &&
         c.kLagMs >= -100 && c.kLagMs <= 300 && c.remote <= 1 && c.autoStart <= 1 && c.tftType <= 2 && c.tftFlip <= 1 &&
         c.waitMs >= 100 && c.waitMs <= 5000 && c.pauseMs >= 50 && c.pauseMs <= 5000;
}

bool loadCfg() {
  uint16_t m; EEPROM.get(CFG_ADDR, m);
  if (m != MAGIC) return false;
  Cfg c; EEPROM.get(CFG_ADDR + 2, c);
  if (EEPROM.read(CFG_ADDR + 2 + sizeof(Cfg)) != crc8((const byte *)&c, sizeof(Cfg)) || !cfgSane(c)) {
    c.waitMs = DEFAULTS.waitMs; c.pauseMs = DEFAULTS.pauseMs;          // kept by 5.1: the same, without P and B
    if (EEPROM.read(CFG_ADDR + 2 + CFG_OLD) != crc8((const byte *)&c, CFG_OLD) || !cfgSane(c)) return false;
  }
  cfg = c;
  return true;
}

void loadCount() {
  bool found = false;
  for (byte i = 0; i < CNT_SLOTS; i++) {
    CntSlot s; EEPROM.get(CNT_ADDR + i * (int)sizeof(CntSlot), s);
    if (s.mark != 0xA5 || s.crc != crc8((const byte *)&s, 12)) continue;
    if (!found || (long)(s.seq - cntSeq) > 0) { found = true; cntSeq = s.seq; made = s.count; total = s.total; cntSlot = i; }
  }
  if (!found) { made = 0; total = 0; cntSeq = 0; cntSlot = -1; }
  savedMade = made;
}

uint32_t savedTotal = 0;
void saveCount() {                       // next slot in the ring, highest sequence number wins at power-up
  if (made == savedMade && total == savedTotal && cntSlot >= 0) return;
  cntSlot = (cntSlot + 1) % CNT_SLOTS;
  cntSeq++;
  CntSlot s = { made, total, cntSeq, 0, 0xA5 };
  s.crc = crc8((const byte *)&s, 12);
  EEPROM.put(CNT_ADDR + cntSlot * (int)sizeof(CntSlot), s);
  savedMade = made; savedTotal = total;
}

void sp(long v) { Serial.print(' '); Serial.print(v); }           // " value" for the status lines
void spf(float v, byte d) { Serial.print(' '); Serial.print(v, d); }
void sayTop(bool s) { Serial.print(F("#T")); sp(s); Serial.println(); }
void offStep(bool up) { cfg.offsetMs += up ? 10 : -10; Serial.print(F("#O")); sp(cfg.offsetMs); Serial.println(); uiDirty(D_INFO); }   // feed timing +/- 10 ms
void sayCount() { Serial.print(F("#P")); sp(made); sp(total); Serial.println(); uiDirty(D_COUNT); }

// ---------------- buzzer (optional) ----------------
unsigned long buzzOff = 0;
void beep(unsigned int ms) { digitalWrite(PIN_BUZZ, HIGH); buzzOff = millis() + ms; }
void buzzTick() { if (buzzOff && (long)(millis() - buzzOff) >= 0) { digitalWrite(PIN_BUZZ, LOW); buzzOff = 0; } }

// ---------------- wiper motor, states, faults ----------------
void motor(bool on) { digitalWrite(PIN_RELAY, on ? LOW : HIGH); }   // relay is ON at 0 V

char lastTop = -1;                       // knife-at-top as last told to the app
void state(byte s) {
  curState = s;
  if (s == ST_IDLE || s == ST_FAULT) lastTop = -1;   // after any job, tell the app where the knife is
  Serial.print(F("#S ")); Serial.println((const __FlashStringHelper *)pgm_read_ptr(&STNAMES[s]));
  uiStateChanged();
}

void fault(const __FlashStringHelper *why) {
  motor(false);
  running = false;
  saveCount();
  Serial.print(F("STOPPED: "));
  Serial.println(why);
  faultMsg = why;
  beep(700);
  state(ST_FAULT);
}

void note(const __FlashStringHelper *msg) {   // a message for the screen (and the PC / phone app)
  Serial.print(F("NOTE: ")); Serial.println(msg);
  noteMsg = msg; uiDirty(D_INFO);
}

// ---------------- limit switch as a clock ----------------
bool swRaw = false, swState = false;
unsigned long swChangeUs = 0;
unsigned long tPressUs = 0, tReleaseUs = 0, periodUs = 0, pressedUs = 0;
unsigned int  pressCount = 0, releaseCount = 0;

// the pin-change interrupt notes the exact time of every change, so drawing the screen never spoils the timing
volatile bool isrRaw = false;
volatile unsigned long isrChangeUs = 0;
#ifdef __AVR__
ISR(PCINT2_vect) {
  bool r = LIMIT_RAW() == LIMIT_PRESSED;
  if (r != isrRaw) { isrRaw = r; isrChangeUs = micros(); }
}
#endif

void pollSwitch() {
  noInterrupts(); bool raw = isrRaw; unsigned long ch = isrChangeUs; interrupts();
  swRaw = raw; swChangeUs = ch;
  unsigned long now = micros();
  if (raw != swState && now - swChangeUs >= 5000UL) {      // steady for 5 ms
    swState = raw;
    if (raw) {
      if (pressCount) periodUs = swChangeUs - tPressUs;
      tPressUs = swChangeUs;
      pressCount++;
    } else {
      pressedUs = swChangeUs - tPressUs;
      tReleaseUs = swChangeUs;
      releaseCount++;
    }
  }
}

void resetSwitchClock() {
  swRaw = swState = (LIMIT_RAW() == LIMIT_PRESSED);
  swChangeUs = micros();
  noInterrupts(); isrRaw = swRaw; isrChangeUs = swChangeUs; interrupts();
  pressCount = 0; releaseCount = 0; periodUs = 0; pressedUs = 0;
}

void watchFor(unsigned long ms) {
  unsigned long t0 = millis();
  while (millis() - t0 < ms) { pollSwitch(); quickKeys(); if (abortAsked) return; }
}

bool waitPresses(unsigned int target, unsigned long timeoutMs) {
  unsigned long t0 = millis();
  while (pressCount < target) {
    pollSwitch(); quickKeys();
    if (abortAsked) return false;
    if (millis() - t0 > timeoutMs) return false;
  }
  return true;
}

bool atTop() {
  bool s = digitalRead(PIN_LIMIT) == LIMIT_PRESSED;
  unsigned long t = millis();
  while (millis() - t < 10) {
    bool n = digitalRead(PIN_LIMIT) == LIMIT_PRESSED;
    if (n != s) { s = n; t = millis(); }
  }
  return s;
}

// ---------------- serial link: framed command lines ----------------
char lineBuf[64];
byte lineLen = 0;
bool lineBad = false;

bool linkRead() {                        // true when a whole clean text line is in lineBuf
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen) { lineBuf[lineLen] = 0; bool ok = !lineBad; lineLen = 0; lineBad = false; if (ok) return true; }
      lineBad = false;
      continue;
    }
    if (c < 32 || c > 126) { lineBad = true; continue; }     // not text: noise, e.g. the Wi-Fi module starting up
    if (lineLen < sizeof(lineBuf) - 1) lineBuf[lineLen++] = c; else lineBad = true;
  }
  return false;
}

byte hexVal(char h) { return h >= '0' && h <= '9' ? h - '0' : ((h | 0x20) >= 'a' && (h | 0x20) <= 'f' ? (h | 0x20) - 'a' + 10 : 16); }

bool linkFrame() {                       // checks "@cmd*HH", leaves "cmd" in lineBuf
  if ((lineBuf[0] == '!' || lineBuf[0] == '?') && lineBuf[1] == 0) return true;
  if (lineBuf[0] != '@') return false;
  char *star = strrchr(lineBuf, '*');
  if (!star || star[1] == 0 || star[2] == 0 || star[3] != 0) return false;
  byte x = 0;
  for (char *p = lineBuf + 1; p < star; p++) x ^= *p;
  byte h = hexVal(star[1]), l = hexVal(star[2]);
  if (h > 15 || l > 15 || x != (byte)((h << 4) | l)) return false;
  *star = 0;
  memmove(lineBuf, lineBuf + 1, star - lineBuf);
  return lineBuf[0] != 0;
}

void wifiInfo(const char *p) {           // "state,rssi,ip,ssid,cloud"
  wifiState = atoi(p);
  const char *q = strchr(p, ','); if (!q) return; wifiRssi = atoi(++q);
  q = strchr(q, ','); if (!q) return; q++;
  byte i = 0; while (*q && *q != ',' && i < sizeof(wifiIp) - 1) wifiIp[i++] = *q++; wifiIp[i] = 0;
  if (*q == ',') q++;
  i = 0; while (*q && *q != ',' && i < sizeof(wifiSsid) - 1) wifiSsid[i++] = *q++; wifiSsid[i] = 0;
  while (*q && *q != ',') q++;
  cloudState = (*q == ',') ? atoi(q + 1) : 0;
  wifiSeen = millis(); if (!wifiSeen) wifiSeen = 1;
  uiDirty(D_HEAD);
}

void quickKeys() {                       // while something is running: stop keys and the buttons; never waits
  if (linkRead() && linkFrame()) {
    char c = lineBuf[0];
    if (c == 'X' || c == 'x') { stopAsked = true; Serial.println(F("stopping")); }
    else if (c == '!') { abortAsked = true; stopAsked = true; motor(false); }
    else if ((c == '+' || c == '-') && running && cfg.remote) offStep(c == '+');
    else if (c == 'I') wifiInfo(lineBuf + 1);
    else if (c != '?' && c != 'Y') Serial.println(F("busy"));
  }
  uiBusyButtons();
  buzzTick();
}

// ---------------- parking at the top ----------------
// The cutter is running at speed. predPress = when the switch is expected to be pressed next (micros),
// skip = presses that will come before that one. The motor is switched off D ms before predPress and the
// knife coasts. P ms later (it must have stopped by then) it is on the switch, past it, or short of it.
// Short of it: nudges of E ms, B ms apart. In a nudge the motor goes off the moment the switch closes,
// so a long nudge cannot drive the knife on past the top; a nudge too short to move the knife grows
// a little every second try.
// Result: 0 = coasted onto the switch, 1 = reached it with nudges, 2 = went past the top, 3 = stopped by ! or no switch,
//         4 = the nudges never reached the switch
byte nudges = 0;
bool lastEarly = false, nudgeOver = false;
byte coastToTop(unsigned long predPress, byte skip) {
  unsigned int p0 = pressCount;
  nudges = 0; lastEarly = false; nudgeOver = false;
  unsigned long t0 = millis();
  unsigned long offAt = predPress - (long)cfg.leadMs * 1000L;
  while ((long)(micros() - offAt) < 0) {
    pollSwitch(); quickKeys();
    if (abortAsked) { motor(false); return 3; }
    if (pressCount - p0 > skip) { lastEarly = true; break; }
    if (millis() - t0 > 2UL * CUT_TIMEOUT_MS) { motor(false); return 3; }
  }
  motor(false);
  unsigned long tOff = micros();
  unsigned int pOff = pressCount, rOff = releaseCount;
  watchFor(cfg.waitMs);                  // let the knife stop before looking (and before any nudge)
  if (abortAsked) return 3;
  Serial.print(F("park: off ")); Serial.print((long)(predPress - tOff) / 1000L); Serial.print(F(" ms early"));
  if (lastEarly) Serial.print(F(", top came early"));
  else if (pressCount != pOff) {
    Serial.print(F(", on switch after ")); Serial.print((tPressUs - tOff) / 1000UL); Serial.print(F(" ms"));
    if (releaseCount != rOff) { Serial.print(F(", off it after ")); Serial.print((tReleaseUs - tPressUs) / 1000UL); Serial.print(F(" ms")); }
  } else if (!swState) Serial.print(F(", stopped short"));
  Serial.println();
  if (swState) {
    watchFor(200);
    if (swState) return 0;
    return 2;
  }
  if (pressCount - p0 > skip) return 2;
  unsigned int on = cfg.creepMs;
  byte touches = 0;
  for (nudges = 1; nudges <= MAX_NUDGES; nudges++) {
    unsigned int p1 = pressCount;
    bool touched = false;
    motor(true);
    unsigned long t = micros();
    while (micros() - t < on * 1000UL) {           // the nudge, cut short the moment the switch closes
      if (touches < 3 && LIMIT_RAW() == LIMIT_PRESSED) {
        byte k = 0;                                  // closed for 0.4 ms, so motor noise on the wire does not count
        while (k < 8 && LIMIT_RAW() == LIMIT_PRESSED) { delayMicroseconds(50); k++; }
        if (k == 8) { touched = true; break; }
      }
    }
    motor(false);
    watchFor(cfg.pauseMs);
    if (abortAsked) return 3;
    if (swState) { watchFor(200); if (swState) return 1; }
    if (pressCount != p1) {
      cfg.creepMs = cfg.creepMs * 2 / 3 ? cfg.creepMs * 2 / 3 : 1;
      nudgeOver = true;
      Serial.print(F("park: a nudge of ")); Serial.print(on); Serial.print(F(" ms went over, now ")); Serial.print(cfg.creepMs); Serial.println(F(" ms"));
      return 2;
    }
    if (touched) { on = cfg.creepMs; touches++; }  // right at the switch: keep the pushes small
    else { touches = 0; if (!(nudges & 1) && on < 100) on += on / 4 + 1; }
  }
  return 4;
}

byte overRun = 0;
void learnFrom(byte r) {
  int d = 0;
  if (r == 2 && !nudgeOver) { if (overRun < 4) overRun++; } else overRun = 0;
  if (r == 0 && lastEarly) d = 5;
  else if (r == 2 && !nudgeOver) d = 25 * overRun;
  else if (r == 2 && nudgeOver) d = -5;
  else if (r == 1 && nudges > 3) { d = -2 * (nudges - 3); if (d < -10) d = -10; }
  else if (r == 4) d = -10;
  int n = cfg.leadMs + d;
  cfg.leadMs = n < -100 ? -100 : (n > 400 ? 400 : n);
}

bool waitEdge(bool press) {
  unsigned int c = press ? pressCount : releaseCount;
  unsigned long t0 = millis();
  while ((press ? pressCount : releaseCount) == c) {
    pollSwitch(); quickKeys();
    if (abortAsked) return false;
    if (millis() - t0 > CUT_TIMEOUT_MS) return false;
  }
  return true;
}

byte parkViaRelease() {
  if (!swState && !waitEdge(true)) { motor(false); return 3; }
  if (!waitEdge(false)) { motor(false); return 3; }
  unsigned long tRel = tReleaseUs;
  if (!cfg.gapMs) {
    if (!waitEdge(true)) { motor(false); return 3; }
    cfg.gapMs = (tPressUs - tRel) / 1000UL;
    cfg.turnMs = (tPressUs - tRel) / 1000UL + pressedUs / 1000UL;
    Serial.print(F("park: one turn ")); Serial.print(cfg.turnMs); Serial.println(F(" ms"));
    if (!waitEdge(false)) { motor(false); return 3; }
    tRel = tReleaseUs;
  }
  byte r = coastToTop(tRel + (unsigned long)cfg.gapMs * 1000UL, 0);
  learnFrom(r);
  return r;
}

byte parkFinish(byte r) {
  byte tries = 0;
  while (r == 2 && tries < 6) {
    tries++;
    Serial.print(F("past the top, round again (lead ")); Serial.print(cfg.leadMs); Serial.println(F(" ms)"));
    motor(true);
    r = parkViaRelease();
  }
  return r;
}

void parkReport(byte r) {
  Serial.print(F("#K")); sp(r); sp(nudges); sp(cfg.leadMs); sp(cfg.creepMs); Serial.println();
  saveCfg();
}

void parkFault(byte r) {
  if (r == 3) fault(F("The knife never reached the top: switch not pressed."));
  else if (r == 4) fault(F("Could not park: nudges never reached the top. Raise Nudge (E)."));
  else if (nudgeOver) fault(F("Could not park: even short nudges carry the knife over the switch."));
  else fault(F("Could not park: it keeps coasting past the top. Raise lead (D)."));
}

byte parkFromRun() {
  unsigned long T = periodUs ? periodUs : (unsigned long)cfg.turnMs * 1000UL;
  unsigned long next = tPressUs + T;
  byte skip = 0;
  if ((long)(next - micros()) < (long)cfg.leadMs * 1000L + 20000L) { next += T; skip = 1; }
  byte r = coastToTop(next, skip);
  learnFrom(r);
  r = parkFinish(r);
  parkReport(r);
  return r;
}

bool parkFromRest(bool oneCut) {
  abortAsked = false; stopAsked = false;
  resetSwitchClock();
  if (swState && !oneCut) { Serial.println(F("already at the top")); return true; }
  byte r;
  motor(true);
  if (swState) {
    if (!waitEdge(false)) {
      motor(false);
      if (abortAsked) abortNow(); else fault(F("Switch stays pressed with the motor on: motor or switch wiring?"));
      return false;
    }
    if (cfg.gapMs) {
      r = coastToTop(tReleaseUs + (unsigned long)cfg.gapMs * 1000UL + (long)cfg.kLagMs * 1000L, 0);
      learnFrom(r);
    } else r = parkViaRelease();
  } else {
    r = parkViaRelease();
  }
  if (r == 3 && !abortAsked) { parkFault(3); return false; }
  r = parkFinish(r);
  if (abortAsked) { abortNow(); return false; }
  parkReport(r);
  if (r > 1) { parkFault(r); return false; }
  return true;
}

// ---------------- stepper feed ----------------
float feedLen(float mm) { float f = mm * cfg.lenK + cfg.lenC; return f < 1.0 ? 1.0 : f; }

float feedSeconds(float mm) {
  float n = mm * STEPS_PER_MM, v0 = START_SPEED * STEPS_PER_MM, vm = cfg.speed * STEPS_PER_MM, a = cfg.accel * STEPS_PER_MM;
  if (vm < v0) vm = v0;
  float r = (vm * vm - v0 * v0) / (2.0 * a);
  if (2.0 * r >= n) { float vp = sqrt(v0 * v0 + a * n); return 2.0 * (vp - v0) / a; }
  return 2.0 * (vm - v0) / a + (n - 2.0 * r) / vm;
}

#ifdef __AVR__
// Timer1 makes each step pulse on time; the main loop works out the speed for the next pulses:
//   speed = sqrt(v0^2 + 2 a x), x = steps from the nearer end of the move, never above the top speed.
volatile long isrLeft = 0, isrDone = 0;
volatile uint16_t isrNext = 0;

ISR(TIMER1_COMPA_vect) {
  if (isrLeft > 0) {
    PUL_HIGH();
    isrLeft--; isrDone++;
    OCR1A = isrNext;
    __builtin_avr_delay_cycles(PULSE_US * 16 - 30);
    PUL_LOW();
  }
  if (isrLeft <= 0) TIMSK1 &= ~_BV(OCIE1A);
}

void moveSteps(long n) {
  if (n == 0) return;
  bool fwd = n > 0;
  long N = fwd ? n : -n;
  digitalWrite(PIN_DIR, fwd ? FEED_DIR : !FEED_DIR);
  delayMicroseconds(20);
  float v0 = START_SPEED * STEPS_PER_MM, vm = cfg.speed * STEPS_PER_MM, a = cfg.accel * STEPS_PER_MM;
  if (vm < v0) vm = v0;
  float v0sq = v0 * v0, twoA = 2.0 * a;
  uint16_t first = (uint16_t)(2000000.0 / v0);
  noInterrupts();
  isrLeft = N; isrDone = 0; isrNext = first;
  TCCR1A = 0; TCCR1B = 0; TCNT1 = 0;
  OCR1A = first;
  TIFR1 = _BV(OCF1A);
  TCCR1B = _BV(WGM12) | _BV(CS11);
  TIMSK1 |= _BV(OCIE1A);
  interrupts();
  for (;;) {
    noInterrupts(); long left = isrLeft, done = isrDone; interrupts();
    if (left <= 0) break;
    long x = done < left ? done : left;
    float v = sqrt(v0sq + twoA * x);
    if (v > vm) v = vm;
    uint16_t t = (uint16_t)(2000000.0 / v);
    noInterrupts(); isrNext = t; interrupts();
    pollSwitch();
  }
  TCCR1B = 0;
  TIMSK1 &= ~_BV(OCIE1A);
}
#else
void moveSteps(long n) {
  if (n == 0) return;
  bool fwd = n > 0;
  long N = fwd ? n : -n;
  digitalWrite(PIN_DIR, fwd ? FEED_DIR : !FEED_DIR);
  delayMicroseconds(20);
  float v0 = START_SPEED * STEPS_PER_MM, vm = cfg.speed * STEPS_PER_MM, a = cfg.accel * STEPS_PER_MM;
  if (vm < v0) vm = v0;
  unsigned long due = micros() + (unsigned long)(1000000.0 / v0);
  for (long done = 0; done < N; ) {
    while ((long)(micros() - due) < 0) pollSwitch();
    PUL_HIGH(); delayMicroseconds(PULSE_US); PUL_LOW();
    done++;
    long left = N - done, x = done < left ? done : left;
    float v = sqrt(v0 * v0 + 2.0 * a * x);
    if (v > vm) v = vm;
    due += (unsigned long)(1000000.0 / v);
  }
}
#endif

void feed(float mm) {
  wantSteps += (double)mm * STEPS_PER_MM;
  long target = lround(wantSteps);
  moveSteps(target - doneSteps);
  doneSteps = target;
}

// ---------------- running ----------------
void abortNow() {
  motor(false);
  running = false;
  saveCount();
  saveCfg();
  Serial.print(F("STOPPED NOW. Pieces made: ")); Serial.println(made);
  note(F("Stopped now. Knife may be down: park it before feeding."));
  state(ST_IDLE);
}

void finishRun() {
  running = false;
  saveCount();
  saveCfg();
  Serial.print(F("DONE, pieces made: ")); Serial.println(made);
  beep(150);
  state(ST_IDLE);
}

bool targetReached() { return cfg.target > 0 && made >= cfg.target; }

void stopRun() {
  state(ST_PARK);
  byte r = parkFromRun();
  if (abortAsked) { abortNow(); return; }
  if (r > 1) { parkFault(r); return; }
  finishRun();
}

void runContinuous() {
  wantSteps = 0; doneSteps = 0; stopAsked = false; abortAsked = false; noteMsg = 0; faultMsg = 0;
  if (targetReached()) {
    Serial.println(F("NOT STARTED: stop count reached."));
    note(F("Count reached the stop count. Reset the count or raise it."));
    state(ST_IDLE);
    return;
  }
  Serial.println(F("GO - measuring the cutter"));
  state(ST_MEASURE);
  sayCount();
  resetSwitchClock();
  motor(true);
  if (!waitPresses(1, (unsigned long)LEAVE_TIMEOUT_MS + CUT_TIMEOUT_MS) || !waitPresses(3, 2UL * CUT_TIMEOUT_MS)) {
    if (abortAsked) abortNow();
    else fault(F("No switch signal while the motor runs: motor or switch wiring?"));
    return;
  }
  const unsigned long T0 = periodUs;
  float fl = feedLen(cfg.pieceMm);
  unsigned long feedUs = (unsigned long)(feedSeconds(fl) * 1000000.0);
  unsigned long openUs = (unsigned long)(OPEN_PART * T0);
  cfg.turnMs = T0 / 1000UL;
  cfg.gapMs = (T0 - pressedUs) / 1000UL;
  feedPlanMs = feedUs / 1000; openMs = openUs / 1000; feedRealMs = 0;
  Serial.print(F("#M"));                // one turn, switch pressed, feed, knife open (ms) sp(T0 / 1000); sp(pressedUs / 1000); sp(feedUs / 1000); sp(openUs / 1000); Serial.println();
  uiDirty(D_INFO);
  if (feedUs > openUs) {
    Serial.println(F("NOT STARTED: the feed is longer than the knife is open. Raise A or S."));
    note(F("Feed too slow for the cutter: raise acceleration."));
    stopRun();
    return;
  }
  long spare = (long)(openUs / 2) - (long)(feedUs / 2) - labs((long)cfg.offsetMs * 1000L);
  if (spare < 0) {
    if (cfg.offsetMs > 0) note(F("Feed ends after the knife starts to close: lower the offset."));
    else note(F("Feed starts before the knife is open: raise the offset."));
  }
  if (stopAsked) { stopRun(); return; }
  running = true;
  state(ST_RUN);
  byte missed = 0, slow = 0;
  unsigned long Tp = T0;                 // the usual turn: follows slow changes, not a single slow (hard) cut
  bool firstFeed = true, savePending = false;
  unsigned long lastPieceMs = 0;

  while (true) {
    if (stopAsked || targetReached()) break;
    unsigned int edge = pressCount;
    unsigned long T = periodUs;
    if (T > Tp + Tp / 2) {               // a slow turn (a hard cut): logged, and the next feed is timed from the usual turn
      Serial.print(F("run: slow turn ")); Serial.print(T / 1000); Serial.print(F(" ms, usual ")); Serial.println(Tp / 1000);
      if (++slow > 2) T = 0;             // three in a row: stop
    } else { slow = 0; Tp = (3 * Tp + T) / 4; }
    if (T > 3 * T0 || T < T0 / 2 || Tp > T0 + T0 / 2) { fault(F("Cutter speed changed a lot: jam, hard cuts, weak 12 V supply?")); return; }

    unsigned long startUs = tPressUs + pressedUs / 2 + Tp - feedUs / 2 + (long)cfg.offsetMs * 1000L;
    while ((long)(micros() - startUs) < 0) {
      pollSwitch();
      quickKeys();
      if (abortAsked) { abortNow(); return; }
      if (stopAsked) break;
      if (micros() - tPressUs > Tp + Tp / 2) { fault(F("No limit switch signal for too long: cutter stalled?")); return; }
      if (micros() - tPressUs > Tp / 2 && (long)(startUs - micros()) > 60000L) {      // mid-turn: nothing to time
        if (savePending) { saveCount(); savePending = false; }
        else uiDraw();
      }
    }
    if (stopAsked) break;
    if (pressCount != edge) {
      if (++missed > 3) { fault(F("Feed timing lost (offset too large?).")); return; }
      continue;
    }
    missed = 0;

    unsigned long f0 = micros();
    feed(fl);
    unsigned long took = micros() - f0;
    made++; total++;
    unsigned long nowMs = millis();
    if (lastPieceMs) rateNow = 60000.0 / (nowMs - lastPieceMs);
    lastPieceMs = nowMs;
    sayCount();
    if (made - savedMade >= COUNT_SAVE_EVERY) savePending = true;
    if (firstFeed) {
      firstFeed = false; feedRealMs = took / 1000;
      Serial.print(F("#M")); sp(T0 / 1000); sp(pressedUs / 1000); sp(feedUs / 1000); sp(openUs / 1000); sp(took / 1000); Serial.println();
    }

    unsigned long w0 = millis();
    while (pressCount == edge) {
      pollSwitch();
      quickKeys();
      if (abortAsked) { abortNow(); return; }
      if (millis() - w0 > Tp / 500) { fault(F("Limit switch not pressed after the feed: cutter stalled?")); return; }   // 2 turns
    }
  }
  running = false;
  rateNow = 0;
  periodUs = Tp;                         // park from the usual turn, not from a slow last cut
  stopRun();
}

// ---------------- feeder tests: the cutter motor stays off ----------------
void feederTest(unsigned int count) {
  motor(false);
  testMade = 0; wantSteps = 0; doneSteps = 0; stopAsked = false; abortAsked = false; noteMsg = 0;
  if (!atTop()) note(F("Knife is not at the top: the net may run into it."));
  float fl = feedLen(cfg.pieceMm);
  Serial.print(F("FEEDER TEST, pieces: ")); Serial.println(count);
  state(ST_FEEDTEST);
  Serial.println(F("#F 0"));
  while (true) {
    unsigned long t0 = millis();
    feed(fl);
    testMade++;
    Serial.print(F("#F ")); Serial.println(testMade);
    uiDirty(D_COUNT);
    if (count > 0 && testMade >= count) break;
    while (millis() - t0 < cfg.testMs && !stopAsked) { quickKeys(); uiDraw(); }
    if (stopAsked || abortAsked) break;
  }
  Serial.print(F("feeder test done: ")); Serial.print(testMade); Serial.println(F(" pieces"));
  state(ST_IDLE);
}

void jog(float mm) { state(ST_JOG); moveSteps(lround(mm * STEPS_PER_MM)); state(ST_IDLE); }
void rollerTurn() { motor(false); state(ST_JOG); moveSteps(STEPS_PER_REV); Serial.print(F("roller one turn: about ")); Serial.print(STEPS_PER_REV / STEPS_PER_MM, 1); Serial.println(F(" mm")); state(ST_IDLE); }

void cutOnce() { noteMsg = 0; faultMsg = 0; state(ST_CUT); if (parkFromRest(true)) state(ST_IDLE); }
void parkOnly() { noteMsg = 0; faultMsg = 0; state(ST_PARK); if (parkFromRest(false)) state(ST_IDLE); }

void watchSwitch() {
  state(ST_WATCH);
  unsigned long t0 = millis();
  bool last = !atTop();
  while (millis() - t0 < 10000) {
    bool s = atTop();
    pollSwitch();
    if (s != last) { last = s; sayTop(s); uiDirty(D_INFO); }
    quickKeys(); uiDraw();
    if (stopAsked) break;
  }
  stopAsked = false;
  state(ST_IDLE);
}

// ---------------- status for the PC / phone app ----------------
void showStatus() {
  // length, target, speed, offset, test rhythm, made, knife at top, steps/mm, accel, factor, offset mm,
  // park lead, nudge, one turn, remote allowed, auto start, wait before the first nudge, pause between nudges
  Serial.print(F("#C")); spf(cfg.pieceMm, 1); sp(cfg.target); spf(cfg.speed, 0); sp(cfg.offsetMs); sp(cfg.testMs);
  sp(made); sp(swState); spf(STEPS_PER_MM, 2); spf(cfg.accel, 0); spf(cfg.lenK, 4); spf(cfg.lenC, 2);
  sp(cfg.leadMs); sp(cfg.creepMs); sp(cfg.turnMs); sp(cfg.remote); sp(cfg.autoStart); sp(cfg.waitMs); sp(cfg.pauseMs);
  Serial.println();
}

void settingsChanged() { saveCfg(); showStatus(); uiDirty(D_ALL); }

// a small number reader for commands (no String class)
float parseNum(const char *s, long *whole) {
  bool neg = false; float v = 0; long w = 0;
  while (*s == ' ') s++;
  if (*s == '-') { neg = true; s++; } else if (*s == '+') s++;
  while (*s >= '0' && *s <= '9') { w = w * 10 + (*s - '0'); v = v * 10 + (*s - '0'); s++; }
  if (*s == '.') { s++; float f = 0.1; while (*s >= '0' && *s <= '9') { v += (*s - '0') * f; f *= 0.1; s++; } }
  if (whole) *whole = neg ? -w : w;
  return neg ? -v : v;
}

void dispatch(char *s) {
  char c = toupper(s[0]);
  long n; float v = parseNum(s + 1, &n);
  bool has = s[1] != 0;
  if (c == '?') { showStatus(); sayCount(); return; }
  if (c == 'I') { wifiInfo(s + 1); return; }
  if (c == 'Y') { wifiDetail(s + 1); return; }       // a row of the Wi-Fi details page
  if (c == '!') { motor(false); Serial.println(F("cutter motor is off")); state(ST_IDLE); return; }
  if (c == 'X') { Serial.println(F("nothing is running")); return; }
  if (!cfg.remote) {                       // the machine panel has locked remote control
    Serial.println(F("#R 0"));
    Serial.println(F("LOCKED: remote control is off on the machine's screen."));
    return;
  }
  if (c == 'G') runContinuous();
  else if (c == 'K') cutOnce();
  else if (c == 'H') parkOnly();
  else if (c == 'W') watchSwitch();
  else if (c == 'L' && v >= 5 && v <= 2000) { cfg.pieceMm = v; settingsChanged(); }
  else if (c == 'Q' && has && n >= 0 && n <= 99999999L) { cfg.target = (uint32_t)n; settingsChanged(); }
  else if (c == 'S' && v >= 30 && v <= 2000) { cfg.speed = v; settingsChanged(); }
  else if (c == 'A' && v >= 500 && v <= 30000) { cfg.accel = v; settingsChanged(); }
  else if (c == 'O' && has && v >= -500 && v <= 500) { cfg.offsetMs = (int)v; settingsChanged(); }
  else if (c == 'T' && v >= 200 && v <= 60000) { cfg.testMs = (unsigned int)v; settingsChanged(); }
  else if (c == 'U' && v >= 0.5 && v <= 1.5) { cfg.lenK = v; settingsChanged(); }
  else if (c == 'V' && has && v >= -50 && v <= 50) { cfg.lenC = v; settingsChanged(); }
  else if (c == 'D' && has && v >= -100 && v <= 400) { cfg.leadMs = (int)v; settingsChanged(); }
  else if (c == 'E' && v >= 1 && v <= 100) { cfg.creepMs = (unsigned int)v; settingsChanged(); }
  else if (c == 'P' && v >= 100 && v <= 5000) { cfg.waitMs = (unsigned int)v; settingsChanged(); }
  else if (c == 'B' && v >= 50 && v <= 5000) { cfg.pauseMs = (unsigned int)v; settingsChanged(); }
  else if (c == 'N' && has && n >= 0 && n <= 99999999L) { made = (uint32_t)n; saveCount(); sayCount(); showStatus(); }
  else if (c == 'Z') { Cfg k = cfg; cfg = DEFAULTS; cfg.turnMs = k.turnMs; cfg.gapMs = k.gapMs; cfg.leadMs = k.leadMs; cfg.tftType = k.tftType; cfg.tftFlip = k.tftFlip; Serial.println(F("default settings")); settingsChanged(); }
  else if (c == 'J' && has && v >= -500 && v <= 500) jog(v);
  else if (c == 'F' && v >= 0 && v <= 60000) feederTest(v < 1 ? 1 : (unsigned int)v);
  else if (c == 'C') feederTest(0);
  else if (c == 'R') rollerTurn();
  else Serial.println(F("unknown command or value out of range"));
}

void handleSerial() {
  if (!linkRead()) return;
  if (!linkFrame()) {
    if (isalpha(lineBuf[0]) && lineLen == 0) { Serial.print(F("ignored, send as @CMD*HH: ")); Serial.println(lineBuf); }
    return;
  }
  dispatch(lineBuf);
}

#include "tft.h"
#include "hmi.h"

void setup() {
  digitalWrite(PIN_RELAY, HIGH);         // relay off before the pin becomes an output
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_PUL, OUTPUT);
  pinMode(PIN_BUZZ, OUTPUT);
  pinMode(PIN_LIMIT, INPUT_PULLUP);
  pinMode(A0, INPUT_PULLUP); pinMode(A1, INPUT_PULLUP); pinMode(A2, INPUT_PULLUP); pinMode(A3, INPUT_PULLUP);
#ifdef __AVR__
  PCMSK2 |= _BV(PCINT20);                // D4 pin-change interrupt
  PCICR |= _BV(PCIE2);
#endif
  Serial.begin(115200);
  bool had = loadCfg();
  if (!had) { cfg = DEFAULTS; saveCfg(); }
  loadCount();
  resetSwitchClock();
  uiSetup();                             // screen on, start-up picture
  Serial.println(F("#B 5"));
  Serial.println(F("Strip cutter v5 ready"));
  if (!had) Serial.println(F("default settings"));
  showStatus();
  sayCount();
  state(ST_IDLE);
  if (cfg.autoStart) {
    Serial.println(F("starting by itself in 3 s"));
    Serial.println(F("#A 3000"));
    if (uiAutoStartWait()) runContinuous();
    else Serial.println(F("automatic start cancelled"));
  } else { delay(800); uiSplashEnd(); }
}

void loop() {
  handleSerial();
  pollSwitch();
  if ((char)swState != lastTop) { lastTop = swState; sayTop(swState); uiDirty(D_HEAD); }
  buzzTick();
  uiIdle();
}
