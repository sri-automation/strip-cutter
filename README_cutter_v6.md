# Cutter v6: plywood demo shear driven by the wiper motor

All files are in `Documents\Strip_Cutter\v3`:

| What | File |
|---|---|
| Drilling templates (print at 100 %) | `Cutter_v6_templates_1to1_A4.pdf`: p1 main plate, p2 lever, p3 link + crank fitting, p4 base layout |
| Print files | `print_STL_cutter_v6\` (5 parts, plate 5 in your Bambu project) |
| Arduino sketch | `firmware\FeedCutDemo\FeedCutDemo.ino` |
| Wiring | `v6_wiring.png` |
| Pictures | `v6_cutter_drive_iso.png`, `v6_cutter_drive_front.png`, `v6_cutter_drive_back.png` |
| CAD | Fusion doc **Strip Cutter v3 (feeder)**. Joint J10 drives the crank, and the whole linkage follows. Scripts are in `cad\build6.py` |

## How it works
- **Bed knife.** The fixed blade is screwed to the front of the vertical plywood plate. Its sharp edge sits level with the net channel floor.
- **Moving knife.** The second blade is on a plywood lever that pivots on an M8 bolt 45 mm to the left of the net.
- **Drive.** The wiper motor is bolted to the back of the same plate, on the stepper side. Its shaft comes through to the front. A printed crank (radius 13.3 mm) pulls the lever through a plywood link, 103.4 mm between hole centres.
- **One cut per turn.** One crank turn is one cut: open at 27°, closed at 10°, then open again, in 2 s at 30 rpm.
  - The net is actually cut between lever angles of 17° and 11.5°. That is near the end of the stroke, where the crank has the most leverage.
  - The motor torque needed is about 0.7 N·m for every 100 N of cutting force.
- **Park switch.** A roller microswitch is pressed by the crank tip when the knife is fully open. The Arduino feeds, runs the motor for one turn, and stops it when the switch clicks.
  - The worm gearbox is self-locking, so the knife stays open while the motor is stopped.
  - The knife is practically still for ±30° of crank around the open point: the lever moves less than 1.2° there. So the exact stopping point doesn't matter.
- **Checked in Fusion.** The full crank turn was checked every 15–45°. Nothing collides.
- **Speed.** A cycle takes about 2.8 s (feed 75 mm + cut + 0.3 s pause), which is about 1,250 pieces an hour.

## Print: plate 5 (32 g, 1 h 39 min, blue PETG, no supports)
| Part | Notes |
|---|---|
| c6_Lever_Pivot_Hub | 2 × 688ZZ press in, one from each end |
| c6_Lever_Drive_Boss | **Now 12.6 mm tall** (changed today). The M8 bolt head fits the hex pocket |
| c6_Crank | Fits the 10 mm motor shaft. M8 head pocket at the back, M4 nut slot at the side |
| c6_Bed_Knife_Ledge | Holds the bed knife height; 3 slotted screw holes |
| c6_Knife_Height_Gauge | Prints lying on its end |

The crank is sized from two estimates:
- the shaft tip stands **29 mm above the flat tops of the 3 bosses**;
- the slot in the shaft runs **from about 13 to 19.5 mm from the shaft end**.

If your measurements differ, tell me before printing and I'll adjust the crank. The other 4 parts don't depend on these numbers.

## Plywood (8 mm)
| Part | Size | Template |
|---|---|---|
| Main plate (vertical) | 240 × 120 | p1 |
| Base board | 285 × 275 | p4 (layout drawn at half size) |
| Lever | about 130 × 55 | p2 |
| Link | 126 × 22 | p3 |

## Hardware to buy
**Lever pivot**
- 1 × M8×60 hex bolt, 1 × M8 nut, 1 × M8 nylock nut
- 1 × M8 large (fender) washer, 2 × M8 plain washers
- 2 × rubber washers for M8, about 3 mm thick (these give the knife preload)
- 2 × 688ZZ bearings (8 × 16 × 5)

**Knives**
- Moving knife: 2 × M4×12 cap screws + 4 × M4 washers
- Bed knife: 2 × wood screws 3.5×12 + 2 × M6 washers, through the blade's U-slots
- Ledge: 3 × wood screws 3.5×12

**Hub and drive boss:** 6 × wood screws 3.5×12

**Plate to feed frame:** 2 × M4×20 flat (countersunk) head screws

**Drive**
- 2 × M8×45 hex bolts (lever pin and crank pin)
- 2 × M8 nylock nuts, 4 × M8 washers
- 3 × M6×20 flat (countersunk) head bolts into the gearbox bosses. First check that an M6 screw goes at least 10 mm into a boss; if the thread is shorter, use M6×16.
- 1 × M4×10 grub screw + 1 × M4 nut (crank set screw)
- 1 × M4×6 screw + 1 × M4 washer with about 12 mm OD (keeps the crank on the shaft). The shaft's thread is only 5 mm deep, so the screw must not bottom out; add a washer if it does.

**Base**
- 3 × L-brackets (you have these) + wood screws
- 4 × wood screws about 4 × 10–12 mm, for the feed frame

**Electronics**
- 1 × roller-lever microswitch (KW11 / SS-5GL type, about 20 × 10 × 6 mm) + 2 × M2×16 screws with nuts, or 2 small wood screws
- 1 × 5 V relay module, 10 A
- 1 × 1N5408 diode (a 1N4007 will do)
- 1 × 5 A fuse and holder
- Hook-up wire
- A 12 V supply of at least 3 A for the wiper. If your TB6600 supply is 12 V and 5 A, you can share it.

## Build

### A. Cut and drill the plywood
1. **Print the templates and check the scale bar measures exactly 100 mm.** Tape each template on the plywood. Cut the outlines and the window in the main plate.
2. **Main plate holes:**
   - pivot 8.2 mm;
   - motor shaft 15 mm;
   - 2 × 4.5 mm for the feed frame, countersunk on the **front** face.
   - **Don't drill the motor bolt holes yet** (step E).
3. **Lever:**
   - pivot hole 16–17 mm (it clears the M8 nut behind it);
   - 2.5 mm pilots for the hub.
   - The drive-boss pilots must be **no more than 6 mm deep**, because the knife sits behind one of them.
4. **Link:** 2 × 8 mm holes, 103.4 mm apart, square to the face. Anything from 103 to 104 mm is fine.

### B. Plate and base
1. **Stand the plate on the base** on the line shown on p4: back face 127 mm from the entry-side edge, left end 30 mm from the board edge.
2. **Fit the 3 L-brackets** on the front (knife) side.
3. **Push the feed frame against the back of the plate** with the exit-guide nose centred in the window.
   - Fit 2 × M4×20 flat heads from the front into the frame.
   - Fit 4 wood screws through the frame's counterbored holes into the base.
4. **The old demo exit tie plate is no longer used.** The plywood plate replaces it.

### C. Bed knife (fixed)
1. **Hold the blade against the plate**, bevel toward the plywood, sharp edge up, in the dashed outline on p1.
2. **Mark the 2 screw holes through the U-slots** and drill 2.5 mm pilots. Fit the screws with M6 washers, just snug.
3. **Hold the printed ledge under the blade.** Mark and pilot its 3 slots, then fit the screws loosely.
4. **Set the height with the gauge:**
   - Slide the gauge's tongue into the exit channel from the front.
   - Push the ledge (and blade) up until the blade edge touches the underside of the gauge.
   - Tighten the ledge screws, then the knife screws, and remove the gauge.
   - The edge is now level with the channel floor, so the net slides over it without catching.

### D. Moving knife and lever
1. **Clamp the second blade on the back of the lever** (see p2): bevel against the wood, sharp edge down, 7 mm below the lever's straight edge, 10 mm from the pivot centre.
2. **Mark the 2 threaded holes through the blade** and drill 4.5 mm. Fit M4×12 with 2 washers each from the front.
   - The screw tips must not stick out past the blade's flat face.
3. **Hub:**
   - Press the two 688ZZ bearings into the printed hub.
   - Screw the hub to the lever front with its flange on the wood (3 × 3.5×12).
4. **Drive pin:** put the M8×45 in the drive boss with its head in the hex pocket, then screw the boss to the lever (3 × 3.5×12). The thread points outward.
5. **Pivot:**
   - Fit the M8×60 from the back with the large washer and run it through the plate.
   - Tighten the M8 nut firmly on the front face. This clamps the bolt to the plate.
   - Slide the lever on so the bolt passes through both bearings. Then fit washer, rubber washer, rubber washer, washer, nylock.
6. **Preload:** tighten the nylock until the moving knife just presses on the bed knife. The lever should swing by hand with a light, even drag.
7. **Paper test:** close the lever by hand on a strip of paper at the left, middle and right of the net channel. A clean cut everywhere means the blades are aligned.
   - If the paper folds at one end, add a little preload.

### E. Motor
1. **Check the M6 depth.** Screw an M6 into each boss by hand and check it goes at least 10 mm deep.
2. **Offer the motor up behind the plate** with the shaft through the 15 mm hole. Point the body **up and away from the stepper**.
   - This is the natural position: one boss points straight at the right-hand edge of the plate.
   - The gearbox must clear the stepper by at least 5 mm.
3. **Mark the bolt holes from the motor itself.** Dab paint or marker on the 3 boss tops and press the motor against the plate. The dots are the real hole centres; my template positions assume the bosses are evenly spaced around the shaft.
   - Drill 6.5 mm and countersink the **front** face.
   - Bolt the motor on with 3 × M6×20 flat heads. The heads must be flush, because the crank passes 1.5 mm in front of them.

### F. Crank
1. **Push an M8×45 through the crank** from its flat back face. The head sits in the hex pocket.
2. **Slide the M4 nut sideways into its slot** and start the M4×10 grub screw.
3. **Slide the crank onto the shaft**, flat side toward the plate, until the hub face is **flush with the shaft end**.
   - If the crank's back face reaches the plate before that, the shaft is shorter than I assumed. Tell me the numbers and I'll send a corrected crank.
4. **Turn the crank until the grub screw drops into the slot on the shaft**, then tighten it. There should be about 1.5 mm of gap to the plate.
5. **Fit the M4×6 and the 12 mm washer into the shaft end.** Snug only.

### G. Link
1. **On each M8 pin, stack:** boss, M8 washer, **link**, M8 washer, nylock.
2. **Tighten the nylock until the link just can't wobble,** then back it off 1/6 turn so the link turns freely. A smear of grease in both holes helps.
3. **To join them:**
   - Put the link on the crank pin first.
   - Swing the lever by hand until the link's other hole lines up with the lever pin.
   - This works at any crank angle, so there is no timing to set.
4. **The link must clear the screw head on the shaft end by 1–2 mm.** If it rubs, add one more washer under the link on **both** pins.

### H. Park switch and wiring
1. **Wire everything as in `v6_wiring.png`:**
   - Relay IN to D8. The relay switches the +12 V to the wiper.
   - The diode goes across the motor, with the stripe on the + wire.
   - Switch COM to GND, NO to D9.
2. **With the Arduino on USB and the 12 V connected, run the crank from the Serial Monitor:** `R1` starts it and `R0` stops it. Stop it with the crank pointing at the lever pin, which is the knife fully open.
3. **Place the switch on the plate** at the dashed position on p1 so the crank tip pushes its roller in by about 2 mm (you hear it click).
   - Pilot and screw it down.
   - Send `W`: it should say **PRESSED**.
4. **Run a few turns with `R1`/`R0`.** The switch should click once per turn.

## First run (FeedCutDemo)
1. **Upload `FeedCutDemo.ino`.** Open the Serial Monitor at 115200 baud with "Newline" line endings. Your old feeder calibration `C` is kept.
2. **`W`** shows the switch state; press the switch by hand to see it change.
3. **`H`** homes: the motor runs until the knife is open.
4. **`K`** does one cut with no net loaded. Watch it close and stop open.
5. **Load the net** through the feeder until it just reaches the knife.
6. **Cut a test batch:**
   - `L75` sets the piece length.
   - `K` squares the end.
   - `Q5` then `G` cuts 5 pieces.
   - `X` stops after the current piece. The button on D11 also starts and stops.
7. **Other settings:**
   - `P` is the pause after each cut (ms).
   - `B` is the run-on after the click, 0–200 ms, which changes where the crank stops.
   - `T` is the jam timeout.

## If something is wrong
| What you see | What to do |
|---|---|
| `FAULT: switch never released` | The motor didn't turn. Check the relay: if it clicks the wrong way, set `RELAY_ACTIVE_LOW = false` in the sketch. Also check the 12 V and the fuse. |
| `FAULT: knife did not come back open` | Jam or stall. Check whether the net is stuck between the blades, the preload is too high, or the knife is dull. |
| Stops with the knife only nearly open | Raise `B` in 20 ms steps. |
| Net not cut through at one edge | Redo the paper test, then add preload or re-square the moving knife. |
| Link rubs the shaft screw | Add 1 washer under the link on both pins. |
| Switch roller catches badly | Swap the two motor wires; either direction works. |

**Safety:** the crank is strong and the blades are sharp. Unplug the 12 V before putting fingers near the knife. Fit a clear guard over the knife before regular use.
