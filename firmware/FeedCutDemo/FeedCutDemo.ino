/*
  Strip Cutter v6 - FEED + CUT DEMO
  ---------------------------------
  Arduino Uno + TB6600 + NEMA23 feeder (as FeederDemo) + 12 V wiper motor (Magna PM-11G, 30 rpm) driving the knife
  lever through a crank and a link. One crank turn = one cut. A roller microswitch is pressed by the crank tip
  when the knife is fully OPEN ("park").

  CYCLE:  feed L mm (knife open)  ->  wiper ON  ->  switch releases (knife closing)  ->  switch presses again
          (knife open)  ->  wiper OFF  ->  short pause  ->  repeat.   About 2.6-3 s per piece at 30 rpm.
  The worm gearbox is self-locking, so the knife stays open when the motor stops.

  WIRING
    TB6600 PUL+ -> D5   PUL- -> GND        TB6600 DIR+ -> D6   DIR- -> GND        TB6600 ENA+ -> D7   ENA- -> GND
    TB6600 VCC/GND -> 12-24 V supply,  A+/A-, B+/B- -> motor coils   (same as FeederDemo)
    Relay module (5 V, 10 A):  VCC -> 5V,  GND -> GND,  IN -> D8
        12 V + -> [fuse 5 A] -> relay COM ;  relay NO -> wiper wire 1 ;  wiper wire 2 -> 12 V -
        Diode 1N5408 (or 1N4007) across the wiper wires: silver stripe to wire 1 (the + side)
    Park microswitch:  COM -> GND,  NO -> D9      (pressed = knife open)
    Push button (optional) between D11 and GND -> press = start / stop

  SERIAL MONITOR 115200 baud, "Newline". Commands:
    G   go (Q pieces, or forever if Q = 0)     X   stop after the current piece
    K   one cut only (no feed)                 H   home: run the crank until the knife is open
    L75 piece length mm      S200 feed speed mm/s      P300 pause after each cut ms     Q10 pieces (0 = forever)
    C17.44 steps per mm      J20 / J-5 jog the net (only with the knife open)          E0 / E1 stepper free / on
    R0 / R1 relay (wiper) off / on  - manual test, careful      W   show the switch state
    B40  run-on after the switch closes, ms (0..200) - fine-tunes where the crank stops
    T3000 cut timeout ms (a jam or stall stops everything)      ?   show settings
  Settings are stored in EEPROM.
*/
#include <EEPROM.h>

const uint8_t PIN_PUL = 5, PIN_DIR = 6, PIN_ENA = 7, PIN_RELAY = 8, PIN_PARK = 9, PIN_BTN = 11, PIN_LED = 13;
const bool    FEED_DIR_LEVEL = HIGH;          // change to LOW if the net goes backwards
const bool    RELAY_ACTIVE_LOW = true;        // most blue relay modules switch ON with IN = LOW; set false if yours is the other way
const float   START_SPEED = 20.0;             // mm/s
const float   ACCEL = 2500.0;                 // mm/s^2

struct Settings { uint16_t magic; float len, speed, spmm; uint16_t pauseMs, qty, runOnMs, cutTimeoutMs; };
Settings cfg;
const uint16_t MAGIC = 0xFC06;

bool running = false, stopReq = false;
uint16_t count = 0;
double targetSteps = 0; long doneSteps = 0;

void save() { EEPROM.put(0, cfg); }
void load() {
  EEPROM.get(0, cfg);
  if (cfg.magic != MAGIC || !(cfg.spmm > 1 && cfg.spmm < 100)) {
    Settings old; EEPROM.get(0, old);
    float spmm = 1600.0 / (PI * 29.2);
    if (old.magic == 0xFD03 && old.spmm > 1 && old.spmm < 100) spmm = old.spmm;   // keep the FeederDemo calibration
    cfg = {MAGIC, 75.0, 200.0, spmm, 300, 0, 40, 3000};
    save();
  }
}

// ---------------- wiper motor + park switch ----------------
void relay(bool on) { digitalWrite(PIN_RELAY, (on ^ RELAY_ACTIVE_LOW) ? HIGH : LOW); }
bool parkedRaw() { return digitalRead(PIN_PARK) == LOW; }
bool parked() {                                  // debounced: stable for 8 ms
  bool s = parkedRaw(); uint32_t t = millis();
  while (millis() - t < 8) { if (parkedRaw() != s) { s = parkedRaw(); t = millis(); } }
  return s;
}
bool waitSwitch(bool wantPressed, uint16_t timeoutMs) {
  uint32_t t0 = millis();
  while (millis() - t0 < timeoutMs) { if (parked() == wantPressed) return true; }
  return false;
}
void fault(const __FlashStringHelper *why) {
  relay(false); running = false;
  Serial.print(F("FAULT: ")); Serial.println(why);
  for (uint8_t i = 0; i < 10; i++) { digitalWrite(PIN_LED, i & 1); delay(120); }
  digitalWrite(PIN_LED, LOW);
}
bool home() {                                    // run until the knife is open
  if (parked()) return true;
  relay(true);
  bool ok = waitSwitch(true, cfg.cutTimeoutMs);
  delay(cfg.runOnMs); relay(false); delay(150);
  if (!ok) fault(F("no park signal while homing (switch position? motor turning?)"));
  return ok;
}
bool cutOnce() {
  if (!parked() && !home()) return false;
  relay(true);
  if (!waitSwitch(false, 1500)) { fault(F("switch never released - crank not turning, or switch stuck")); return false; }
  if (!waitSwitch(true, cfg.cutTimeoutMs)) { fault(F("knife did not come back open - jam or stall, check the net")); return false; }
  delay(cfg.runOnMs); relay(false);
  delay(150);                                    // let the motor stop before feeding
  return true;
}

// ---------------- feeder (as FeederDemo) ----------------
void motorOn(bool on) { digitalWrite(PIN_ENA, on ? LOW : HIGH); if (on) delay(5); }
void moveSteps(long n, float speedMm) {
  if (n == 0) return;
  bool fwd = n > 0; long total = fwd ? n : -n;
  digitalWrite(PIN_DIR, fwd ? FEED_DIR_LEVEL : !FEED_DIR_LEVEL);
  delayMicroseconds(10);
  const float v0 = START_SPEED * cfg.spmm, vmax = speedMm * cfg.spmm, a = ACCEL * cfg.spmm;
  uint32_t t = micros();
  for (long i = 0; i < total; i++) {
    long fromEnd = total - 1 - i; long r = i < fromEnd ? i : fromEnd;
    float v = sqrt(v0 * v0 + 2.0 * a * r); if (v > vmax) v = vmax;
    uint32_t period = (uint32_t)(1000000.0 / v);
    while ((uint32_t)(micros() - t) < period) { }
    t += period;
    digitalWrite(PIN_PUL, HIGH); delayMicroseconds(5); digitalWrite(PIN_PUL, LOW);
  }
}
bool feed(float mm) {                            // never feed into a closed knife
  if (!parked()) { fault(F("feed blocked: knife not open")); return false; }
  targetSteps += (double)mm * cfg.spmm;
  long want = lround(targetSteps);
  motorOn(true);
  moveSteps(want - doneSteps, cfg.speed);
  doneSteps = want;
  return true;
}

void status() {
  Serial.print(F("L=")); Serial.print(cfg.len, 1);
  Serial.print(F(" S=")); Serial.print(cfg.speed, 0);
  Serial.print(F(" P=")); Serial.print(cfg.pauseMs);
  Serial.print(F(" Q=")); Serial.print(cfg.qty);
  Serial.print(F(" C=")); Serial.print(cfg.spmm, 3);
  Serial.print(F(" B=")); Serial.print(cfg.runOnMs);
  Serial.print(F(" T=")); Serial.print(cfg.cutTimeoutMs);
  Serial.print(F(" knife=")); Serial.print(parked() ? F("OPEN") : F("not open"));
  Serial.print(F(" count=")); Serial.print(count);
  Serial.println(running ? F(" RUNNING") : F(" idle"));
}

void startRun() {
  running = true; stopReq = false; count = 0; targetSteps = 0; doneSteps = 0;
  digitalWrite(PIN_LED, HIGH); Serial.println(F("GO"));
  if (!home()) return;
}
void endRun(const __FlashStringHelper *why) { running = false; relay(false); digitalWrite(PIN_LED, LOW); Serial.print(why); Serial.print(F(" pieces=")); Serial.println(count); }

void serialCmd() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n'); s.trim();
  if (!s.length()) return;
  char c = toupper(s[0]); float v = s.substring(1).toFloat();
  switch (c) {
    case 'G': if (!running) startRun(); return;
    case 'X': stopReq = true; relay(false); if (!running) Serial.println(F("idle")); return;
    case 'K': if (!running) { Serial.println(cutOnce() ? F("cut ok") : F("cut failed")); } return;
    case 'H': if (!running) { Serial.println(home() ? F("knife open") : F("home failed")); } return;
    case 'W': Serial.println(parked() ? F("switch PRESSED (knife open)") : F("switch released")); return;
    case 'R': if (!running) { relay(v > 0.5); Serial.println(v > 0.5 ? F("wiper ON  (R0 to stop)") : F("wiper off")); } return;
    case 'L': if (v >= 5 && v <= 1000) cfg.len = v; break;
    case 'S': if (v >= 30 && v <= 400) cfg.speed = v; break;
    case 'P': if (v >= 0 && v <= 60000) cfg.pauseMs = (uint16_t)v; break;
    case 'Q': if (v >= 0 && v <= 60000) cfg.qty = (uint16_t)v; break;
    case 'C': if (v > 1 && v < 100) cfg.spmm = v; break;
    case 'B': if (v >= 0 && v <= 200) cfg.runOnMs = (uint16_t)v; break;
    case 'T': if (v >= 1500 && v <= 10000) cfg.cutTimeoutMs = (uint16_t)v; break;
    case 'J': if (!running) { if (parked()) { motorOn(true); moveSteps(lround(v * cfg.spmm), 40); } else Serial.println(F("knife not open - H first")); } break;
    case 'E': motorOn(v > 0.5); break;
    case '?': break;
    default: Serial.println(F("? unknown command")); return;
  }
  save(); status();
}

bool buttonPressed() {
  static uint32_t last = 0; static bool prev = HIGH;
  bool now = digitalRead(PIN_BTN);
  bool fired = (prev == HIGH && now == LOW && millis() - last > 250);
  if (now != prev) last = millis();
  prev = now;
  return fired;
}

void setup() {
  relay(false); pinMode(PIN_RELAY, OUTPUT); relay(false);
  pinMode(PIN_PUL, OUTPUT); pinMode(PIN_DIR, OUTPUT); pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_PARK, INPUT_PULLUP); pinMode(PIN_BTN, INPUT_PULLUP); pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200); Serial.setTimeout(30);
  load();
  motorOn(true);
  Serial.println(F("Feed + cut demo ready. H=home K=one cut G=go X=stop  L/S/P/Q/C/J/E/R/W/B/T ?"));
  status();
}

void loop() {
  serialCmd();
  if (buttonPressed()) { if (running) stopReq = true; else startRun(); }
  if (!running) return;
  if (stopReq) { endRun(F("STOPPED")); return; }
  if (!feed(cfg.len)) return;
  if (!cutOnce()) return;
  count++;
  Serial.print(F("piece ")); Serial.println(count);
  if (cfg.qty && count >= cfg.qty) { endRun(F("DONE")); return; }
  uint32_t t0 = millis();
  while (millis() - t0 < cfg.pauseMs) { serialCmd(); if (buttonPressed()) stopReq = true; }
}
