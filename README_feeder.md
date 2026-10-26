# Feeder v3: assembly and first run

These files are in `Documents\Strip_Cutter\v3`. The Fusion document is **Strip Cutter v3 (feeder)**, and only the feeder parts are visible in it.

## Printed parts
- **Main plate** (blue PETG, about 6.5 h, 148 g): feed frame, entry guide, exit guide, pinch arm, pressure knob and two drive rollers. Your motor shaft is **6.35 mm**, so use **Drive_Roller_6.35mm_shaft**. The 6.00 mm roller is a spare.
- **Small second plate** (about 25 min): **Pinch_Roller_688** plus **Top_Roller_Spacer_x2** (print 2, or 3 to keep a spare). This replaces the top roller on the main plate, which was made for 628 bearings and has too thin a wall. Keep that one as a spare only.

## Hardware for the feeder
| Qty | Part | Where |
|---|---|---|
| 2 | 688ZZ bearing 8×16×5 | top roller |
| 1 | M8×40 hex bolt, 1 M8 nylock nut (no washers: the 2 printed spacers replace them) | top-roller axle |
| 4 | M5×20 bolt, 4 M5 nuts, 8 M5 washers | stepper to frame |
| 1 | M5×25 bolt, 1 M5 nylock nut, 1 M5 washer | pinch-arm pivot |
| 1 | M4×40 hex-head bolt, 1 M4 nut, 1 M4 washer, 3 rubber washers | pressure knob |
| 1 | M4×25 hex-head bolt, 1 M4 nut | gap-stop screw and its lock nut |
| 2 | M4×12 | entry guide into frame |
| 2 | M4×20 | exit guide, through the stepper wall |
| 1 | M3×8 screw (or grub screw), 1 M3 nut | drive roller onto motor shaft |

## Assembly (about 20 minutes)
1. **Clean up the prints.**
   - Snap off the small tree support under the entry-guide tongue.
   - If they are tight, run drills through these holes: 5.5 mm (arm pivot) and 8.5 mm (arm axle hole).
2. **Top roller.** Press one 688ZZ into each side of Pinch_Roller_688 until it stops against the centre web and sits flush with the face. Use a vise with two flat plates. They are a snug press fit.
3. **Nut in the frame.** Drop the M4 nut into the slot in the short column next to the pinch arm. The slot opens toward the rollers.
4. **Stepper and drive roller.**
   - Put the M3 nut into the slot in the roller hub.
   - Start the M3 screw 2 turns so the nut can't fall out.
   - Set the roller inside the frame with its hub facing the stepper wall.
   - Push the motor into the Ø38 pilot hole so the shaft goes into the roller.
   - Bolt the motor on with 4 × M5×20. The heads go on the roller side. The washers and nuts go behind the motor flange.
   - Slide the roller until the hub is about 1 mm from the wall. Turn the screw onto the flat of the shaft and tighten it.
5. **Guides.**
   - Set the entry guide on the frame base and fix it with 2 × M4×12 from the top.
   - Set the exit guide on the inner wall next to the stepper.
   - Fix the exit guide with 2 × M4×20 from the outside of the stepper wall. These screws cut their own thread in the plastic, so don't over-tighten.
6. **Pinch arm.**
   - Build the arm first on the bench, in this order: M8×40 bolt → printed spacer → top roller → printed spacer → arm → M8 nylock. The spacers touch only the bearings' inner rings, so the roller spins free.
   - Tighten the nylock until the roller has no side play but still spins freely.
   - Lower the arm into the frame from the top. The nylock drops into the slot in the frame wall, which stops it turning.
   - Fit the M5×25 pivot bolt from outside the frame, with a washer and nylock. Tighten only until the arm still drops under its own weight.
7. **Pressure knob.**
   - Press the knob onto the head of the M4×40 bolt.
   - Stack, from the top down: M4 washer, 3 rubber washers, arm slot, nut in the column.
   - Turn the knob until it just starts to grip.
8. **Gap stop.**
   - Screw the lock nut onto the M4×25 bolt.
   - Screw the bolt down into the small hole at the entry end of the arm, until its tip touches the frame column.
9. **Fixing down.** Clamp the base to the table with a C-clamp, or screw it to a plank using the 6 holes in the base.

## Setting the grip
- **Gap:** turn the stop screw. One turn changes the roller gap by about **1.2 mm**. The range is 0 to about 5 mm.
  1. With no net loaded, set the gap to about **1 mm** (a feeler gauge or a folded paper strip works).
  2. Lock the nut.
  3. Try 0.5 to 1.5 mm with the real net.
- **Force:** tighten the knob until a pulled net does not slip, then add half a turn. The rubber washers let the arm lift over thick spots.
- **Loading net:**
  1. Loosen the knob 2 turns and lift the arm.
  2. Push the net through the entry guide, between the rollers and into the exit guide.
  3. Tighten the knob again.

## Running the demo (FeederDemo.ino)
Wiring:
- **TB6600 to Arduino:** PUL+ → D5, DIR+ → D6, ENA+ → D7. Connect PUL-, DIR- and ENA- to GND.
- **Driver supply:** 12–24 V DC, 3 A or more.
- **Motor:** coils to A+/A- and B+/B-.
- **Start/stop button (optional):** between D11 and GND.
- **DIP switches:** SW1 OFF, SW2 ON, SW3 OFF (8 microsteps); SW4 ON, SW5 OFF, SW6 OFF (about 2 A).

Open the Serial Monitor at 115200 baud with "Newline" line ending. Commands:
- `L75`: piece length in mm
- `S200`: feed speed in mm/s
- `P1200`: pause between pieces in ms
- `Q10`: number of pieces
- `G`: go
- `X`: stop
- `J20`: jog forward 20 mm
- `?`: show settings

If the net moves backwards, swap A+ and A-.

**Calibration:**
1. Run `L100`, `Q10`, `G`.
2. Wait 1 minute, then measure the average piece length **A**.
3. Send `C` + (17.44 × 100 / A).
