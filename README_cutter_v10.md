# Cutter v10: gap filler plate

Stops the net climbing into the gap between the main plate and the upper (moving) blade.

Everything is in `Documents\Strip_Cutter\v3`:

| What | Where |
|---|---|
| Bambu project (1 plate, sliced, not started) | `print_STL_cutter_v10\Strip_Cutter_v10_gap_filler_PETG-CF_0.6_nozzle.3mf` |
| STL files | `print_STL_cutter_v10\` |
| Where to drill | `v10_gap_filler_where_to_drill.png` |
| CAD | Fusion doc **Strip Cutter v3 (feeder)**, component `C10_Gap_Filler_PRINT`; script `cad\build10_filler.py` |

## Plate
A1, 0.6 nozzle, Generic PETG-CF, 0.30 mm Strength, Textured PEI plate, top shell layers 5 (prints solid). 8.7 g, 24 min.

| Part | Thickness | Use |
|---|---|---|
| Filler, square corners | 2.4 mm | Fit this one |
| Filler, one corner cut off | 2.1 mm | Spare, only if the upper blade rubs on the 2.4 mm one |

Both print with the countersinks facing up.

## Fitting
1. Take the lever and upper blade off (one M8 nylock nut at the pivot).
2. Hold the filler flat on the front of the main plate, countersinks facing you, tongue pointing down. The tongue's bottom edge sits level with the roof of the net opening and is centred on the opening. Tape or clamp it.
3. Drill 5 mm through the main plate at both holes, using the filler as the template. Hole centres land 28 mm below the plate's top edge, 36 mm left and 26 mm right of the net centre.
4. Fix with 2 x M4 x 16 countersunk screws from the front, washer and nut behind the plate. The left nut is beside the feed frame, the right one is above it.
5. Check both screw heads are below the filler's face. If one stands proud, deepen the countersink by hand with an 8 to 10 mm drill bit.
6. Refit the lever. The blade should pass the filler without rubbing (0.5 mm clearance by design).

## Hardware
| Item | Qty |
|---|---|
| M4 x 16 countersunk screw | 2 |
| M4 washer | 2 |
| M4 nut (nylock if you have them) | 2 |

## Shims (added 7 Oct): the real gap is wider than 2.4 mm
The 2.4 mm filler left a gap and 2.4 + 2.1 mm was too thick, so the real gap is between the two. Three shims set the total in 0.3 mm steps.

Project: `print_STL_cutter_v10\Strip_Cutter_v10_filler_shims_PETG-CF_0.6_nozzle.3mf` (5.3 g, 18 min).

| Shim | Mark on the top edge |
|---|---|
| 0.6 mm | 1 notch |
| 0.9 mm | 2 notches |
| 1.2 mm | 3 notches |

Shims go behind the filler, against the main plate. The countersunk filler stays at the front.

| Total | Stack |
|---|---|
| 2.7 mm | 2.1 filler + 0.6 |
| 3.0 mm | 2.4 filler + 0.6 |
| 3.3 mm | 2.4 filler + 0.9 |
| 3.6 mm | 2.4 filler + 1.2 |
| 3.9 mm | 2.4 filler + 0.6 + 0.9 |
| 4.2 mm | 2.4 filler + 0.6 + 1.2 |

Use the thickest stack that lets the upper blade pass without rubbing over the whole stroke. M4 x 16 screws are long enough up to 4.2 mm.

## Filler v2 (7 Oct): one piece, 3.3 mm, with side walls
The 2.4 + 0.9 mm stack stopped the net going up, but it still escaped left or right. Filler v2 replaces the stack.

- One solid plate, 3.3 mm thick, same two M4 countersunk holes. No new drilling.
- The net leaves through a window: roof as before, plus a wall on each side that reaches down to the fixed blade, and a low sill in the fixed blade's bevel pocket.
- Window is 16 mm wide and about 6.6 mm high.

Project: `print_STL_cutter_v10\Strip_Cutter_v10_filler_v2_3.3mm_PETG-CF_0.6_nozzle.3mf` (8.1 g, 23 min). STL: `c10_Gap_Filler_v2_3.3mm_side_walls.stl`. Picture: `v10_filler_v2_front_view.png`. Script: `cad\build10_filler2.py`.

Fitting: take off the old filler and shim, fit v2 with the same screws, countersinks facing you. If the two pointed bottom corners touch the fixed blade and the plate will not sit flat, file them back. Turn the crank by hand through one full cut before switching on.
