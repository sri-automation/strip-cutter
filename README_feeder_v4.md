# Feeder v4: fixes for twists, roller tilt and frame flex

The files are in `Documents\Strip_Cutter\v3`:
- STLs in `print_STL_feeder_v4`
- CAD in `cad` (`build3.py`, `Strip_Cutter_v4.step` / `.f3d`)

The Fusion document is **Strip Cutter v3 (feeder)**. It now shows the v4 feeder with your 628 top roller.

## What changed and why

| Problem you saw | Fix |
|---|---|
| Twisted net jams in the entry guide; the roof was stringy | The entry guide is now an **open trough** with no roof, so twists pass freely and there is nothing to snag. The mouth is 28 mm wide and tapers to 13.2 mm. All the lead-in edges are chamfered (floor lip 3 mm, wall lips 2 mm, wall tops 1.2 mm). |
| Net jams in the exit guide | The channel is now **13.2 × 6.2 mm** (it was 12.8 × 3.0). That passes a net twisted up to about 5.5 mm. The entry from the rollers is a two-stage funnel (14.8 × 8.7 mm tapering down), and the exit end is flared. |
| Top roller lifts on the motor side | The single arm is replaced by a **yoke**: two side plates joined by a bar over the roller. It pivots on a full-width tube that is supported on **both** sides, by the wall and by a new pivot bracket on the motor wall. The M8 axle head sits in a hex pocket in the motor-side plate. |
| Top of the frame flexes | 1. The **pivot rod** (M5×45 through a clamped sleeve) ties the arm-side wall to the bracket and motor wall at the entry end. <br>2. The **exit tie plate** ties both walls at the exit end (demo only; in the full machine the aluminium main plate does this job). |
| Top roller | Back to the **628 version you already assembled**. It is not reprinted. |

**Checks run in Fusion:** clearances were checked with the gap at 0.27, 0.5, 2, 4 and 5.3 mm. There were no collisions. The only contacts are the designed ones:
- the gap-stop screw landing on its column;
- the rubber washers compressing as the arm lifts;
- the self-tapping screws cutting their thread.

## Print tonight (plate 3 in your Bambu project)
- **Parts:** pinch yoke, pivot bracket, pivot sleeve, entry guide v4, exit guide v4, exit tie plate.
- **Estimate:** 88 g of blue PETG and about 4 h 20 min.
- **Settings:** 5 walls, 40% infill.
- **Supports:**
  - Tree supports on the yoke, between its two side plates, under the motor-side plate.
  - A small tree under the entry-guide tongue.
  - Remove both with pliers and clean the face around the axle hole.

## Reuse from what you have
- **Kept as they are:** frame, drive roller, 628 top roller and bearings, knob, rubber washers, M8×40 with nylock and 2 washers, M4×40 with nut and washer, M4×25 gap stop with lock nut, the 2 × M4×12 of the entry guide, and the lower M4×20 of the exit guide.
- **The old M5×25 pivot bolt moves** to the top stepper bolt on the entry side. It replaces the M5×20 there, because it now also clamps the bracket.
- **Now spare:**
  - Retired prints: the old arm and both old guides.
  - Hardware: the M5 nylock, the upper M4×20, and one M5×20.

## Buy (small hardware shop)
| Qty | Part | Where it goes |
|---|---|---|
| 1 | M5×45 hex bolt | Pivot rod. **It must be 45.** A 50 hits the motor wall. You can also cut an M5×50 down to 45. |
| 1 | M5 plain nut | Sits in the hex pocket of the pivot bracket |
| 1 | M4×16 | Upper exit-guide screw. The new hole is shorter, so an M4×20 will not seat. |
| 2 | M4×12 | Exit tie plate |

## Assembly (about 25 min)
1. **Strip down.**
   - Remove the knob, the pressure bolt, the gap-stop screw and the M5 pivot.
   - Lift out the arm and the roller, then take the roller off the M8.
   - Remove the old entry guide (2 × M4×12) and the old exit guide (2 × M4×20).
2. **Pivot bracket.**
   - Take out the **upper stepper bolt on the entry-guide side** only; the other 3 hold the motor.
   - Drop the plain M5 nut into the hex pocket on the bracket's flat face.
   - Put that flat face against the **inside** of the motor wall. The big round boss goes up at the wall's top corner, in line with the pivot hole in the opposite wall.
   - Bolt it with the **M5×25**. The head goes in the bracket's counterbore; the washer and nut go behind the motor flange as before.
3. **Exit guide v4.**
   - Fit it as before.
   - Put the **M4×20** in the lower hole and the **M4×16** in the upper hole. Both go in from outside the motor wall.
4. **Entry guide v4.** Snap off the tongue support, then fit it with the same 2 × M4×12 into the slab.
5. **Yoke on the bench.**
   - Drop the M8×40 **head into the hex pocket** on the yoke's motor-side plate, so it sits below the surface.
   - Thread on, in this order: washer → 628 roller → washer → through the arm-side plate → M8 nylock.
   - Tighten until the roller has no side play but still spins freely.
   - Screw in the gap-stop M4×25 with its lock nut, as before.
   - Slide the printed sleeve into the yoke's pivot tube.
6. **Yoke into the frame.**
   - Lower it in. The nylock drops into the wall slot, and the tube lines up between the wall and the bracket.
   - Push the **M5×45 with a washer** from outside the wall, through the sleeve, into the nut in the bracket.
   - Tighten it **firmly**. It clamps the sleeve, which ties the frame, and the yoke still swings freely on the sleeve.
   - Check that the yoke drops under its own weight.
7. **Pressure knob and gap stop.** These are the same as before.
   - Knob stack, from top down: M4 washer, 3 rubber washers, yoke slot, nut in the column.
   - One turn of the stop screw changes the gap by about 1.2 mm.
8. **Exit tie plate.** Hold it on the exit end of the frame, around the exit-guide nose, and fix it with 2 × M4×12 into the two small holes in the ends of the walls.

## Setting the grip
These steps are the same as before.
1. Set the gap to about 1 mm with no net loaded.
2. Try 0.5 to 1.5 mm with the real net.
3. Tighten the knob until a pulled net doesn't slip, then add half a turn.

With both ends of the roller now held, the pressure should be even across the net. If one edge still slips, check that the M5×45 is tight and that the yoke swings without binding.

## Notes for the final PETG-CF build
- Every v4 part prints unchanged in PETG-CF. It needs a hardened nozzle (0.4 or 0.6 hardened steel).
- The optional strip-end microswitch no longer has a place on the open entry guide. It can go on the outer trough wall later if you want it.
