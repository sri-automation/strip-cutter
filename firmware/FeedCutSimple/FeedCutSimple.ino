/*
  Strip cutter - feed and cut (Arduino Uno), version 3 (limit switch wired to GND)

  Every piece:  wiper motor ON  ->  knife leaves the top (limit switch releases)
                ->  knife is back at the top (limit switch pressed)  ->  motor OFF
                ->  ONLY THEN the stepper feeds the next length.
  The stepper never moves unless the limit switch was seen to release and press again in that cycle.

  Pins
    D2  -> TB6600 DIR+        D3 -> TB6600 PUL+        (DIR- and PUL- to GND)
    D9  <- limit switch: one terminal to D9, the other to Arduino GND. Pressed = knife at the top.
           No resistor and no +5 V wire: the Arduino's built-in pull-up is used.
    D10 -> relay IN for the wiper motor: 0 V = motor ON

  Serial Monitor: 115200 baud, line ending "Newline"
    G      start        X     stop after the current piece
    K      one cut only (no feed)
    W      watch the limit switch for 10 s (prints every change) - use it to test the switch
    L75    piece length in mm          Q100   number of pieces (0 = keep going)
    J20    jog the net 20 mm (J-5 = back 5 mm)
    ?      show settings and the switch state
*/

// ---------------- settings you may change ----------------
float PIECE_MM      = 75.0;     // piece length, mm
unsigned int PIECES = 0;        // how many pieces per run (0 = until you send X)
const float STEPS_PER_MM = 17.44;   // 1600 steps/rev on a 29.2 mm roller; use your calibrated value if you have one
const float FEED_SPEED   = 200.0;   // mm per second
const float START_SPEED  = 20.0;    // mm per second
const float ACCEL        = 2500.0;  // mm per second squared
const bool  FEED_DIR     = HIGH;    // change to LOW if the net runs backwards
const unsigned int PAUSE_MS         = 300;    // rest after each feed
const unsigned int RUN_ON_MS        = 40;     // motor stays on this long after the switch is pressed (tunes where the knife stops)
const unsigned int LEAVE_TIMEOUT_MS = 2000;   // the switch must release within this time after the motor starts
const unsigned int CUT_TIMEOUT_MS   = 4000;   // the knife must be back at the top within this time
const bool  AUTO_START   = false;   // true = start by itself 3 s after power-up
const bool  LIMIT_PRESSED = LOW;    // switch connects pin 9 to GND when pressed

// ---------------- pins ----------------
const byte PIN_DIR = 2, PIN_PUL = 3, PIN_LIMIT = 9, PIN_RELAY = 10, PIN_LED = 13;

bool running = false, stopAsked = false;
unsigned int made = 0;
double wantSteps = 0;
long doneSteps = 0;

// ---------------- wiper motor and limit switch ----------------
void motor(bool on) { digitalWrite(PIN_RELAY, on ? LOW : HIGH); }   // relay is ON at 0 V

bool atTop() {                           // limit switch pressed (pin 9 at 0 V), steady for 10 ms
  bool s = digitalRead(PIN_LIMIT) == LIMIT_PRESSED;
  unsigned long t = millis();
  while (millis() - t < 10) {
    bool n = digitalRead(PIN_LIMIT) == LIMIT_PRESSED;
    if (n != s) { s = n; t = millis(); }
  }
  return s;
}

bool waitSwitch(bool pressed, unsigned int timeoutMs) {
  unsigned long t0 = millis();
  while (millis() - t0 < timeoutMs) {
    if (atTop() == pressed) return true;
  }
  return false;
}

void fault(const __FlashStringHelper *why) {
  motor(false);
  running = false;
  Serial.print(F("STOPPED: "));
  Serial.println(why);
  for (byte i = 0; i < 10; i++) { digitalWrite(PIN_LED, i & 1); delay(120); }
  digitalWrite(PIN_LED, LOW);
}

// Runs the wiper motor until the knife is at the top again. Returns true only if the
// limit switch was seen RELEASED and then PRESSED while the motor was running.
bool cutToTop() {
  motor(true);
  if (!waitSwitch(false, LEAVE_TIMEOUT_MS)) {
    fault(F("limit switch stays pressed with the motor on. Wiper motor not turning, or pin 9 is shorted to GND, or the switch is wired to the wrong contact (use COM and NO)."));
    return false;
  }
  if (!waitSwitch(true, CUT_TIMEOUT_MS)) {
    fault(F("the knife did not reach the top (limit switch never pressed). Jam, the crank does not touch the switch, or a switch wire is loose."));
    return false;
  }
  delay(RUN_ON_MS);
  motor(false);
  delay(150);                            // let the motor stop before the stepper moves
  return true;
}

// ---------------- stepper feed ----------------
void moveSteps(long n) {
  if (n == 0) return;
  bool fwd = n > 0;
  long total = fwd ? n : -n;
  digitalWrite(PIN_DIR, fwd ? FEED_DIR : !FEED_DIR);
  delayMicroseconds(20);
  const float v0 = START_SPEED * STEPS_PER_MM, vmax = FEED_SPEED * STEPS_PER_MM, a = ACCEL * STEPS_PER_MM;
  unsigned long t = micros();
  for (long i = 0; i < total; i++) {
    long fromEnd = total - 1 - i;
    long r = i < fromEnd ? i : fromEnd;                // ramp up, then ramp down
    float v = sqrt(v0 * v0 + 2.0 * a * r);
    if (v > vmax) v = vmax;
    unsigned long period = (unsigned long)(1000000.0 / v);
    while ((unsigned long)(micros() - t) < period) { }
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

// ---------------- run control ----------------
void showStatus() {
  Serial.print(F("length ")); Serial.print(PIECE_MM, 1);
  Serial.print(F(" mm, pieces ")); Serial.print(PIECES);
  Serial.print(F(", made ")); Serial.print(made);
  Serial.print(F(", limit switch ")); Serial.print(atTop() ? F("PRESSED (knife at top)") : F("released"));
  Serial.println(running ? F(", RUNNING") : F(", idle"));
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

void startRun() {
  made = 0; wantSteps = 0; doneSteps = 0; stopAsked = false;
  Serial.println(F("GO - first the wiper motor makes one turn to find the top"));
  if (!cutToTop()) return;               // no feeding until the top has been found
  running = true;
  digitalWrite(PIN_LED, HIGH);
}

void stopRun() {
  running = false;
  motor(false);
  digitalWrite(PIN_LED, LOW);
  Serial.print(F("DONE, pieces made: ")); Serial.println(made);
}

void handleSerial() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n');
  s.trim();
  if (s.length() == 0) return;
  char c = toupper(s[0]);
  float v = s.substring(1).toFloat();
  if (c == 'X') { stopAsked = true; Serial.println(F("stopping after this piece")); return; }
  if (c == '?') { showStatus(); return; }
  if (running) { Serial.println(F("running - send X first")); return; }
  if (c == 'G') startRun();
  else if (c == 'K') { if (cutToTop()) Serial.println(F("cut done, knife at top")); }
  else if (c == 'W') watchSwitch();
  else if (c == 'L' && v >= 5 && v <= 2000) { PIECE_MM = v; showStatus(); }
  else if (c == 'Q' && v >= 0 && v <= 60000) { PIECES = (unsigned int)v; showStatus(); }
  else if (c == 'J' && v >= -500 && v <= 500) moveSteps(lround(v * STEPS_PER_MM));
  else Serial.println(F("commands: G X K W L75 Q100 J20 ?"));
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
  Serial.println(F("Strip cutter v3 ready. G = start, X = stop, W = test switch, ? = status"));
  showStatus();
  if (AUTO_START) { delay(3000); startRun(); }
}

void loop() {
  handleSerial();
  if (!running) return;
  feed(PIECE_MM);                        // knife is at the top here: the last cutToTop() confirmed it
  delay(PAUSE_MS);
  if (!cutToTop()) return;               // motor ON until the limit switch says top; stops everything if it fails
  made++;
  handleSerial();
  if (stopAsked || (PIECES > 0 && made >= PIECES)) stopRun();
}
