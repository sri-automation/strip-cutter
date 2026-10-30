# Strip Cutter

A bench machine that feeds red packaging net (12 × 2.7 mm) and cuts it into pieces of a set length (50–100 mm, 70 mm by default).

- **Feed:** a NEMA 23 stepper (TB6600 driver, 1600 steps/rev) drives a printed roller, with a spring-loaded pinch roller above it.
- **Cut:** a 12 V car wiper motor (switched by a relay) turns a crank. A link and lever close an HSS planer knife past a fixed one, like scissors. A limit switch stops the knife at the top, where the net is fed.
- **Control:**
  - an Arduino *Uno + WiFi* board (ATmega328P + ESP8266);
  - a 1.8" colour screen and four buttons on the front panel;
  - a phone/PC app that works over USB, over your Wi-Fi, or from anywhere through a free cloud server.

| | |
|---|---|
| **Control app (online)** | https://sri-automation.github.io/strip-cutter/ |
| **Electronics, Wi-Fi and app guide** | [README_electronics_v5.html](https://sri-automation.github.io/strip-cutter/README_electronics_v5.html) (opens as a page; the copy in this repo is the same file) |
| **At the machine** | http://stripcutter.local, or the address shown on the machine's screen |

## What is where

| Path | What it is |
|---|---|
| `index.html` | The control app, published with GitHub Pages. It is the same file as `app/StripCutter.html`. |
| `app/StripCutter.html` | The control app. To use it on the PC over USB, open it with `app/Start Strip Cutter.bat`. `app/old_v3`, `app/old_v4`: earlier apps, which don't work with the v5 firmware. |
| `firmware/FeedCutHMI/` | **Machine sketch (current)** for the ATmega328P: feeding, cutting, screen, buttons. |
| `firmware/StripCutterWiFi/` | **Wi-Fi module sketch (current)** for the ESP8266: saved networks, setup hotspot, app server, cloud link. `app_gz.h` is the app, built into the module. |
| `firmware/FeedCut*`, `firmware/FeederDemo` | Earlier sketches, kept for reference. |
| `print_STL_*` | 3D-print files by part group and version. Most folders have a sliced Bambu Lab A1 project (`.3mf`: 0.6 mm nozzle, PETG-CF). |
| `cad/` | Fusion 360 archives (`.f3d`), STEP files, and the Python scripts that built and checked the parts. |
| `README_feeder*.md`, `README_cutter_v*.md` | Build notes for each change: what was changed and why, print settings, hardware, fitting steps. |
| `*.png` | Pictures referenced by the build notes. |
| `Cutter_v6_templates_1to1_A4.pdf` | Drilling templates (print at 100 %). |
| `tools/make_app_gz.py` | After editing the app, updates `index.html` and `app_gz.h`. |

## Build notes, in order

| Notes | Change |
|---|---|
| [README_feeder.md](README_feeder.md) | Feeder v3: printed feed frame, rollers, pinch arm, assembly and first run |
| [README_feeder_v4.md](README_feeder_v4.md) | Feeder v4: fixes for twists, roller tilt and frame flex |
| [README_feeder_v5.md](README_feeder_v5.md) | Feeder v5: keeps the net centred through the rollers |
| [README_cutter_v6.md](README_cutter_v6.md) | Cutter v6: plywood demo shear driven by the wiper motor |
| [README_cutter_v7.md](README_cutter_v7.md) | Cutter v7: printed PETG-CF cutter parts |
| [README_cutter_v8.md](README_cutter_v8.md) | Cutter v8: corrected after the template and coupon test |
| [README_cutter_v9.md](README_cutter_v9.md) | Cutter v9: reprinted plates, keyed crank, shaft keys, exit ramp |
| [README_cutter_v10.md](README_cutter_v10.md) | Cutter v10: gap-filler plate between the main plate and the upper blade |
| [README_cutter_v11.md](README_cutter_v11.md) | Cutter v11: exit-guide extension nozzle |
| [README_feeder_v6_exit_guide.md](README_feeder_v6_exit_guide.md) | Feeder v6: exit guide with a long nose. Replaces the v10 gap filler, the shims and the v11 nozzle |
| [README_feeder_v7.md](README_feeder_v7.md) | Feeder v7: stronger pinch arm, and an exit guide that clears the top roller and the blade |
| [README_electronics_v5.html](https://sri-automation.github.io/strip-cutter/README_electronics_v5.html) | Electronics v5: screen, buttons, Wi-Fi, app, cloud |
| `print_STL_hmi_panel_v1/`, `print_STL_hmi_panel_v2/` | Front panel fit checks. v2 has the arrow-key layout, and the screen is held by four M3 screws through its corner holes |
| [README_hmi_enclosure_v1.md](README_hmi_enclosure_v1.md) | HMI enclosure v1: 150 mm sloped stand for the v2 front panel (60° face), with a foot screwed to the wood and wiring paths |

## Loading the firmware (short version)

The full steps, wiring and DIP-switch table are in the [electronics guide](https://sri-automation.github.io/strip-cutter/README_electronics_v5.html).

1. **Machine sketch.**
   - DIP switches **3 + 4 ON**, the rest OFF.
   - Board **Arduino Uno**. Upload `firmware/FeedCutHMI/FeedCutHMI.ino`.
2. **Wi-Fi sketch.**
   - Install the board package **esp8266 (3.1.x)**.
   - Install the libraries **WebSockets** by Markus Sattler and **PubSubClient** by Nick O'Leary.
   - DIP switches **5 + 6 + 7 ON**, the rest OFF.
   - Tools settings: board **Generic ESP8266 Module**, flash **4MB (FS:none OTA:~1019KB)**, CPU **160 MHz**.
   - Upload `firmware/StripCutterWiFi/StripCutterWiFi.ino`.
3. **Run.**
   - DIP switches **1 + 2 ON**, the rest OFF, then power off and on again.
   - With no network saved, the machine opens the hotspot **StripCutter-Setup** (password `stripcutter`).
   - Join it with a phone and add your 2.4 GHz Wi-Fi networks on the Wi-Fi tab.
   - Then change the machine password.

If the machine does not join your Wi-Fi, open **Wi-Fi & remote → Wi-Fi details** on its screen. It shows why (password refused, not in range, no answer, no address ...), every saved network with its signal, and the networks it can hear. OK there tries again.

Buttons on the v2 front panel:

| Button | Pin | Does |
|---|---|---|
| LEFT | A0 | STOP / BACK |
| UP | A1 | UP |
| DOWN | A2 | DOWN |
| RIGHT | A3 | OK / START (hold 1 s to start) |

## Parking the knife at the top

On a stop, and after **One cut + park**, the motor switches off just before the top and the knife coasts up to the limit switch. If it stops short, short nudges bring it onto the switch.

The settings are in the app (**Settings → Parking at the top**) and on the machine (**menu → Parking**):

| Setting | Command | Range | What it does |
|---|---|---|---|
| Switch-off lead | D | −100 to 400 ms | The motor goes off this long before the top. The machine fine-tunes it after every stop. |
| Nudge | E | 1 to 100 ms | One short push. It ends early the moment the switch closes. A nudge too short to move the knife gets a little longer every second try. |
| Wait before nudging | P | 100 to 5000 ms (800) | The time after the switch-off before the machine looks where the knife is. The knife must have stopped coasting by then. |
| Pause between nudges | B | 50 to 5000 ms (300) | The time after each nudge before the next one. |

To tune it:

1. Press **One cut + park** a few times.
2. Watch the **Last stop** line and the parking log in the app.
3. If the knife is still creeping when the nudges start, raise **Wait before nudging**.
4. If it keeps going past the top, raise **Switch-off lead**.

A relay needs a few milliseconds to pull in, so very short nudges may do nothing. The machine lengthens them by itself until they move the knife.

## When it stops with "cutter stalled" or "speed changed a lot"

While cutting, the machine times every feed from the turns before it. A turn much slower than usual is logged as `run: slow turn 1630 ms, usual 848`, and the app shows the count on the Run page.

| Log shows | Usually means |
|---|---|
| An occasional turn 1.5 to 3 times the usual | A hard cut, or the 12 V supply dipping under the wiper motor's load. The machine carries on, timing the next feed from the usual turn. |
| A turn about twice the usual | The limit switch missed one press. |
| Three slow turns in a row, a turn over 3 times the usual, or no switch for 2 turns | The machine stops. |

**Check:**

- The 12 V supply can deliver the wiper motor's current under load. A separate supply for the stepper driver helps.
- The knife is sharp and set with the right clearance.
- Nothing binds in the crank.

## Using the app from anywhere

The machine keeps one connection open to a free MQTT cloud server (for example a HiveMQ Cloud *Serverless* cluster). The online app connects to the same server.

1. Create the cluster and its credentials (guide, section 10a).
2. Enter them on the app's **Wi-Fi** tab while you are on the same Wi-Fi as the machine.
3. Open https://sri-automation.github.io/strip-cutter/ on any phone, choose **From anywhere**, and enter:
   - the cloud details;
   - the machine ID shown on the Wi-Fi tab;
   - the machine password.

**Copy setup link for another phone** on the Wi-Fi tab makes a link to this page that fills in everything except the passwords. The page itself holds no passwords; each phone keeps its own.

## Safety

- Fit a latching emergency-stop switch in the wiper motor's 12 V supply. The STOP button and the app's stop are software.
- When someone is working at the machine, set **Wi-Fi & remote → Remote control** to OFF on the machine. Phones can then only watch and stop it.
