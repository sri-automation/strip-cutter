/*
  Strip cutter - CONTINUOUS mode (Arduino Uno), version 4, for the Strip Cutter Control panel on the PC

  The wiper motor runs all the time. The limit switch (pressed = knife at the top) is used as a
  clock: the program measures how long one turn takes and feeds the net once per turn, centred on
  the moment the knife is at the top. The knife then cuts on its way down.

  New in version 4
    - Faster feed: speed up to 2000 mm/s and an acceleration setting (A). The step pulses are timed
      from a schedule, so the Uno keeps up at the higher step rates.
    - Parks at the top: the motor is switched off a little BEFORE the knife reaches the top, it
      coasts up to it, and short nudges finish the move if it stopped short. The program learns how
      early to switch off (D) from every stop.
    - Settings are kept in the Arduino's memory (EEPROM) and come back after a power cut.
    - The piece count is kept too. It is no longer reset by Start: N0 resets it, N1234 sets it.
      Q is now the count to stop at (0 = no limit).
    - Length correction: the net fed per piece = U x length + V, to make up for slip.

  Pins (same as before)
    D2  -> TB6600 DIR+        D3 -> TB6600 PUL+        (DIR- and PUL- to GND)
    D9  <- limit switch between D9 and GND (pressed = knife at the top)
    D10 -> relay IN for the wiper motor: 0 V = motor ON

  Serial Monitor: 115200 baud, line ending "Newline"
    G      start continuous cutting
    while running, single keys:   X = stop at the top    + = feed 10 ms later    - = feed 10 ms earlier
    K      one cut, then park at the top        H     park the knife at the top
    W      watch the limit switch for 10 s      ?     show settings
    L70    piece length in mm                   Q500  stop when the count reaches 500 (0 = no limit)
    S1000  top feed speed in mm/s               A6000 feed acceleration in mm/s2
    O20    feed timing offset in ms             J20   jog the net 20 mm
    N0     reset the piece count                N1234 set the piece count
    U1.15  length correction factor             V-5.9 length correction offset in mm
    D60    switch the cutter off this many ms before the top when parking (learnt by itself)
    E25    length of one nudge in ms when parking
    Z      put all settings back to the defaults (the piece count stays)

  Feeder tests (the cutter motor stays OFF)
    F      feed one piece and stop         F5    feed 5 pieces, one after the other
    C      keep feeding piece after piece until you send X
    T2000  time from one test feed to the next, in ms
    R      turn the feed roller exactly one turn

  !      STOP NOW: cutter motor off at once, wherever the knife is (works at any time)

  At power-up it waits 3 s and then starts cutting by itself (AUTO_START). Send any key in
  those 3 s to cancel the automatic start. The control panel does this for you if you want.

  Lines that start with # are status reports for the control panel:
    #B version  #S state  #P pieces made  #F test feeds  #C settings  #O offset  #M cutter timing
    #T knife at top  #A auto start pending  #K park result
*/

#include <EEPROM.h>

// ---------------- fixed settings ----------------
const float STEPS_PER_MM = 17.44;   // 1600 steps/rev on a 29.2 mm roller (use U and V to correct the length)
const float START_SPEED  = 20.0;    // mm per second
const bool  FEED_DIR     = LOW;     // change to HIGH if the net runs backwards
const float OPEN_PART    = 0.30;    // part of one turn in which the knife is safely open for feeding (0.30 = 108 degrees)
const unsigned int LEAVE_TIMEOUT_MS = 2000;   // the switch must release within this time after the motor starts
const unsigned int CUT_TIMEOUT_MS   = 4000;   // one turn must not take longer than this
const bool  AUTO_START   = true;    // true = start by itself 3 s after power-up (any key in those 3 s cancels it)
const long  STEPS_PER_REV = 1600;   // TB6600 microstep setting: pulses for one turn of the stepper
const bool  LIMIT_PRESSED = LOW;    // switch connects pin 9 to GND when pressed
const byte  COUNT_SAVE_EVERY = 5;   // while running, the count is written to memory every 5 pieces (and at every stop)
const unsigned int SETTLE_MS = 300;        // after the cutter is switched off, time for it to come to rest
const unsigned int NUDGE_SETTLE_MS = 180;  // rest time after each nudge
const byte  MAX_NUDGES = 60;
const unsigned int PULSE_US = 8;    // width of one step pulse

// ---------------- settings kept in EEPROM ----------------
struct Cfg {
  float    pieceMm;    // L  piece length, mm
  uint32_t target;     // Q  stop when the count reaches this (0 = no limit)
  float    speed;      // S  top feed speed, mm/s
  float    accel;      // A  feed acceleration, mm/s2
  int16_t  offsetMs;   // O  feed timing: + = later, - = earlier
  uint16_t testMs;     // T  feeder test rhythm
  float    lenK;       // U  net fed = lenK x length + lenC
  float    lenC;       // V
  int16_t  leadMs;     // D  park: switch off this long before the knife reaches the top (learnt)
  uint16_t creepMs;    // E  park: one nudge
  int16_t  kLagMs;     // extra time the first turn from rest takes (the motor speeding up)
  uint16_t turnMs;     // learnt: time of one turn
  uint16_t gapMs;      // learnt: time from the knife leaving the top to it arriving at the top again
};
// The length correction starts from your measurements with version 3: 70 -> 66 mm and 60 -> 57.3 mm.
const Cfg DEFAULTS = { 70.0, 0, 1000.0, 6000.0, 20, 2000, 1.1494, -5.86, 60, 25, 30, 0, 0 };
Cfg cfg;

const uint16_t MAGIC = 0x5C04;
const int CFG_ADDR = 0;              // magic (2 bytes), settings, check byte
const int CNT_ADDR = 128;            // piece count: a ring of slots so no cell wears out
const byte CNT_SLOTS = 64;
struct CntSlot { uint32_t count; uint32_t seq; byte crc; byte mark; };

// ---------------- pins ----------------
const byte PIN_DIR = 2, PIN_PUL = 3, PIN_LIMIT = 9, PIN_RELAY = 10, PIN_LED = 13;
#ifdef __AVR__
  #define PUL_HIGH()  (PORTD |= _BV(3))          // D3, fast
  #define PUL_LOW()   (PORTD &= ~_BV(3))
  #define LIMIT_RAW() ((PINB & _BV(1)) ? HIGH : LOW)   // D9, fast
#else
  #define PUL_HIGH()  digitalWrite(PIN_PUL, HIGH)
  #define PUL_LOW()   digitalWrite(PIN_PUL, LOW)
  #define LIMIT_RAW() digitalRead(PIN_LIMIT)
#endif

bool running = false, stopAsked = false, abortAsked = false;
void quickKeys();
void abortNow();
uint32_t made = 0;            // pieces made, kept in EEPROM
uint32_t savedMade = 0, cntSeq = 0;
int cntSlot = -1;
unsigned int testMade = 0;
double wantSteps = 0;
long doneSteps = 0;

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
         c.lenC >= -50 && c.lenC <= 50 && c.leadMs >= -100 && c.leadMs <= 400 && c.creepMs >= 5 && c.creepMs <= 100 &&
         c.kLagMs >= -100 && c.kLagMs <= 300;
}

bool loadCfg() {
  uint16_t m; EEPROM.get(CFG_ADDR, m);
  if (m != MAGIC) return false;
  Cfg c; EEPROM.get(CFG_ADDR + 2, c);
  if (EEPROM.read(CFG_ADDR + 2 + sizeof(Cfg)) != crc8((const byte *)&c, sizeof(Cfg)) || !cfgSane(c)) return false;
  cfg = c;
  return true;
}

void loadCount() {
  bool found = false;
  for (byte i = 0; i < CNT_SLOTS; i++) {
    CntSlot s; EEPROM.get(CNT_ADDR + i * (int)sizeof(CntSlot), s);
    if (s.mark != 0xA5 || s.crc != crc8((const byte *)&s, 8)) continue;
    if (!found || (long)(s.seq - cntSeq) > 0) { found = true; cntSeq = s.seq; made = s.count; cntSlot = i; }
  }
  if (!found) { made = 0; cntSeq = 0; cntSlot = -1; }
  savedMade = made;
}

void saveCount() {                       // next slot in the ring, highest sequence number wins at power-up
  if (made == savedMade && cntSlot >= 0) return;
  cntSlot = (cntSlot + 1) % CNT_SLOTS;
  cntSeq++;
  CntSlot s = { made, cntSeq, 0, 0xA5 };
  s.crc = crc8((const byte *)&s, 8);
  EEPROM.put(CNT_ADDR + cntSlot * (int)sizeof(CntSlot), s);
  savedMade = made;
}

void sayCount() { Serial.print(F("#P ")); Serial.println(made); }

// ---------------- wiper motor ----------------
void motor(bool on) { digitalWrite(PIN_RELAY, on ? LOW : HIGH); }   // relay is ON at 0 V

void state(const __FlashStringHelper *s) { Serial.print(F("#S ")); Serial.println(s); }   // for the control panel

void fault(const __FlashStringHelper *why) {
  motor(false);
  running = false;
  saveCount();
  Serial.print(F("STOPPED: "));
  Serial.println(why);
  state(F("FAULT"));
  for (byte i = 0; i < 10; i++) { digitalWrite(PIN_LED, i & 1); delay(120); }
  digitalWrite(PIN_LED, LOW);
}

// ---------------- limit switch as a clock (never waits, call it very often) ----------------
bool swRaw = false, swState = false;
unsigned long swChangeUs = 0;      // when the raw level last changed
unsigned long tPressUs = 0;        // when the switch was last pressed
unsigned long tReleaseUs = 0;      // when it was last released
unsigned long periodUs = 0;        // time of one turn (press to press)
unsigned long pressedUs = 0;       // how long the switch stays pressed each turn
unsigned int  pressCount = 0;      // presses seen
unsigned int  releaseCount = 0;    // releases seen

void pollSwitch() {
  bool raw = LIMIT_RAW() == LIMIT_PRESSED;
  unsigned long now = micros();
  if (raw != swRaw) { swRaw = raw; swChangeUs = now; return; }
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
  swRaw = swState = (digitalRead(PIN_LIMIT) == LIMIT_PRESSED);
  swChangeUs = micros();
  pressCount = 0; releaseCount = 0; periodUs = 0; pressedUs = 0;
}

void watchFor(unsigned long ms) {        // let time pass while watching the switch and the keys
  unsigned long t0 = millis();
  while (millis() - t0 < ms) { pollSwitch(); quickKeys(); if (abortAsked) return; }
}

bool waitPresses(unsigned int target, unsigned long timeoutMs) {
  unsigned long t0 = millis();
  while (pressCount < target) {
    pollSwitch();
    quickKeys();
    if (abortAsked) return false;
    if (millis() - t0 > timeoutMs) return false;
  }
  return true;
}

bool atTop() {                           // simple steady read, used only when idle
  bool s = digitalRead(PIN_LIMIT) == LIMIT_PRESSED;
  unsigned long t = millis();
  while (millis() - t < 10) {
    bool n = digitalRead(PIN_LIMIT) == LIMIT_PRESSED;
    if (n != s) { s = n; t = millis(); }
  }
  return s;
}

// ---------------- parking at the top ----------------
// The cutter is running at speed. predPress = when the switch is expected to be pressed next (micros),
// skip = presses that will come before that one. The motor is switched off D ms before predPress,
// the knife coasts, and if it stops short, short nudges bring it onto the switch.
// Result: 0 = coasted onto the switch, 1 = reached it with nudges, 2 = went past the top, 3 = stopped by ! or no switch
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
    if (pressCount - p0 > skip) { lastEarly = true; break; }         // the top came sooner than expected
    if (millis() - t0 > 2UL * CUT_TIMEOUT_MS) { motor(false); return 3; }
  }
  motor(false);
  unsigned long tOff = micros();
  unsigned int pOff = pressCount, rOff = releaseCount;
  watchFor(SETTLE_MS);
  if (abortAsked) return 3;
  // what happened while it coasted, for the log
  Serial.print(F("park: cutter off ")); Serial.print((long)(predPress - tOff) / 1000L); Serial.print(F(" ms before the expected top"));
  if (lastEarly) Serial.print(F(" (the top came early)"));
  else if (pressCount != pOff) {
    Serial.print(F(", reached the switch ")); Serial.print((tPressUs - tOff) / 1000UL); Serial.print(F(" ms later"));
    if (releaseCount != rOff) { Serial.print(F(" and left it again after ")); Serial.print((tReleaseUs - tPressUs) / 1000UL); Serial.print(F(" ms")); }
  } else if (!swState) Serial.print(F(", stopped short of the switch"));
  Serial.println();
  if (swState) {                                   // on the switch: at the top, if it has really stopped there
    watchFor(200);
    if (swState) return 0;
    return 2;                                      // still creeping on, and off the switch again
  }
  if (pressCount - p0 > skip) return 2;            // pressed and released again: went past the top
  // stopped short of the top: nudge it up
  unsigned int on = cfg.creepMs;
  for (nudges = 1; nudges <= MAX_NUDGES; nudges++) {
    unsigned int p1 = pressCount;
    motor(true);
    watchFor(on);
    motor(false);
    watchFor(NUDGE_SETTLE_MS);
    if (abortAsked) return 3;
    if (swState) { watchFor(200); if (swState) return 1; }
    if (pressCount != p1) {                        // one nudge went right over the top: make the nudges shorter
      cfg.creepMs = cfg.creepMs * 2 / 3 < 5 ? 5 : cfg.creepMs * 2 / 3;
      nudgeOver = true;
      Serial.print(F("park: a nudge went over the top, nudges now ")); Serial.print(cfg.creepMs); Serial.println(F(" ms"));
      return 2;
    }
    if (nudges % 6 == 0 && on < 60) on += 5;       // hardly moving: a little longer each time
  }
  return 3;
}

// Learn from one stop: v = how long before the top the cutter is switched off (the lead D).
// Went past the top: switch off earlier (more if it keeps happening). Needed several nudges: a little later.
byte overRun = 0;                                  // stops in a row that coasted past the top
void learnFrom(byte r) {
  int d = 0;
  if (r == 2 && !nudgeOver) { if (overRun < 4) overRun++; } else overRun = 0;
  if (r == 0 && lastEarly) d = 5;                  // got there before the switch-off: a bit earlier
  else if (r == 2 && !nudgeOver) d = 25 * overRun; // coasted past the top: clearly earlier
  else if (r == 2 && nudgeOver) d = -5;            // stopped short, but so close that a nudge went over: a bit later
  else if (r == 1 && nudges >= 2) { d = -4 * (nudges - 1); if (d < -15) d = -15; }   // stopped short: a bit later
  int n = cfg.leadMs + d;
  cfg.leadMs = n < -100 ? -100 : (n > 400 ? 400 : n);
}

// wait, with the motor on, for the switch to be pressed (press = true) or released
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

// The motor is on, the knife anywhere. Let it come round to the top and leave it again (that edge is
// a clean time mark at full speed), then park on the next top. Learns the turn time first if needed.
byte parkViaRelease() {
  if (!swState && !waitEdge(true)) { motor(false); return 3; }   // up to the top...
  if (!waitEdge(false)) { motor(false); return 3; }                // ...and past it
  unsigned long tRel = tReleaseUs;
  if (!cfg.gapMs) {                                                // learn: leaving the top -> reaching it again
    if (!waitEdge(true)) { motor(false); return 3; }
    cfg.gapMs = (tPressUs - tRel) / 1000UL;
    cfg.turnMs = (tPressUs - tRel) / 1000UL + pressedUs / 1000UL;
    Serial.print(F("park: one turn takes about ")); Serial.print(cfg.turnMs); Serial.println(F(" ms"));
    if (!waitEdge(false)) { motor(false); return 3; }
    tRel = tReleaseUs;
  }
  byte r = coastToTop(tRel + (unsigned long)cfg.gapMs * 1000UL, 0);
  learnFrom(r);
  return r;
}

// After going past the top: round again at full speed and park on the following top, learning as it goes.
byte parkFinish(byte r) {
  byte tries = 0;
  while (r == 2 && tries < 6) {
    tries++;
    Serial.print(F("went past the top, going round once more (switch-off lead now ")); Serial.print(cfg.leadMs); Serial.println(F(" ms)"));
    motor(true);
    r = parkViaRelease();
  }
  return r;
}

void parkReport(byte r) {
  Serial.print(F("#K ")); Serial.print(r); Serial.print(' '); Serial.print(nudges);
  Serial.print(' '); Serial.println(cfg.leadMs);
  if (r <= 1) {
    Serial.print(F("parked at the top"));
    if (r == 1) { Serial.print(F(" after ")); Serial.print(nudges); Serial.print(F(" nudge(s)")); }
    Serial.print(F(", switch-off lead now ")); Serial.print(cfg.leadMs); Serial.println(F(" ms"));
  }
  saveCfg();                             // keeps what was learnt (only changed bytes are written)
}

void parkFault() {
  if (nudgeOver) fault(F("could not park the knife at the top: even the shortest nudge carries it past the switch (the cutter coasts too far)"));
  else fault(F("could not park the knife at the top. Try a larger 'switch off before the top' (D) in the app"));
}

// Park from a run: the knife is turning steadily, last press at tPressUs, one turn = periodUs
byte parkFromRun() {
  unsigned long T = periodUs ? periodUs : (unsigned long)cfg.turnMs * 1000UL;
  unsigned long next = tPressUs + T;
  byte skip = 0;
  if ((long)(next - micros()) < (long)cfg.leadMs * 1000L + 20000L) { next += T; skip = 1; }   // too late for this top: take the next one
  byte r = coastToTop(next, skip);
  learnFrom(r);
  r = parkFinish(r);
  parkReport(r);
  return r;
}

// Park from rest: K (one cut) or H (just go to the top)
bool parkFromRest(bool oneCut) {
  abortAsked = false; stopAsked = false;
  resetSwitchClock();
  if (swState && !oneCut) { Serial.println(F("the knife is already at the top")); return true; }
  byte r;
  motor(true);
  if (swState) {                         // at the top: leave it, then come round once
    if (!waitEdge(false)) {
      motor(false);
      if (abortAsked) abortNow(); else fault(F("limit switch stays pressed with the motor on (motor not turning, or switch wiring)"));
      return false;
    }
    if (cfg.gapMs) {                     // one turn from here; the motor was speeding up at the start, hence the small lag
      r = coastToTop(tReleaseUs + (unsigned long)cfg.gapMs * 1000UL + (long)cfg.kLagMs * 1000L, 0);
      learnFrom(r);
    } else r = parkViaRelease();         // turn time not known yet: one more turn to measure it
  } else {                               // somewhere on the way: round through the top once, then park
    r = parkViaRelease();
  }
  if (r == 3 && !abortAsked) { fault(F("the knife did not reach the top (limit switch never pressed)")); return false; }
  r = parkFinish(r);
  if (abortAsked) { abortNow(); return false; }
  parkReport(r);
  if (r > 1) { parkFault(); return false; }
  return true;
}

// ---------------- stepper feed ----------------
float feedLen(float mm) { float f = mm * cfg.lenK + cfg.lenC; return f < 1.0 ? 1.0 : f; }   // net to feed for a piece

float feedSeconds(float mm) {            // how long a feed of this length takes
  float n = mm * STEPS_PER_MM, v0 = START_SPEED * STEPS_PER_MM, vm = cfg.speed * STEPS_PER_MM, a = cfg.accel * STEPS_PER_MM;
  if (vm < v0) vm = v0;
  float r = (vm * vm - v0 * v0) / (2.0 * a);           // steps needed to reach full speed
  if (2.0 * r >= n) { float vp = sqrt(v0 * v0 + a * n); return 2.0 * (vp - v0) / a; }
  return 2.0 * (vm - v0) / a + (n - 2.0 * r) / vm;
}

#ifdef __AVR__
// Step pulses come from Timer1: its interrupt makes each pulse exactly on time, and the main loop
// keeps working out the speed for the next pulses from how far the net has gone:
//   speed = sqrt(v0^2 + 2 a x), x = steps from the nearer end of the move, never above the top speed.
volatile long isrLeft = 0, isrDone = 0;
volatile uint16_t isrNext = 0;            // timer ticks (0.5 us) until the next pulse

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
  TCCR1B = _BV(WGM12) | _BV(CS11);        // CTC mode, 16 MHz / 8 = 0.5 us ticks
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
    pollSwitch();                                      // keep watching the switch while feeding
  }
  TCCR1B = 0;
  TIMSK1 &= ~_BV(OCIE1A);
}

#else
// Test bench on the PC: the same speed profile, timed by the loop.
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
  wantSteps += (double)mm * STEPS_PER_MM;              // keeps the rounding error from adding up
  long target = lround(wantSteps);
  moveSteps(target - doneSteps);
  doneSteps = target;
}

// ---------------- continuous run ----------------
void quickKeys() {                       // single keys while running; never waits
  while (Serial.available()) {
    char c = toupper(Serial.read());
    if (c == 'X') { stopAsked = true; Serial.println(F("stopping")); }
    else if (c == '!') { abortAsked = true; stopAsked = true; motor(false); }      // STOP NOW
    else if (c == '+') { cfg.offsetMs += 10; Serial.print(F("#O ")); Serial.println(cfg.offsetMs); }
    else if (c == '-') { cfg.offsetMs -= 10; Serial.print(F("#O ")); Serial.println(cfg.offsetMs); }
  }
}

void abortNow() {                        // after STOP NOW: everything off, knife stays where it is
  motor(false);
  running = false;
  digitalWrite(PIN_LED, LOW);
  saveCount();
  saveCfg();
  Serial.print(F("STOPPED NOW by request. Pieces made: ")); Serial.println(made);
  Serial.println(F("The knife may not be at the top: send H to park it before feeding."));
  state(F("IDLE"));
}

void finishRun() {
  running = false;
  digitalWrite(PIN_LED, LOW);
  saveCount();
  saveCfg();
  Serial.print(F("DONE, pieces made: ")); Serial.println(made);
  state(F("IDLE"));
}

bool targetReached() { return cfg.target > 0 && made >= cfg.target; }

void stopRun() {                         // park at the top, then report
  state(F("PARK"));
  byte r = parkFromRun();
  if (abortAsked) { abortNow(); return; }
  if (r > 1) { parkFault(); return; }
  finishRun();
}

void runContinuous() {
  wantSteps = 0; doneSteps = 0; stopAsked = false; abortAsked = false;
  if (targetReached()) {
    Serial.print(F("NOT STARTED: the count has reached the target of ")); Serial.print(cfg.target);
    Serial.println(F(" pieces. Reset the count (N0) or raise the target (Q)."));
    state(F("IDLE"));
    return;
  }
  Serial.println(F("GO continuous - measuring the cutter for 3 turns, no feeding yet"));
  state(F("MEASURE"));
  sayCount();
  resetSwitchClock();
  motor(true);
  if (!waitPresses(1, (unsigned long)LEAVE_TIMEOUT_MS + CUT_TIMEOUT_MS) || !waitPresses(3, 2UL * CUT_TIMEOUT_MS)) {
    if (abortAsked) abortNow();
    else fault(F("no limit switch signal while the motor runs (motor not turning, or switch wiring)"));
    return;
  }
  const unsigned long T0 = periodUs;                   // time of one turn at the start
  float fl = feedLen(cfg.pieceMm);
  unsigned long feedUs = (unsigned long)(feedSeconds(fl) * 1000000.0);
  unsigned long openUs = (unsigned long)(OPEN_PART * T0);
  cfg.turnMs = T0 / 1000UL;                            // remembered for parking (saved at the end of the run)
  cfg.gapMs = (T0 - pressedUs) / 1000UL;
  Serial.print(F("one turn ")); Serial.print(T0 / 1000);
  Serial.print(F(" ms, switch pressed ")); Serial.print(pressedUs / 1000);
  Serial.print(F(" ms, feed of ")); Serial.print(fl, 1);
  Serial.print(F(" mm takes ")); Serial.print(feedUs / 1000);
  Serial.print(F(" ms, knife safely open ")); Serial.print(openUs / 1000); Serial.println(F(" ms"));
  Serial.print(F("#M ")); Serial.print(T0 / 1000); Serial.print(' '); Serial.print(pressedUs / 1000); Serial.print(' ');
  Serial.print(feedUs / 1000); Serial.print(' '); Serial.println(openUs / 1000);
  if (feedUs > openUs) {
    Serial.println(F("NOT STARTED: the feed takes longer than the knife is open. Raise the acceleration (A) or the speed (S), or use a shorter piece (L)."));
    stopRun();
    return;
  }
  long spare = (long)(openUs / 2) - (long)(feedUs / 2) - labs((long)cfg.offsetMs * 1000L);   // time to spare on the tight side
  if (spare < 0) {
    Serial.print(F("NOTE: with the offset of ")); Serial.print(cfg.offsetMs); Serial.print(F(" ms the feed "));
    Serial.print(cfg.offsetMs > 0 ? F("ends ") : F("starts ")); Serial.print(-spare / 1000);
    Serial.println(cfg.offsetMs > 0 ? F(" ms after the knife starts to close: make the offset smaller (-)") : F(" ms before the knife is open: make the offset larger (+)"));
  }
  if (stopAsked) { stopRun(); return; }               // stop was asked while measuring
  running = true;
  digitalWrite(PIN_LED, HIGH);
  state(F("RUN"));
  byte missed = 0;
  bool firstFeed = true, savePending = false;

  while (true) {
    if (stopAsked || targetReached()) break;           // just after a top: a whole turn to park in
    unsigned int edge = pressCount;
    unsigned long T = periodUs;
    if (T > T0 + T0 / 2 || T < T0 / 2) { fault(F("the cutter speed changed a lot (jam, or switch bouncing)")); return; }

    // next top = last press + half the pressed time + one turn. Start so the feed is centred on it.
    unsigned long startUs = tPressUs + pressedUs / 2 + T - feedUs / 2 + (long)cfg.offsetMs * 1000L;
    while ((long)(micros() - startUs) < 0) {
      pollSwitch();
      quickKeys();
      if (abortAsked) { abortNow(); return; }
      if (stopAsked) break;                            // park at the coming top (or the one after)
      if (micros() - tPressUs > T + T / 2) { fault(F("no limit switch signal for too long (cutter stalled?)")); return; }
      if (savePending && micros() - tPressUs > T / 2 && (long)(startUs - micros()) > 60000L) { saveCount(); savePending = false; }   // mid-turn, nothing to time
    }
    if (stopAsked) break;
    if (pressCount != edge) {                          // knife got to the top before the feed could start: skip this turn
      if (++missed > 3) { fault(F("feed timing lost (offset too large?)")); return; }
      continue;
    }
    missed = 0;

    unsigned long f0 = micros();
    feed(fl);                                          // the knife passes the top during this feed
    unsigned long took = micros() - f0;
    made++;
    sayCount();
    if (made - savedMade >= COUNT_SAVE_EVERY) savePending = true;
    if (firstFeed) {                                   // report the real feed time once
      firstFeed = false;
      Serial.print(F("#M ")); Serial.print(T0 / 1000); Serial.print(' '); Serial.print(pressedUs / 1000); Serial.print(' ');
      Serial.print(feedUs / 1000); Serial.print(' '); Serial.print(openUs / 1000); Serial.print(' '); Serial.println(took / 1000);
    }

    unsigned long w0 = millis();                       // the switch must have been pressed during or right after the feed
    while (pressCount == edge) {
      pollSwitch();
      quickKeys();
      if (abortAsked) { abortNow(); return; }
      if (millis() - w0 > T / 2000) { fault(F("limit switch not pressed after the feed (cutter stalled?)")); return; }
    }
  }
  running = false;
  stopRun();
}

// ---------------- feeder tests: the cutter motor stays off ----------------
// count = how many pieces to feed, 0 = keep going until X
void feederTest(unsigned int count) {
  motor(false);
  testMade = 0; wantSteps = 0; doneSteps = 0; stopAsked = false; abortAsked = false;
  if (!atTop()) Serial.println(F("NOTE: the knife is not at the top (limit switch not pressed). If it is closed the net will run into it. Send H first to park it."));
  float fl = feedLen(cfg.pieceMm);
  if (count == 0) Serial.println(F("FEEDER TEST, continuous - cutter OFF - send X to stop"));
  else { Serial.print(F("FEEDER TEST, pieces: ")); Serial.print(count); Serial.println(F(" - cutter OFF")); }
  state(F("FEEDTEST"));
  Serial.println(F("#F 0"));
  digitalWrite(PIN_LED, HIGH);
  while (true) {
    unsigned long t0 = millis();
    feed(fl);
    testMade++;
    Serial.print(F("#F ")); Serial.println(testMade);
    if (count > 0 && testMade >= count) break;
    while (millis() - t0 < cfg.testMs && !stopAsked) quickKeys();
    quickKeys();
    if (stopAsked) break;
  }
  digitalWrite(PIN_LED, LOW);
  Serial.print(F("feeder test done: ")); Serial.print(testMade);
  Serial.print(F(" pieces, ")); Serial.print(testMade * fl, 1); Serial.println(F(" mm of net fed"));
  state(F("IDLE"));
}

void rollerTurns(float turns) {
  motor(false);
  Serial.print(F("roller: ")); Serial.print(turns, 2); Serial.print(F(" turn(s) = "));
  long n = lround(turns * STEPS_PER_REV);
  Serial.print(n); Serial.print(F(" steps, should feed about ")); Serial.print(n / STEPS_PER_MM, 1); Serial.println(F(" mm"));
  state(F("JOG"));
  moveSteps(n);
  Serial.println(F("done. Measure the length that came out."));
  state(F("IDLE"));
}

// ---------------- commands ----------------
void showStatus() {
  float fl = feedLen(cfg.pieceMm);
  Serial.print(F("length ")); Serial.print(cfg.pieceMm, 1);
  Serial.print(F(" mm (feeds ")); Serial.print(fl, 1);
  Serial.print(F(" mm), stop at ")); Serial.print(cfg.target);
  Serial.print(F(", speed ")); Serial.print(cfg.speed, 0);
  Serial.print(F(" mm/s, accel ")); Serial.print(cfg.accel, 0);
  Serial.print(F(" mm/s2 (feed takes ")); Serial.print((unsigned long)(feedSeconds(fl) * 1000.0));
  Serial.print(F(" ms), offset ")); Serial.print(cfg.offsetMs);
  Serial.print(F(" ms, made ")); Serial.print(made);
  bool top = atTop();
  Serial.print(F(", limit switch ")); Serial.println(top ? F("PRESSED (knife at top)") : F("released"));
  // for the control panel: length, target, speed, offset, test rhythm, made, knife at top, steps per mm,
  // accel, length factor, length offset, park lead, nudge, one turn
  Serial.print(F("#C ")); Serial.print(cfg.pieceMm, 1); Serial.print(' '); Serial.print(cfg.target); Serial.print(' ');
  Serial.print(cfg.speed, 0); Serial.print(' '); Serial.print(cfg.offsetMs); Serial.print(' '); Serial.print(cfg.testMs); Serial.print(' ');
  Serial.print(made); Serial.print(' '); Serial.print(top ? 1 : 0); Serial.print(' '); Serial.print(STEPS_PER_MM, 2); Serial.print(' ');
  Serial.print(cfg.accel, 0); Serial.print(' '); Serial.print(cfg.lenK, 4); Serial.print(' '); Serial.print(cfg.lenC, 2); Serial.print(' ');
  Serial.print(cfg.leadMs); Serial.print(' '); Serial.print(cfg.creepMs); Serial.print(' '); Serial.println(cfg.turnMs);
}

void watchSwitch() {
  Serial.println(F("watching pin 9 for 10 s - press and release the switch by hand"));
  state(F("WATCH"));
  bool last = atTop();
  Serial.println(last ? F("PRESSED") : F("released"));
  Serial.print(F("#T ")); Serial.println(last ? 1 : 0);
  unsigned long t0 = millis();
  while (millis() - t0 < 10000) {
    bool s = atTop();
    if (s != last) { last = s; Serial.println(s ? F("PRESSED") : F("released")); Serial.print(F("#T ")); Serial.println(s ? 1 : 0); }
  }
  Serial.println(F("watch finished"));
  state(F("IDLE"));
}

void setAndSave() { saveCfg(); showStatus(); }

void handleSerial() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n');
  s.trim();
  if (s.length() == 0) return;
  char c = toupper(s[0]);
  float v = s.substring(1).toFloat();
  long n = s.substring(1).toInt();
  if (c == 'G') runContinuous();
  else if (c == '?') showStatus();
  else if (c == '!') { motor(false); Serial.println(F("cutter motor is off")); state(F("IDLE")); }
  else if (c == 'X') Serial.println(F("nothing is running"));
  else if (c == 'K') { state(F("CUT")); if (parkFromRest(true)) { Serial.println(F("cut done, knife at top")); state(F("IDLE")); } }
  else if (c == 'H') { state(F("PARK")); if (parkFromRest(false)) { Serial.println(F("knife at top")); state(F("IDLE")); } }
  else if (c == 'W') watchSwitch();
  else if (c == 'L' && v >= 5 && v <= 2000) { cfg.pieceMm = v; setAndSave(); }
  else if (c == 'Q' && n >= 0 && n <= 99999999L) { cfg.target = (uint32_t)n; setAndSave(); }
  else if (c == 'S' && v >= 30 && v <= 2000) { cfg.speed = v; setAndSave(); }
  else if (c == 'A' && v >= 500 && v <= 30000) { cfg.accel = v; setAndSave(); }
  else if (c == 'O' && v >= -500 && v <= 500) { cfg.offsetMs = (int)v; setAndSave(); }
  else if (c == 'T' && v >= 200 && v <= 60000) { cfg.testMs = (unsigned int)v; setAndSave(); }
  else if (c == 'U' && v >= 0.5 && v <= 1.5) { cfg.lenK = v; setAndSave(); }
  else if (c == 'V' && v >= -50 && v <= 50) { cfg.lenC = v; setAndSave(); }
  else if (c == 'D' && v >= -100 && v <= 400) { cfg.leadMs = (int)v; setAndSave(); }
  else if (c == 'E' && v >= 5 && v <= 100) { cfg.creepMs = (unsigned int)v; setAndSave(); }
  else if (c == 'N' && n >= 0 && n <= 99999999L && s.length() > 1) { made = (uint32_t)n; saveCount(); sayCount(); showStatus(); }
  else if (c == 'Z') { uint16_t tm = cfg.turnMs, gm = cfg.gapMs; cfg = DEFAULTS; cfg.turnMs = tm; cfg.gapMs = gm; Serial.println(F("settings back to the defaults")); setAndSave(); }
  else if (c == 'J' && v >= -500 && v <= 500) { state(F("JOG")); moveSteps(lround(v * STEPS_PER_MM)); state(F("IDLE")); }
  else if (c == 'F' && v >= 0 && v <= 60000) feederTest(v < 1 ? 1 : (unsigned int)v);
  else if (c == 'C') feederTest(0);
  else if (c == 'R' && v >= -20 && v <= 20) rollerTurns(v == 0 ? 1.0 : v);
  else Serial.println(F("commands: G K H W ? L Q S A O N U V D E Z J  feeder tests: F F5 C T R   (while running: X + - !)"));
}

void setup() {
  digitalWrite(PIN_RELAY, HIGH);         // set the level first so the relay does not click at power-up
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_PUL, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_LIMIT, INPUT_PULLUP);      // switch pulls the pin to GND when pressed
  Serial.begin(115200);
  Serial.setTimeout(50);
  bool had = loadCfg();
  if (!had) { cfg = DEFAULTS; saveCfg(); }
  loadCount();
  Serial.println(F("#B 4"));
  Serial.println(F("Strip cutter CONTINUOUS v4 ready. G = start, X = stop, F = feed one piece, H = park, ? = settings"));
  if (!had) Serial.println(F("first start of version 4: default settings written to memory"));
  showStatus();
  sayCount();
  state(F("IDLE"));
  if (AUTO_START) {
    Serial.println(F("starting by itself in 3 s - send any key to cancel"));
    Serial.println(F("#A 3000"));
    unsigned long t0 = millis();
    bool cancelled = false;
    while (millis() - t0 < 3000) {
      if (Serial.available()) { cancelled = true; break; }
    }
    if (cancelled) Serial.println(F("automatic start cancelled"));   // the key that cancelled it is then read as a normal command
    else runContinuous();
  }
}

void loop() {
  handleSerial();
  static unsigned long tLast = 0;        // when idle, tell the control panel when the knife-at-top switch changes
  static char lastTop = -1;
  if (millis() - tLast >= 150) {
    tLast = millis();
    char t = atTop() ? 1 : 0;
    if (t != lastTop) { lastTop = t; Serial.print(F("#T ")); Serial.println((int)t); }
  }
}
