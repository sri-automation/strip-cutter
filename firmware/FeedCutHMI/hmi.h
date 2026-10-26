// Screen pages and the four buttons.
#pragma once

#define D_FOOT 0x08

// ---------------- buttons: A0 STOP/BACK, A1 UP, A2 DOWN, A3 OK ----------------
#define B_BACK 1
#define B_UP   2
#define B_DOWN 4
#define B_OK   8
enum { E_NONE, E_BACK, E_UP, E_DOWN, E_OK, E_OKLONG, E_OKUP };
#ifdef __AVR__
static inline byte btnRaw() { return (~PINC) & 0x0F; }
#else
byte simButtons = 0;
static inline byte btnRaw() { return simButtons; }
#endif
byte btnLast = 0, btnStable = 0;
unsigned long btnChangeMs = 0, btnDownMs = 0, btnRepMs = 0;
bool btnLongSent = false;

byte btnEvent() {
  byte raw = btnRaw();
  unsigned long now = millis();
  if (raw != btnLast) { btnLast = raw; btnChangeMs = now; }
  if (now - btnChangeMs < 15) return E_NONE;                 // still bouncing
  byte pressed = raw & ~btnStable, released = btnStable & ~raw;
  btnStable = raw;
  if (pressed) {
    btnDownMs = now; btnRepMs = now + 450; btnLongSent = false;
    if (pressed & B_BACK) return E_BACK;
    if (pressed & B_UP) return E_UP;
    if (pressed & B_DOWN) return E_DOWN;
    return E_OK;
  }
  if ((released & B_OK) && !btnLongSent) return E_OKUP;
  if ((btnStable & (B_UP | B_DOWN)) && (long)(now - btnRepMs) >= 0) {      // held: repeat, faster after a while
    btnRepMs = now + (now - btnDownMs > 1500 ? 60 : 140);
    return (btnStable & B_UP) ? E_UP : E_DOWN;
  }
  if ((btnStable & B_OK) && !btnLongSent && now - btnDownMs >= 900) { btnLongSent = true; return E_OKLONG; }
  return E_NONE;
}
byte holdMult() { unsigned long h = millis() - btnDownMs; return h < 1500 ? 1 : (h < 4000 ? 10 : 100); }

// ---------------- menus ----------------
enum { K_VAL, K_ACT, K_SUB, K_INFO, K_TOG };
enum {   // values
  V_L, V_Q, V_N, V_S, V_A, V_O, V_T, V_U, V_V, V_D, V_E, V_TFT,
  // toggles
  T_REMOTE, T_AUTO, T_FLIP,
  // read-only
  I_WIFI, I_SSID, I_IP, I_RSSI, I_CLOUD, I_TURN, I_TOTAL, I_VER,
  // actions
  A_START, A_RESETN, A_F1, A_FC, A_K, A_H, A_JF, A_JB, A_R, A_W, A_DEF, A_AP, A_FORGET,
  // sub menus
  M_MAIN, M_TEST, M_CORR, M_PARK, M_WIFI, M_MACH
};
struct MItem { const char *label; uint8_t kind; uint8_t id; };
#define MI(name, text) const char name[] PROGMEM = text;
MI(L_START, "Start cutting") MI(L_LEN, "Piece length") MI(L_Q, "Stop at count") MI(L_N, "Piece count") MI(L_RESETN, "Reset count")
MI(L_S, "Feed speed") MI(L_A, "Acceleration") MI(L_O, "Feed timing") MI(L_TESTS, "Tests") MI(L_CORR, "Length correction")
MI(L_PARK, "Parking") MI(L_WIFI, "Wi-Fi & remote") MI(L_MACH, "Machine")
MI(L_F1, "Feed one piece") MI(L_FC, "Feed until STOP") MI(L_K, "One cut + park") MI(L_H, "Park the knife")
MI(L_JF, "Jog net +10 mm") MI(L_JB, "Jog net -10 mm") MI(L_R, "Roller one turn") MI(L_W, "Switch test")
MI(L_U, "Factor") MI(L_V, "Offset") MI(L_D, "Switch-off lead") MI(L_E, "Nudge")
MI(L_WST, "Status") MI(L_SSID, "Network") MI(L_IP, "Address") MI(L_RSSI, "Signal") MI(L_CLOUD, "Cloud")
MI(L_REM, "Remote control") MI(L_AP, "Setup hotspot") MI(L_FORGET, "Forget Wi-Fi") MI(L_AUTO, "Auto start") MI(L_T, "Test rhythm") MI(L_TURN, "One turn") MI(L_TOT, "Total pieces")
MI(L_TFT, "Screen type") MI(L_FLIP, "Flip screen") MI(L_DEF, "Factory settings") MI(L_VER, "Version")
MI(L_SETTINGS, "SETTINGS")

const MItem MAIN_ITEMS[] PROGMEM = {
  {L_START, K_ACT, A_START}, {L_LEN, K_VAL, V_L}, {L_Q, K_VAL, V_Q}, {L_N, K_VAL, V_N}, {L_RESETN, K_ACT, A_RESETN},
  {L_S, K_VAL, V_S}, {L_A, K_VAL, V_A}, {L_O, K_VAL, V_O}, {L_TESTS, K_SUB, M_TEST}, {L_CORR, K_SUB, M_CORR},
  {L_PARK, K_SUB, M_PARK}, {L_WIFI, K_SUB, M_WIFI}, {L_MACH, K_SUB, M_MACH} };
const MItem TEST_ITEMS[] PROGMEM = {
  {L_F1, K_ACT, A_F1}, {L_FC, K_ACT, A_FC}, {L_K, K_ACT, A_K}, {L_H, K_ACT, A_H},
  {L_JF, K_ACT, A_JF}, {L_JB, K_ACT, A_JB}, {L_R, K_ACT, A_R}, {L_W, K_ACT, A_W} };
const MItem CORR_ITEMS[] PROGMEM = { {L_U, K_VAL, V_U}, {L_V, K_VAL, V_V} };
const MItem PARK_ITEMS[] PROGMEM = { {L_D, K_VAL, V_D}, {L_E, K_VAL, V_E}, {L_H, K_ACT, A_H} };
const MItem WIFI_ITEMS[] PROGMEM = {
  {L_WST, K_INFO, I_WIFI}, {L_SSID, K_INFO, I_SSID}, {L_IP, K_INFO, I_IP}, {L_RSSI, K_INFO, I_RSSI},
  {L_CLOUD, K_INFO, I_CLOUD}, {L_REM, K_TOG, T_REMOTE}, {L_AP, K_ACT, A_AP}, {L_FORGET, K_ACT, A_FORGET} };
const MItem MACH_ITEMS[] PROGMEM = {
  {L_AUTO, K_TOG, T_AUTO}, {L_T, K_VAL, V_T}, {L_TURN, K_INFO, I_TURN}, {L_TOT, K_INFO, I_TOTAL},
  {L_TFT, K_VAL, V_TFT}, {L_FLIP, K_TOG, T_FLIP}, {L_DEF, K_ACT, A_DEF}, {L_VER, K_INFO, I_VER} };

struct Menu { const char *title; const MItem *items; uint8_t n; };
const Menu MENUS[] PROGMEM = {
  {L_SETTINGS, MAIN_ITEMS, 13}, {L_TESTS, TEST_ITEMS, 8}, {L_CORR, CORR_ITEMS, 2},
  {L_PARK, PARK_ITEMS, 3}, {L_WIFI, WIFI_ITEMS, 8}, {L_MACH, MACH_ITEMS, 8} };

// ---------------- page state ----------------
enum { SC_HOME, SC_MENU, SC_EDIT, SC_CONFIRM, SC_FAULT };
byte screen = SC_HOME, dirty = D_ALL;
byte menuId = 0, sel = 0, top = 0, parentSel = 0;     // menuId 0..5 = M_MAIN..M_MACH
byte editId = 0, confirmId = 0;
float editVal = 0;
unsigned long okHoldMs = 0;
byte shownDigits = 0;
bool splashOn = false;
#define ROWS 7

void uiDirty(byte what) { dirty |= what; }

MItem menuItem(byte m, byte i) {
  Menu mn; memcpy_P(&mn, &MENUS[m], sizeof(Menu));
  MItem it; memcpy_P(&it, &mn.items[i], sizeof(MItem));
  return it;
}
byte menuLen(byte m) { return pgm_read_byte(&MENUS[m].n); }

// value limits: lo, hi, step, decimals, unit
struct VMeta { float lo, hi, step; uint8_t dp; const char *unit; };
const char U_MM[] PROGMEM = "mm", U_MMS[] PROGMEM = "mm/s", U_MMS2[] PROGMEM = "mm/s2", U_MS[] PROGMEM = "ms", U_PCS[] PROGMEM = "pcs", U_NONE[] PROGMEM = "";
VMeta valMeta(byte id) {
  switch (id) {
    case V_L:   return { 5, 2000, 0.5, 1, U_MM };
    case V_Q:   return { 0, 9999999, 1, 0, U_PCS };
    case V_N:   return { 0, 9999999, 1, 0, U_PCS };
    case V_S:   return { 50, 2000, 50, 0, U_MMS };
    case V_A:   return { 500, 30000, 500, 0, U_MMS2 };
    case V_O:   return { -500, 500, 5, 0, U_MS };
    case V_T:   return { 200, 60000, 100, 0, U_MS };
    case V_U:   return { 0.5, 1.5, 0.001, 4, U_NONE };
    case V_V:   return { -50, 50, 0.1, 2, U_MM };
    case V_D:   return { -100, 400, 5, 0, U_MS };
    case V_E:   return { 5, 100, 1, 0, U_MS };
    default:    return { 1, 3, 1, 0, U_NONE };            // V_TFT
  }
}
float valGet(byte id) {
  switch (id) {
    case V_L: return cfg.pieceMm;   case V_Q: return cfg.target;   case V_N: return made;
    case V_S: return cfg.speed;     case V_A: return cfg.accel;    case V_O: return cfg.offsetMs;
    case V_T: return cfg.testMs;    case V_U: return cfg.lenK;     case V_V: return cfg.lenC;
    case V_D: return cfg.leadMs;    case V_E: return cfg.creepMs;  default: return cfg.tftType + 1;
  }
}
void valSet(byte id, float v) {
  long n = lround(v);
  switch (id) {
    case V_L: cfg.pieceMm = v; break;   case V_Q: cfg.target = n; break;
    case V_N: made = n; saveCount(); sayCount(); break;
    case V_S: cfg.speed = v; break;     case V_A: cfg.accel = v; break;     case V_O: cfg.offsetMs = n; break;
    case V_T: cfg.testMs = n; break;    case V_U: cfg.lenK = v; break;      case V_V: cfg.lenC = v; break;
    case V_D: cfg.leadMs = n; break;    case V_E: cfg.creepMs = n; break;
    case V_TFT: cfg.tftType = n - 1; tftType = cfg.tftType; tftSetRotation(); break;
  }
  settingsChanged();
}

// text of a value for the list and the edit page
char *valText(byte id, char *b) {
  b[0] = 0;
  if (id <= V_TFT) {
    VMeta m = valMeta(id);
    float v = valGet(id);
    if (id == V_Q && v == 0) { strcpy_P(b, PSTR("off")); return b; }
    fmtNum(b, v, id == V_U ? 3 : m.dp);
    if (id != V_U && id != V_TFT && id != V_Q && id != V_N) { strcat(b, " "); strcat_P(b, m.unit); }
    return b;
  }
  switch (id) {
    case T_REMOTE: strcpy_P(b, cfg.remote ? PSTR("ON") : PSTR("OFF")); break;
    case T_AUTO:   strcpy_P(b, cfg.autoStart ? PSTR("ON") : PSTR("OFF")); break;
    case T_FLIP:   strcpy_P(b, cfg.tftFlip ? PSTR("ON") : PSTR("OFF")); break;
    case I_WIFI:   strcpy_P(b, wifiState == 2 ? PSTR("connected") : wifiState == 1 ? PSTR("looking") : wifiState == 3 ? PSTR("setup hotspot") : PSTR("no module")); break;
    case I_SSID:   strcpy(b, wifiState >= 2 && wifiSsid[0] ? wifiSsid : "-"); break;
    case I_IP:     strcpy(b, wifiState >= 2 && wifiIp[0] ? wifiIp : "-"); break;
    case I_RSSI:   if (wifiState == 2) { itoa(wifiRssi, b, 10); strcat_P(b, PSTR(" dBm")); } else strcpy(b, "-"); break;
    case I_CLOUD:  strcpy_P(b, cloudState == 2 ? PSTR("online") : cloudState == 1 ? PSTR("connecting") : PSTR("off")); break;
    case I_TURN:   if (cfg.turnMs) { itoa(cfg.turnMs, b, 10); strcat_P(b, PSTR(" ms")); } else strcpy(b, "-"); break;
    case I_TOTAL:  ultoa(total, b, 10); break;
    case I_VER:    strcpy_P(b, PSTR(VERSION_TEXT)); break;
  }
  return b;
}

// ---------------- drawing ----------------
const char H_READY[] PROGMEM = "READY", H_MEAS[] PROGMEM = "MEASURING", H_RUN[] PROGMEM = "CUTTING", H_TEST[] PROGMEM = "FEED TEST",
           H_CUT[] PROGMEM = "ONE CUT", H_PARK[] PROGMEM = "PARKING", H_JOG[] PROGMEM = "JOG", H_WATCH[] PROGMEM = "SWITCH", H_FAULT[] PROGMEM = "FAULT",
           H_STOPPING[] PROGMEM = "STOPPING";
const char *const HNAMES[] PROGMEM = { H_READY, H_MEAS, H_RUN, H_TEST, H_CUT, H_PARK, H_JOG, H_WATCH, H_FAULT };

uint16_t stateColour() {
  switch (curState) {
    case ST_IDLE: return C_PANEL;
    case ST_MEASURE: case ST_RUN: return C_GO;
    case ST_FAULT: return C_RED;
    default: return C_AMBER;
  }
}

void drawIcons(uint16_t bg) {            // right end of the header: remote lock, cloud, Wi-Fi bars
  fillRect(118, 2, 42, 14, bg);
  bool dark = (bg == C_AMBER);
  uint16_t on = dark ? C_BLACK : C_WHITE, off = dark ? 0x8400 : C_LINE;
  if (wifiState == 3) drawTextP(140, 5, F("AP"), on, bg, 1);
  else if (wifiState) {
    byte bars = wifiState != 2 ? 0 : wifiRssi >= -55 ? 4 : wifiRssi >= -65 ? 3 : wifiRssi >= -75 ? 2 : 1;
    for (byte i = 0; i < 4; i++) fillRect(141 + i * 4, 14 - 3 * (i + 1), 3, 3 * (i + 1), i < bars ? on : off);
  }
  if (cloudState) {                      // a small cloud
    uint16_t c = cloudState == 2 ? on : off;
    fillRect(128, 9, 9, 4, c); fillRect(130, 6, 5, 3, c);
  }
  if (!cfg.remote) {                     // padlock: remote control is locked
    uint16_t c = on;
    fillRect(119, 9, 7, 6, c); fillRect(120, 5, 1, 4, c); fillRect(124, 5, 1, 4, c); fillRect(120, 4, 5, 1, c);
  }
}

void drawHeader() {
  uint16_t bg; const __FlashStringHelper *t;
  if (screen == SC_MENU || screen == SC_EDIT || screen == SC_CONFIRM) {
    bg = C_BLUE;
    if (screen == SC_EDIT) t = (const __FlashStringHelper *)menuItem(menuId, sel).label;
    else if (screen == SC_CONFIRM) t = F("ARE YOU SURE?");
    else t = (const __FlashStringHelper *)pgm_read_ptr(&MENUS[menuId].title);
  } else {
    bg = stateColour();
    t = (stopAsked && (running || curState == ST_FEEDTEST)) ? (const __FlashStringHelper *)H_STOPPING
                                                             : (const __FlashStringHelper *)pgm_read_ptr(&HNAMES[curState]);
  }
  uint16_t fg = (bg == C_AMBER) ? C_BLACK : C_WHITE;
  fillRect(0, 0, 118, 18, bg);
  byte s = lenP(t) <= 9 ? 2 : 1;
  drawTextP(4, s == 2 ? 2 : 6, t, fg, bg, s);
  drawIcons(bg);
  fillRect(118, 0, 42, 2, bg); fillRect(118, 16, 42, 2, bg);
}

void drawFooter() {
  fillRect(0, 116, TFT_W, 12, C_PANEL);
  const __FlashStringHelper *h;
  if (screen == SC_MENU) h = F(SYM_UP SYM_DOWN " move  OK pick STOP back");
  else if (screen == SC_EDIT) h = F(SYM_UP SYM_DOWN " set  OK save  STOP undo");
  else if (screen == SC_CONFIRM) h = F("OK = yes      STOP = no");
  else if (screen == SC_FAULT) h = F("OK = clear");
  else if (curState == ST_IDLE) h = F("hold OK = START  " SYM_UP SYM_DOWN " MENU");
  else if (stopAsked) h = F("STOP again = stop now");
  else if (curState == ST_RUN || curState == ST_MEASURE) h = F("STOP = stop  " SYM_UP SYM_DOWN " timing");
  else h = F("STOP = stop");
  drawTextP(3, 118, h, C_DIM, C_PANEL, 1);
}

// long text over several lines of 25 characters
byte drawWrapped(int y, const __FlashStringHelper *ft, uint16_t fg, byte maxLines) {
  const char *p = (const char *)ft; byte lines = 0;
  while (pgm_read_byte(p) && lines < maxLines) {
    byte n = 0, cut = 0;
    while (n < 25 && pgm_read_byte(p + n)) { if (pgm_read_byte(p + n) == ' ') cut = n; n++; }
    if (pgm_read_byte(p + n) && cut) n = cut;
    fillRect(0, y, TFT_W, 9, C_BG);
    for (byte i = 0; i < n; i++) drawChar(5 + i * 6, y, pgm_read_byte(p + i), fg, C_BG, 1);
    p += n; while (pgm_read_byte(p) == ' ') p++;
    y += 10; lines++;
  }
  return lines;
}

void drawCount() {
  char b[12];
  uint32_t v = (curState == ST_FEEDTEST) ? testMade : made;
  ultoa(v, b, 10);
  byte n = strlen(b), digits = n < 3 ? 3 : n;
  if (digits > 6) { digits = 6; }                       // above 999999 the low six digits are shown
  if (digits != shownDigits) { fillRect(0, 20, TFT_W, 40, C_BG); shownDigits = digits; }
  int w = digits * 24 - 4, x = (TFT_W - w) / 2;
  for (byte i = 0; i < digits; i++) {
    int k = (int)n - digits + i;
    char d = k >= 0 ? b[k] : ' ';
    drawSeg(x + i * 24, 22, d, 20, 36, 4, curState == ST_FEEDTEST ? C_AMBER : C_TEXT, C_PANEL);
  }
}

void drawInfo() {
  char b[16];
  fillRect(0, 60, TFT_W, 56, C_BG);
  if (curState == ST_WATCH) {
    bool on = swState;
    fillRect(20, 64, 120, 26, on ? C_GO : C_PANEL);
    drawTextP(on ? 38 : 32, 69, on ? F("PRESSED") : F("released"), C_WHITE, on ? C_GO : C_PANEL, 2);
    drawTextP(5, 96, F("Press the switch by hand"), C_DIM, C_BG, 1);
    return;
  }
  drawTextP(5, 62, curState == ST_FEEDTEST ? F("test feeds") : F("pieces"), C_DIM, C_BG, 1);
  if (cfg.target) {
    int x = drawTextP(80, 62, F("stop at "), C_DIM, C_BG, 1);
    drawText(x, 62, ultoa(cfg.target, b, 10), C_TEXT, C_BG, 1);
    fillRect(5, 72, 150, 4, C_PANEL);
    uint32_t w = made >= cfg.target ? 150 : (uint32_t)150 * made / cfg.target;
    fillRect(5, 72, w, 4, C_GO);
  }
  if (faultMsg && curState != ST_FAULT) faultMsg = 0;
  if (noteMsg) { drawWrapped(81, noteMsg, C_AMBER, 3); return; }
  int x = drawTextP(5, 81, F("Length "), C_DIM, C_BG, 1);
  x = drawText(x, 81, fmtNum(b, cfg.pieceMm, 1), C_TEXT, C_BG, 1);
  drawTextP(x, 81, F(" mm"), C_DIM, C_BG, 1);
  if (curState == ST_RUN && rateNow > 0) {
    x = drawText(100, 81, fmtNum(b, rateNow, 1), C_GOLITE, C_BG, 1);
    drawTextP(x, 81, F("/min"), C_DIM, C_BG, 1);
  }
  x = drawTextP(5, 93, F("Timing "), C_DIM, C_BG, 1);
  itoa(cfg.offsetMs, b, 10); x = drawText(x, 93, b, C_TEXT, C_BG, 1);
  x = drawTextP(x, 93, F(" ms"), C_DIM, C_BG, 1);
  if (feedPlanMs) {
    x = drawTextP(84, 93, F("feed "), C_DIM, C_BG, 1);
    itoa(feedRealMs ? feedRealMs : feedPlanMs, b, 10); x = drawText(x, 93, b, C_TEXT, C_BG, 1);
    drawTextP(x, 93, F("ms"), C_DIM, C_BG, 1);
  }
  x = drawTextP(5, 104, F("Knife "), C_DIM, C_BG, 1);
  if (running || curState == ST_MEASURE || curState == ST_CUT || curState == ST_PARK) drawTextP(x, 104, F("moving"), C_TEXT, C_BG, 1);
  else drawTextP(x, 104, swState ? F("at the top") : F("NOT at the top"), swState ? C_GOLITE : C_AMBER, C_BG, 1);
}

void drawRow(byte i) {                   // one line of the menu list
  byte idx = top + i;
  int y = 20 + i * 13;
  bool s = (idx == sel);
  uint16_t bg = s ? C_SEL : C_BG;
  fillRect(0, y, 156, 13, bg);
  if (idx >= menuLen(menuId)) return;
  MItem it = menuItem(menuId, idx);
  drawTextP(5, y + 3, (const __FlashStringHelper *)it.label, s ? C_WHITE : C_TEXT, bg, 1);
  char b[22];
  if (it.kind == K_SUB) strcpy(b, SYM_RIGHT);
  else if (it.kind == K_ACT) b[0] = 0;
  else valText(it.id, b);
  byte room = (141 - lenP((const __FlashStringHelper *)it.label) * 6) / 6;   // chars left after the label
  byte n = strlen(b); if (n > room) { b[room] = 0; n = room; }
  drawText(152 - n * 6, y + 3, b, it.kind == K_INFO ? C_DIM : (s ? C_WHITE : C_GOLITE), bg, 1);
}

void drawMenu() {
  fillRect(0, 18, TFT_W, 98, C_BG);
  for (byte i = 0; i < ROWS; i++) drawRow(i);
  byte n = menuLen(menuId);
  if (n > ROWS) {                        // scroll bar
    fillRect(157, 20, 2, 91, C_PANEL);
    byte h = 91 * ROWS / n, y = 20 + (91 - h) * top / (n - ROWS);
    fillRect(157, y, 2, h, C_DIM);
  }
}

void drawEditValue() {
  char b[16];
  VMeta m = valMeta(editId);
  fmtNum(b, editVal, editId == V_U ? 3 : m.dp);
  if (editId == V_Q && editVal == 0) strcpy_P(b, PSTR("off"));
  byte n = strlen(b), s = n <= 8 ? 3 : 2;
  fillRect(0, 34, TFT_W, 26, C_BG);
  drawText((TFT_W - n * 6 * s) / 2, 36, b, C_WHITE, C_BG, s);
}

void drawEdit() {
  char b[24], c[12];
  fillRect(0, 18, TFT_W, 98, C_BG);
  drawEditValue();
  VMeta m = valMeta(editId);
  byte n = strlen_P(m.unit);
  drawTextP((TFT_W - n * 6) / 2, 64, (const __FlashStringHelper *)m.unit, C_DIM, C_BG, 1);
  fmtNum(b, m.lo, m.dp); strcat(b, " to "); strcat(b, fmtNum(c, m.hi, m.dp));
  drawText((TFT_W - strlen(b) * 6) / 2, 80, b, C_DIM, C_BG, 1);
  drawTextP(14, 96, F("hold " SYM_UP SYM_DOWN " to go faster"), C_DIM, C_BG, 1);
}

void drawConfirm() {
  fillRect(0, 18, TFT_W, 98, C_BG);
  if (confirmId == A_RESETN) { drawTextP(14, 46, F("Reset the piece count"), C_TEXT, C_BG, 1); drawTextP(50, 60, F("to zero?"), C_TEXT, C_BG, 1); }
  else if (confirmId == A_FORGET) { drawTextP(14, 46, F("Forget saved Wi-Fi and"), C_TEXT, C_BG, 1); drawTextP(14, 60, F("reset the password?"), C_TEXT, C_BG, 1); }
  else { drawTextP(14, 46, F("Put all settings back"), C_TEXT, C_BG, 1); drawTextP(26, 60, F("to the defaults?"), C_TEXT, C_BG, 1); }
}

void drawFault() {
  fillRect(0, 18, TFT_W, 98, C_BG);
  if (faultMsg) drawWrapped(26, faultMsg, C_TEXT, 8);
}

void uiDraw() {                          // draws whatever has changed; short, can be called while running
  if (!dirty || splashOn) return;
  byte d = dirty; dirty = 0;
  if (d == D_ALL) { fillRect(0, 18, TFT_W, 98, C_BG); shownDigits = 0; }
  if (d & D_HEAD) drawHeader();
  if (screen == SC_HOME) {
    if (d & D_COUNT) drawCount();
    if (d & D_INFO) drawInfo();
  } else if (d & (D_COUNT | D_INFO)) {
    if (screen == SC_MENU) drawMenu();
    else if (screen == SC_EDIT) drawEdit();
    else if (screen == SC_CONFIRM) drawConfirm();
    else drawFault();
  }
  if (d & D_FOOT) drawFooter();
}

void goScreen(byte s) { screen = s; dirty = D_ALL; }
void openMenu(byte m, byte s);

void uiStateChanged() {
  if (curState == ST_FAULT) { goScreen(SC_FAULT); okHoldMs = 0; }
  else if (curState != ST_IDLE && screen != SC_HOME) goScreen(SC_HOME);
  else if (curState == ST_IDLE && screen == SC_FAULT) goScreen(SC_HOME);
  else dirty |= D_HEAD | D_FOOT | D_INFO | D_COUNT;
  uiDraw();
}

void uiSetup() {
  tftType = cfg.tftType; tftFlip = cfg.tftFlip;
  tftInit();
  fillRect(0, 0, TFT_W, TFT_H, C_BG);
  fillRect(0, 0, TFT_W, 4, C_NET);
  drawTextP(35, 30, F("STRIP"), C_WHITE, C_BG, 3);
  drawTextP(26, 58, F("CUTTER"), C_WHITE, C_BG, 3);
  drawTextP(62, 90, F("v" VERSION_TEXT), C_DIM, C_BG, 1);
  splashOn = true;
}
void uiSplashEnd() { if (splashOn) { splashOn = false; goScreen(SC_HOME); uiDraw(); } }

// The 3 s before an automatic start: any button or a command cancels it, OK starts at once.
bool uiAutoStartWait() {
  unsigned long t0 = millis();
  byte shown = 9;
  while (millis() - t0 < 3000) {
    byte left = 3 - (millis() - t0) / 1000;
    if (left != shown) {
      shown = left;
      fillRect(0, 100, TFT_W, 28, C_BG);
      int x = drawTextP(14, 102, F("Starting in "), C_AMBER, C_BG, 1);
      drawChar(x, 102, '0' + left, C_AMBER, C_BG, 1);
      drawTextP(14, 114, F("any button = cancel"), C_DIM, C_BG, 1);
    }
    byte e = btnEvent();
    if (e) { uiSplashEnd(); return false; }    // any button cancels, as the screen says
    if (linkRead() && linkFrame()) {
      if (lineBuf[0] == 'I') wifiInfo(lineBuf + 1);
      else { uiSplashEnd(); dispatch(lineBuf); return false; }
    }
  }
  uiSplashEnd();
  return true;
}

void uiBusyButtons() {                   // while something runs: STOP and the timing keys
  byte e = btnEvent();
  if (e == E_BACK) {
    if (!stopAsked) { stopAsked = true; Serial.println(F("stopping")); }
    else { abortAsked = true; motor(false); }
    beep(30);
    dirty |= D_HEAD | D_FOOT;
  } else if ((e == E_UP || e == E_DOWN) && (curState == ST_RUN || curState == ST_MEASURE)) {
    cfg.offsetMs += e == E_UP ? 10 : -10;
    Serial.print(F("#O ")); Serial.println(cfg.offsetMs);
    dirty |= D_INFO;
  }
}

void doAction(byte id) {
  byte m = menuId, s = sel, p = parentSel;
  dirty = D_ALL;
  switch (id) {
    case A_START: goScreen(SC_HOME); runContinuous(); break;
    case A_F1: feederTest(1); break;
    case A_FC: feederTest(0); break;
    case A_K:  cutOnce(); break;
    case A_H:  parkOnly(); break;
    case A_JF: jog(10); break;
    case A_JB: jog(-10); break;
    case A_R:  rollerTurn(); break;
    case A_W:  watchSwitch(); break;
    case A_AP: Serial.println(F("$AP")); break;                  // tells the Wi-Fi module to open its setup hotspot
    case A_RESETN: case A_DEF: case A_FORGET: confirmId = id; goScreen(SC_CONFIRM); return;
  }
  if (curState != ST_FAULT && id != A_START) { parentSel = p; openMenu(m, s); }   // back to the list it came from
}

void openMenu(byte m, byte s) {
  menuId = m; sel = s; top = s >= ROWS ? s - ROWS + 1 : 0;
  goScreen(SC_MENU);
}

void uiIdle() {                          // navigation while nothing is running
  if (wifiSeen && millis() - wifiSeen > 15000) { wifiState = 0; cloudState = 0; wifiSeen = 0; dirty |= D_HEAD; }
  byte e = btnEvent();
  if (e) beep(8);
  switch (screen) {
    case SC_HOME:
      if (e == E_OK) { okHoldMs = millis(); }
      else if (e == E_OKLONG) { okHoldMs = 0; dirty |= D_FOOT; runContinuous(); }
      else if (e == E_OKUP) { okHoldMs = 0; dirty |= D_FOOT; }
      else if (e == E_UP || e == E_DOWN) { noteMsg = 0; openMenu(0, 0); }
      else if (e == E_BACK && noteMsg) { noteMsg = 0; dirty |= D_INFO; }
      if (okHoldMs) {                    // filling bar while OK is held
        unsigned long h = millis() - okHoldMs; if (h > 900) h = 900;
        fillRect(0, 116, h * TFT_W / 900, 12, C_GO);
      }
      break;
    case SC_FAULT:
      if (e == E_OK || e == E_BACK) { faultMsg = 0; state(ST_IDLE); goScreen(SC_HOME); }
      break;
    case SC_MENU: {
      byte n = menuLen(menuId);
      if (e == E_UP && sel > 0) sel--;
      else if (e == E_DOWN && sel < n - 1) sel++;
      else if (e == E_BACK) { if (menuId) openMenu(0, parentSel); else goScreen(SC_HOME); break; }
      else if (e == E_OK) {
        MItem it = menuItem(menuId, sel);
        if (it.kind == K_SUB) { parentSel = sel; openMenu(it.id - M_MAIN, 0); }
        else if (it.kind == K_VAL) { editId = it.id; editVal = valGet(editId); goScreen(SC_EDIT); }
        else if (it.kind == K_TOG) {
          if (it.id == T_REMOTE) cfg.remote ^= 1;
          else if (it.id == T_AUTO) cfg.autoStart ^= 1;
          else { cfg.tftFlip ^= 1; tftFlip = cfg.tftFlip; tftSetRotation(); dirty = D_ALL; }
          settingsChanged();
        }
        else if (it.kind == K_ACT) doAction(it.id);
        break;
      } else break;
      if (sel < top) { top = sel; dirty |= D_INFO; }
      else if (sel >= top + ROWS) { top = sel - ROWS + 1; dirty |= D_INFO; }
      else { drawRow(sel - top + (e == E_UP ? 1 : -1)); drawRow(sel - top); }
      break;
    }
    case SC_EDIT: {
      VMeta m = valMeta(editId);
      if (e == E_UP || e == E_DOWN) {
        float st = m.step * holdMult();
        editVal += e == E_UP ? st : -st;
        editVal = lround(editVal / m.step) * m.step;
        if (editVal < m.lo) editVal = m.lo;
        if (editVal > m.hi) editVal = m.hi;
        drawEditValue();
      }
      else if (e == E_OK) { valSet(editId, editVal); goScreen(SC_MENU); }
      else if (e == E_BACK) goScreen(SC_MENU);
      break;
    }
    case SC_CONFIRM:
      if (e == E_OK) {
        if (confirmId == A_RESETN) { made = 0; saveCount(); sayCount(); showStatus(); }
        else if (confirmId == A_FORGET) Serial.println(F("$FORGET"));   // the Wi-Fi module clears its list
        else { Cfg k = cfg; cfg = DEFAULTS; cfg.turnMs = k.turnMs; cfg.gapMs = k.gapMs; cfg.leadMs = k.leadMs; cfg.tftType = k.tftType; cfg.tftFlip = k.tftFlip; settingsChanged(); }
        goScreen(SC_MENU);
      } else if (e == E_BACK) goScreen(SC_MENU);
      break;
  }
  uiDraw();
}
