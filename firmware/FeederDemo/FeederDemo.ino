/*
  Strip Cutter v3 - FEEDER DEMO (no cutter needed)
  -------------------------------------------------
  Arduino Uno + TB6600 + NEMA23 23HS5628, printed serrated drive roller (effective dia ~29.2 mm).
  Feeds a set length, pauses (where the knife would cut), repeats.

  WIRING
    TB6600 PUL+ -> D5     PUL- -> GND
    TB6600 DIR+ -> D6     DIR- -> GND
    TB6600 ENA+ -> D7     ENA- -> GND     (HIGH = motor free)
    TB6600 VCC/GND -> 12-24 V DC supply (3 A or more)
    TB6600 A+/A- , B+/B- -> motor coils (find pairs with a meter, ~0.9 ohm each pair)
    Push button (optional) between D11 and GND -> press = start / stop
    DIP switches: SW1 OFF, SW2 ON, SW3 OFF (8 microsteps = 1600 pulses/rev)
                  SW4 ON, SW5 OFF, SW6 OFF (about 2.0 A) - or follow the table printed on your driver

  SERIAL MONITOR 115200 baud, "Newline" line ending. Commands:
    G        go (runs Q pieces, or forever if Q = 0)      X   stop after the current piece
    L75      piece length in mm                            S200 feed speed mm/s (30..400)
    P1200    pause between pieces in ms                    Q10  number of pieces (0 = forever)
    J20      jog 20 mm forward   J-5 jog 5 mm back         C17.44  steps per mm (calibration)
    E0 / E1  motor off (free) / on                         ?    show settings
  Settings are stored in EEPROM.

  CALIBRATION: feed 10 pieces of L100, measure the average length A (after 1 min relax),
               new C = old C x 100 / A, send "C<new>".
*/
#include <EEPROM.h>

const uint8_t PIN_PUL = 5, PIN_DIR = 6, PIN_ENA = 7, PIN_BTN = 11, PIN_LED = 13;
const bool    FEED_DIR_LEVEL = HIGH;          // change to LOW if the net goes backwards
const float   START_SPEED = 20.0;             // mm/s
const float   ACCEL = 2500.0;                 // mm/s^2

struct Settings { uint16_t magic; float len, speed, spmm; uint16_t pauseMs, qty; };
Settings cfg;
const uint16_t MAGIC = 0xFD03;

bool running = false, stopReq = false;
uint16_t count = 0;
double targetSteps = 0; long doneSteps = 0;

void save() { EEPROM.put(0, cfg); }
void load() {
  EEPROM.get(0, cfg);
  if (cfg.magic != MAGIC || !(cfg.spmm > 1 && cfg.spmm < 100)) {
    cfg = {MAGIC, 75.0, 200.0, 1600.0 / (PI * 29.2), 1200, 0};
    save();
  }
}
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
void feed(float mm) {                           // accumulated target: no rounding drift over many pieces
  targetSteps += (double)mm * cfg.spmm;
  long want = lround(targetSteps);
  motorOn(true);
  moveSteps(want - doneSteps, cfg.speed);
  doneSteps = want;
}

void status() {
  Serial.print(F("L=")); Serial.print(cfg.len, 1);
  Serial.print(F(" S=")); Serial.print(cfg.speed, 0);
  Serial.print(F(" P=")); Serial.print(cfg.pauseMs);
  Serial.print(F(" Q=")); Serial.print(cfg.qty);
  Serial.print(F(" C=")); Serial.print(cfg.spmm, 3);
  Serial.print(F(" count=")); Serial.print(count);
  Serial.println(running ? F(" RUNNING") : F(" idle"));
}

void startRun() { running = true; stopReq = false; count = 0; targetSteps = 0; doneSteps = 0; digitalWrite(PIN_LED, HIGH); Serial.println(F("GO")); }
void endRun(const __FlashStringHelper *why) { running = false; digitalWrite(PIN_LED, LOW); Serial.print(why); Serial.print(F(" pieces=")); Serial.println(count); }

void serialCmd() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n'); s.trim();
  if (!s.length()) return;
  char c = toupper(s[0]); float v = s.substring(1).toFloat();
  switch (c) {
    case 'G': if (!running) startRun(); return;
    case 'X': stopReq = true; if (!running) Serial.println(F("idle")); return;
    case 'L': if (v >= 5 && v <= 1000) cfg.len = v; break;
    case 'S': if (v >= 30 && v <= 400) cfg.speed = v; break;
    case 'P': if (v >= 0 && v <= 60000) cfg.pauseMs = (uint16_t)v; break;
    case 'Q': if (v >= 0 && v <= 60000) cfg.qty = (uint16_t)v; break;
    case 'C': if (v > 1 && v < 100) cfg.spmm = v; break;
    case 'J': if (!running) { motorOn(true); moveSteps(lround(v * cfg.spmm), 40); } break;
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
  pinMode(PIN_PUL, OUTPUT); pinMode(PIN_DIR, OUTPUT); pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_BTN, INPUT_PULLUP); pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200); Serial.setTimeout(30);
  load();
  motorOn(true);
  Serial.println(F("Feeder demo ready. G=go X=stop L/S/P/Q/C/J/E ?"));
  status();
}

void loop() {
  serialCmd();
  if (buttonPressed()) { if (running) stopReq = true; else startRun(); }
  if (!running) return;
  if (stopReq) { endRun(F("STOPPED")); return; }
  feed(cfg.len);
  count++;
  Serial.print(F("piece ")); Serial.println(count);
  if (cfg.qty && count >= cfg.qty) { endRun(F("DONE")); return; }
  uint32_t t0 = millis();                         // pause = where the knife cuts
  while (millis() - t0 < cfg.pauseMs) { serialCmd(); if (buttonPressed()) stopReq = true; }
}
