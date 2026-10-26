/*
  Strip cutter - CONTINUOUS mode (Arduino Uno)

  The wiper motor runs all the time. The limit switch (pressed = knife at the top) is used as a
  clock: the program measures how long one turn takes, and each turn it feeds the net so that the
  feed is centred on the moment the knife is at the top. The knife then cuts on its way down.
  No stopping between pieces, so one piece per turn of the cutter (about 30 per minute).

  It refuses to start if the feed would take longer than the time the knife is safely open,
  and it stops everything if the cutter slows down a lot or the switch signal is lost.

  Pins (same as before)
    D2  -> TB6600 DIR+        D3 -> TB6600 PUL+        (DIR- and PUL- to GND)
    D9  <- limit switch between D9 and GND (pressed = knife at the top)
    D10 -> relay IN for the wiper motor: 0 V = motor ON

  Serial Monitor: 115200 baud, line ending "Newline"
    G      start continuous cutting
    while running, single keys:   X = stop at the top    + = feed 10 ms later    - = feed 10 ms earlier
    K      one cut only (no feed)          W     watch the limit switch for 10 s
    L75    piece length in mm              Q100  number of pieces (0 = keep going)
    S250   feed speed in mm/s              O20   feed timing offset in ms (same as + and -)
    J20    jog the net 20 mm               ?     show settings
*/

// ---------------- settings you may change ----------------
float PIECE_MM      = 75.0;     // piece length, mm
unsigned int PIECES = 0;        // how many pieces per run (0 = until you send X)
float FEED_SPEED    = 200.0;    // mm per second
int   OFFSET_MS     = 0;        // feed timing: + = later, - = earlier
const float STEPS_PER_MM = 17.44;   // 1600 steps/rev on a 29.2 mm roller; use your calibrated value if you have one
const float START_SPEED  = 20.0;    // mm per second
const float ACCEL        = 2500.0;  // mm per second squared
const bool  FEED_DIR     = LOW;     // change to HIGH if the net runs backwards
const float OPEN_PART    = 0.30;    // part of one turn in which the knife is safely open for feeding (0.30 = 108 degrees)
const unsigned int RUN_ON_MS        = 40;     // motor stays on this long after the switch is pressed when stopping
const unsigned int LEAVE_TIMEOUT_MS = 2000;   // the switch must release within this time after the motor starts
const unsigned int CUT_TIMEOUT_MS   = 4000;   // one turn must not take longer than this
const bool  AUTO_START   = false;   // true = start by itself 3 s after power-up
const bool  LIMIT_PRESSED = LOW;    // switch connects pin 9 to GND when pressed

// ---------------- pins ----------------
const byte PIN_DIR = 2, PIN_PUL = 3, PIN_LIMIT = 9, PIN_RELAY = 10, PIN_LED = 13;

bool running = false, stopAsked = false;
unsigned int made = 0;
double wantSteps = 0;
long doneSteps = 0;

// ---------------- wiper motor ----------------
void motor(bool on) { digitalWrite(PIN_RELAY, on ? LOW : HIGH); }   // relay is ON at 0 V

void fault(const __FlashStringHelper *why) {
  motor(false);
  running = false;
  Serial.print(F("STOPPED: "));
  Serial.println(why);
  for (byte i = 0; i < 10; i++) { digitalWrite(PIN_LED, i & 1); delay(120); }
  digitalWrite(PIN_LED, LOW);
}

// ---------------- limit switch as a clock (never waits, call it very often) ----------------
bool swRaw = false, swState = false;
unsigned long swChangeUs = 0;      // when the raw level last changed
unsigned long tPressUs = 0;        // when the switch was last pressed
unsigned long periodUs = 0;        // time of one turn (press to press)
unsigned long pressedUs = 0;       // how long the switch stays pressed each turn
unsigned int  pressCount = 0;      // number of presses seen

void pollSwitch() {
  bool raw = digitalRead(PIN_LIMIT) == LIMIT_PRESSED;
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
    }
  }
}

void resetSwitchClock() {
  swRaw = swState = (digitalRead(PIN_LIMIT) == LIMIT_PRESSED);
  swChangeUs = micros();
  pressCount = 0; periodUs = 0; pressedUs = 0;
}

bool waitPresses(unsigned int target, unsigned long timeoutMs) {
  unsigned long t0 = millis();
  while (pressCount < target) {
    pollSwitch();
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

// The motor is running: switch it off the next time the knife arrives at the top.
bool stopAtTop() {
  unsigned int c = pressCount;
  unsigned long t0 = millis();
  bool ok = true;
  while (pressCount == c) {
    pollSwitch();
    if (millis() - t0 > CUT_TIMEOUT_MS) { ok = false; break; }
  }
  if (ok) delay(RUN_ON_MS);
  motor(false);
  return ok;
}

bool cutToTop() {                        // one single cut, motor stops at the top
  resetSwitchClock();
  motor(true);
  if (swState) {                         // already at the top: it must leave first
    unsigned long t0 = millis();
    while (swState) {
      pollSwitch();
      if (millis() - t0 > LEAVE_TIMEOUT_MS) { fault(F("limit switch stays pressed with the motor on (motor not turning, or switch wiring)")); return false; }
    }
  }
  if (!stopAtTop()) { fault(F("the knife did not reach the top (limit switch never pressed)")); return false; }
  delay(150);
  return true;
}

// ---------------- stepper feed ----------------
float feedSeconds(float mm) {            // how long a feed of this length takes
  float n = mm * STEPS_PER_MM, v0 = START_SPEED * STEPS_PER_MM, vm = FEED_SPEED * STEPS_PER_MM, a = ACCEL * STEPS_PER_MM;
  if (vm < v0) vm = v0;
  float r = (vm * vm - v0 * v0) / (2.0 * a);           // steps needed to reach full speed
  if (2.0 * r >= n) { float vp = sqrt(v0 * v0 + a * n); return 2.0 * (vp - v0) / a; }
  return 2.0 * (vm - v0) / a + (n - 2.0 * r) / vm;
}

void moveSteps(long n) {
  if (n == 0) return;
  bool fwd = n > 0;
  long total = fwd ? n : -n;
  digitalWrite(PIN_DIR, fwd ? FEED_DIR : !FEED_DIR);
  delayMicroseconds(20);
  float v0 = START_SPEED * STEPS_PER_MM, vmax = FEED_SPEED * STEPS_PER_MM, a = ACCEL * STEPS_PER_MM;
  if (vmax < v0) vmax = v0;
  unsigned long t = micros();
  for (long i = 0; i < total; i++) {
    long fromEnd = total - 1 - i;
    long r = i < fromEnd ? i : fromEnd;                // ramp up, then ramp down
    float v = sqrt(v0 * v0 + 2.0 * a * r);
    if (v > vmax) v = vmax;
    unsigned long period = (unsigned long)(1000000.0 / v);
    while ((unsigned long)(micros() - t) < period) pollSwitch();   // keep watching the switch while feeding
    t += period;
    digitalWrite(PIN_PUL, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_PUL, LOW);
  }
}

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
    if (c == 'X') { stopAsked = true; Serial.println(F("stopping at the top")); }
    else if (c == '+') { OFFSET_MS += 10; Serial.print(F("offset ")); Serial.println(OFFSET_MS); }
    else if (c == '-') { OFFSET_MS -= 10; Serial.print(F("offset ")); Serial.println(OFFSET_MS); }
  }
}

void finishRun() {
  running = false;
  digitalWrite(PIN_LED, LOW);
  Serial.print(F("DONE, pieces made: ")); Serial.println(made);
}

void runContinuous() {
  made = 0; wantSteps = 0; doneSteps = 0; stopAsked = false;
  Serial.println(F("GO continuous - measuring the cutter for 3 turns, no feeding yet"));
  resetSwitchClock();
  motor(true);
  if (!waitPresses(1, (unsigned long)LEAVE_TIMEOUT_MS + CUT_TIMEOUT_MS) || !waitPresses(3, 2UL * CUT_TIMEOUT_MS)) {
    fault(F("no limit switch signal while the motor runs (motor not turning, or switch wiring)"));
    return;
  }
  const unsigned long T0 = periodUs;                   // time of one turn at the start
  unsigned long feedUs = (unsigned long)(feedSeconds(PIECE_MM) * 1000000.0);
  unsigned long openUs = (unsigned long)(OPEN_PART * T0);
  Serial.print(F("one turn ")); Serial.print(T0 / 1000);
  Serial.print(F(" ms, switch pressed ")); Serial.print(pressedUs / 1000);
  Serial.print(F(" ms, feed takes ")); Serial.print(feedUs / 1000);
  Serial.print(F(" ms, knife safely open ")); Serial.print(openUs / 1000); Serial.println(F(" ms"));
  if (feedUs > openUs) {
    Serial.println(F("NOT STARTED: the feed takes longer than the knife is open. Use a shorter piece (L) or a faster feed (S)."));
    stopAtTop();
    return;
  }
  running = true;
  digitalWrite(PIN_LED, HIGH);
  byte missed = 0;

  while (true) {
    unsigned int edge = pressCount;
    unsigned long T = periodUs;
    if (T > T0 + T0 / 2 || T < T0 / 2) { fault(F("the cutter speed changed a lot (jam, or switch bouncing)")); return; }

    // next top = last press + half the pressed time + one turn. Start so the feed is centred on it.
    unsigned long startUs = tPressUs + pressedUs / 2 + T - feedUs / 2 + (long)OFFSET_MS * 1000L;
    while ((long)(micros() - startUs) < 0) {
      pollSwitch();
      quickKeys();
      if (micros() - tPressUs > T + T / 2) { fault(F("no limit switch signal for too long (cutter stalled?)")); return; }
    }
    if (stopAsked || (PIECES > 0 && made >= PIECES)) break;
    if (pressCount != edge) {                          // knife got to the top before the feed could start: skip this turn
      if (++missed > 3) { fault(F("feed timing lost (offset too large?)")); return; }
      continue;
    }
    missed = 0;

    unsigned long f0 = micros();
    feed(PIECE_MM);                                    // the knife passes the top during this feed
    feedUs = micros() - f0;
    made++;

    unsigned long w0 = millis();                       // the switch must have been pressed during or right after the feed
    while (pressCount == edge) {
      pollSwitch();
      if (millis() - w0 > T / 2000) { fault(F("limit switch not pressed after the feed (cutter stalled?)")); return; }
    }
  }

  stopAtTop();
  finishRun();
}

// ---------------- commands ----------------
void showStatus() {
  Serial.print(F("length ")); Serial.print(PIECE_MM, 1);
  Serial.print(F(" mm, pieces ")); Serial.print(PIECES);
  Serial.print(F(", speed ")); Serial.print(FEED_SPEED, 0);
  Serial.print(F(" mm/s (feed takes ")); Serial.print((unsigned long)(feedSeconds(PIECE_MM) * 1000.0));
  Serial.print(F(" ms), offset ")); Serial.print(OFFSET_MS);
  Serial.print(F(" ms, made ")); Serial.print(made);
  Serial.print(F(", limit switch ")); Serial.println(atTop() ? F("PRESSED (knife at top)") : F("released"));
}

void watchSwitch() {
  Serial.println(F("watching pin 9 for 10 s - press and release the switch by hand"));
  bool last = atTop();
  Serial.println(last ? F("PRESSED") : F("released"));
  unsigned long t0 = millis();
  while (millis() - t0 < 10000) {
    bool s = atTop();
    if (s != last) { last = s; Serial.println(s ? F("PRESSED") : F("released")); }
  }
  Serial.println(F("watch finished"));
}

void handleSerial() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n');
  s.trim();
  if (s.length() == 0) return;
  char c = toupper(s[0]);
  float v = s.substring(1).toFloat();
  if (c == 'G') runContinuous();
  else if (c == '?') showStatus();
  else if (c == 'K') { if (cutToTop()) Serial.println(F("cut done, knife at top")); }
  else if (c == 'W') watchSwitch();
  else if (c == 'L' && v >= 5 && v <= 2000) { PIECE_MM = v; showStatus(); }
  else if (c == 'Q' && v >= 0 && v <= 60000) { PIECES = (unsigned int)v; showStatus(); }
  else if (c == 'S' && v >= 30 && v <= 600) { FEED_SPEED = v; showStatus(); }
  else if (c == 'O' && v >= -500 && v <= 500) { OFFSET_MS = (int)v; showStatus(); }
  else if (c == 'J' && v >= -500 && v <= 500) moveSteps(lround(v * STEPS_PER_MM));
  else Serial.println(F("commands: G K W L75 Q100 S250 O20 J20 ?   (while running: X + -)"));
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
  Serial.println(F("Strip cutter CONTINUOUS ready. G = start, X = stop, ? = settings"));
  showStatus();
  if (AUTO_START) { delay(3000); runContinuous(); }
}

void loop() {
  handleSerial();
}
