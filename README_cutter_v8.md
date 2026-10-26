# Cutter v8: corrected after the template and coupon test

Everything is in `Documents\Strip_Cutter\v3`:

| What | Where |
|---|---|
| Bambu project (3 plates, sliced, not started) | `print_STL_cutter_v8\Strip_Cutter_v8_PETG-CF_0.6_nozzle.3mf` |
| STL files | `print_STL_cutter_v8\` |
| Pictures | `v8_printed_cutter_front.png`, `v8_printed_cutter_back.png` |
| CAD | Fusion doc **Strip Cutter v3 (feeder)**; script `cad\build8.py` |

The v7 lever, link, crank, ledge, spacers and pinch yoke are replaced by the v8 ones. Keep the motor template and the knife height gauge; they are unchanged.

## What your measurements changed
| You measured | I had assumed | Change |
|---|---|---|
| Shaft tip 32.88 mm above the template (35.28 mm above the bosses) | 29 mm above the bosses | The main plate now has three raised pads, 6.3 mm high, on its back. The motor sits on them, so the shaft tip still ends 21 mm in front of the plate. |
| Shaft slot from 4 to 16 mm from the end | 13 to 19.5 mm | The crank's set-screw slot moved; the screw now lands mid-slot, about 10 mm from the shaft end. |
| All three M6 screws start | | Hole pattern kept as it was. |
| Bearing, shaft and M8 bolt all too tight | | Every printed hole and nut pocket is larger (table below). |

## New hole sizes
| Feature | v7 | v8 |
|---|---|---|
| 688ZZ bearing seat | 16.2 | 16.4 |
| Crank bore (10.07 shaft) | 10.35 | 10.6, with a lead-in chamfer |
| M8 clearance / hex pocket for the head | 8.3 / 13.3 | 8.7 / 13.7 |
| M6 clearance | 6.6 | 6.9 |
| M5 clearance / nut pocket | 5.5 / 8.2 | 5.8 / 8.5 |
| M4 clearance / nut pocket | 4.4 to 4.5 / 7.2 | 4.8 / 7.5 |
| Hole an M4 grub screw threads into | 3.5 | 3.7 |

## Plates
Settings are unchanged: A1, 0.6 nozzle, Generic PETG-CF, 0.30 mm Strength, 4 walls, 40 % gyroid.

| Plate | Parts | Filament | Time |
|---|---|---|---|
| 1 | Graded fit gauge | 15 g | 39 min |
| 2 | Main plate + 3 front brackets | 258 g | 8 h 26 min |
| 3 | Knife lever, link, crank, bed-knife ledge, 3 pin spacers, pinch yoke (tree supports on the yoke) | 106 g | 3 h 51 min |

**Print plate 1 first and check it before the other two.**

## Reading the fit gauge
One corner is cut off. That corner marks the smallest holes; sizes grow as you move away from it.

| Row | Holes, starting at the cut corner | Used in the parts |
|---|---|---|
| Big holes | 16.3, 16.4, 16.5, 16.6 | 16.4 |
| Small holes | 10.5, 10.6, 10.7 | 10.6 |
| Same row, next | M8 hole 8.7 with a 13.7 hex pocket on top | as is |
| Same row, next | M6 hole 6.9 | as is |
| Last two, small | 3.7 (nearer the big holes) and 4.8 (nearer the edge) | as is |

What to look for:
- **Bearing:** the right hole takes a 688ZZ with firm thumb pressure or a light squeeze in a vise, and holds it.
- **Shaft:** the right hole slides on the motor shaft with no wobble.
- **M8 bolt:** passes freely and its head drops into the hex pocket.
- **M6 and M4 screws:** pass freely through the 6.9 and 4.8 holes.
- **M4 grub screw:** cuts its own thread in the 3.7 hole and holds.

If the bearing fits the second big hole and the shaft the second small hole, print plates 2 and 3 as they are. Otherwise tell me which holes fit and I'll change the parts.

## One check on the motor before plate 2
Look at the motor from the shaft end with the motor body pointing up. The gearbox housing must not reach further than **42 mm to the left** of the shaft centre (the stepper is there) or **40 mm below** it (the base board is there). I assumed 34 mm for both. The plate has no feet or ribs behind the gearbox, so those are the only two limits.

## Hardware
| Item | Qty | Used for |
|---|---|---|
| 688ZZ bearing (8 × 16 × 5) | 6 | 2 in the lever hub, 4 in the link |
| M8 × 60 hex bolt | 1 | Lever pivot, head in the plate's hex pocket |
| M8 nut | 1 | Clamps the pivot bolt to the plate |
| M8 × 45 hex bolt | 2 | Lever drive pin, crank pin |
| M8 nylock nut | 3 | Pivot, two link pins |
| M8 washer | 4 | 2 at the pivot, 1 on each link pin |
| Rubber washer, 8 mm hole | 2 | Knife preload at the pivot |
| M6 × 20 countersunk | 3 | Motor to the plate |
| M6 × 12 button head + washer + nut | 2 | Bed knife |
| M5 × 16 + washer + nut | 3 | Front brackets to the plate |
| M5 × 40 cap screw + washer + nut | 1 | Pinch yoke tie bolt |
| M4 × 16 countersunk | 2 | Plate to the feed frame |
| M4 × 16 pan or button head + 2 washers + nut | 3 | Bed-knife ledge |
| M4 × 10 cap screw + 12 mm washer | 2 | Moving blade clamp |
| M4 × 12 grub screw | 4 | 3 blade stops, 1 crank set screw |
| M4 nut | 1 | Crank set screw |
| M4 × 6 screw + 12 mm washer | 1 | Shaft end |
| Wood screw, 4 mm countersunk | 5 | 2 plate feet, 3 brackets; length to suit your base board |
| Small self-tapping screw, about 2.2 × 13 | 2 | Park switch |

## Fitting notes
- **Motor:** the M6 × 20 heads sit 2 mm below the plate's front face, so 7.7 mm of thread goes into each boss. If a screw bottoms out before it is tight, put an M6 washer between each pad and boss.
- **Nuts in the back of the plate:** put the three M5 bracket nuts, the two M6 bed-knife nuts and the three M4 ledge nuts in their pockets before the plate goes on the feeder, and hold them with tape. The stepper and the feed frame cover some of them afterwards.
- **Ledge:** use both washers under each screw head; with one, the screw nearest the pivot touches the feed frame.
- **Crank:** drop the M4 nut into the channel from the hub end, start the grub screw through the side slot, slide the crank on with the arm toward the plate, and tighten the screw into the shaft slot.
- **Shaft-end screw:** the thread is only 5 mm deep. If the M4 × 6 bottoms out, add a second washer.
- **Blade on the lever, link pins, bearings, pinch yoke:** as in `README_cutter_v7.md`.
