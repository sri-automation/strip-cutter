# Feeder v5: keep the net centred through the rollers

The files are in `Documents\Strip_Cutter\v3`:
- STL: `print_STL_feeder_v5\v5_1_Exit_Guide.stl` (use this one; `v5_Exit_Guide.stl` is superseded)
- CAD: `cad\build3.py`
- Picture: `v5_exit_guide_iso.png`

The Fusion document is **Strip Cutter v3 (feeder)**, saved as "feeder v5".

## What was wrong
- **The net can walk sideways.** Between the end of the entry guide (x −60) and the start of the exit channel (x −33), nothing held its edges. That is 27 mm with the nip in the middle.
- **Why it walks to one side.** The top roller axle has some play in its printed holes. The knob and the gap stop both press on the wall-side arm only. Together these can leave the top roller a fraction of a degree skewed, and a skewed roller steers the net sideways like a conveyor roller.
- **Why it then locks up.** On the motor side, next to the drive-roller tread, there is an open pocket above the hub. Once the net edge passes the tread end at 7 mm, it drops into that pocket, gets dragged round the hub and jams.

## The fix: one new part, the v5 exit guide
The main body is the same as v4, with two **side cheeks** added. They reach back past the rollers to the entry guide.
- **Before and after the nip:** lips hold the net at **±6.6 mm**. That is 13.2 mm for the 12 mm net, the same width as the entry channel.
  - The lips run from the entry guide to about 4 mm before the nip.
  - They start again about 4 mm after the nip.
  - Both lip starts have a 45° lead-in, so the mesh can't hook.
- **At the nip:** flat ledges sit 0.5 mm beside each end of the drive tread, with walls at ±8.5 mm. The edge can no longer drop into the pocket or reach the hub.

**Clearance checks in Fusion, gap 0.27 to 5.3 mm:**
- 0.45 mm to the drive teeth.
- 0.5 mm to the top roller at its lowest.
- Clear of the hub, the M3 screw, the washers, both yoke plates, the entry tongue, the columns and the gap-stop screw.

**Nothing else changes.** All the other v4 parts and all hardware stay as they are. The same 2 screws hold it: M4×20 lower, M4×16 upper.

## Print (plate 4 in your Bambu project)
- **v5_Exit_Guide:** printed upright, about **18 g** and **1 h 06 min**.
- **Settings:** 5 walls; thin-wall detection on.
- **Supports:**
  - Small tree supports "on build plate only", under the motor-side cheek arch and under the nose.
  - Snap them off. Nothing needs cleaning on the faces the net touches.

## Swap it in (about 15 min)
1. **Lift out the yoke.**
   - Remove the knob with its M4×40, then pull the M5×45 pivot rod.
   - Lift the yoke and top roller out. The M8 nylock slides up out of the wall slot.
2. **While the yoke is on the bench, tighten the M8 nylock firmly.** It only clamps the bearing inner rings, so the roller still spins freely. This stops the axle shifting or skewing in its holes, which is the main cause of the drift.
3. **Remove the old guide.** Take off the exit tie plate (2 × M4×12), then the old exit guide (2 screws from outside the motor wall).
4. **Set the drive roller position.** The hub face must be **1.5 mm from the motor wall**. Use an M8 washer (1.6 mm) as a feeler.
   - Loosen the M3 screw, slide the roller, then tighten.
   - This centres the tread between the new ledges.
5. **Drop in the v5 exit guide from above.**
   - The wall-side cheek goes down beside the drive roller.
   - The motor-side cheek arches over the hub.
   - Push it onto the tie wall against the motor wall, then fit the M4×20 (lower) and M4×16 (upper) from outside.
6. **Spin the drive roller by hand.** Nothing should rub. If a tread end touches a ledge, redo step 4.
7. **Refit everything else.** Yoke, pivot rod (tight), knob, then the tie plate.
8. **Load the net.**
   - Loosen the knob and lift the yoke.
   - Push the net through the entry guide, between the cheek lips and into the channel.
   - Retighten the knob.

## Settings that reduce drift further
- Use the **least knob pressure** that feeds without slip. Too much pressure on the wall side tilts the roller.
- **Set the gap with the net loaded (0.5–1.5 mm).** Check that the top roller sits level: look along the nip against a light, and both ends should show the same gap.
- **Keep the pivot rod firm.** The yoke should still drop under its own weight.

## v5.1 (27 Sep): the top roller couldn't reach the drive roller
**Cause.** With the rollers touching, the v5 cheeks cleared the parts above them by very little:
- 0.2 mm to the top roller;
- 0.2 mm to both yoke plates;
- 0 mm with 18 mm OD M8 washers, and 1.45 mm of overlap with 20 mm OD washers.

Shop washers are often bigger than the standard 16 mm, so the washers or the yoke landed on the cheek tops before the rollers touched.

**Fix.** v5.1 lowers the cheek tops. With the rollers touching, it now clears:
- the top roller by 0.55 mm;
- 20 mm OD washers by 0.7 mm or more;
- the yoke by 1.2 mm.

The top roller can also press 0.5 mm into the drive roller and everything else still clears. The lips now hold the net at ±6.6 up to about 6 mm from the nip on each side (it was 4 mm).

**Print.** Plate 4 now holds `v5_1_Exit_Guide.stl`: 18 g, about 1 h 05 min, same settings.

**Fitting.** Same steps as v5. For the rollers to touch, also back the gap-stop screw off. That is the M4×25 in the arm above the small column: loosen its lock nut and turn it up two turns.
