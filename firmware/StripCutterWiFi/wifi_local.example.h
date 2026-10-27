// wifi_local.h - this machine's own settings. Copy this file to wifi_local.h (same folder) and fill
// it in. wifi_local.h stays on your PC: it is listed in .gitignore, so it never goes to GitHub.
#pragma once

// A network the machine always knows (added, or its password corrected, at every start).
// Leave these two lines out to use only the networks saved from the app.
#define DEFAULT_WIFI_NAME "your network name"
#define DEFAULT_WIFI_PASS "your password"

// 1 = Wi-Fi log on the serial port for fault finding: DIP 5 + 6 ON (7 OFF), Serial Monitor 115200.
// The log stops once the machine is on Wi-Fi, after 10 minutes, and whenever the machine runs.
#define WIFI_LOG 0
