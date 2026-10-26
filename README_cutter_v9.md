# Cutter v9: reprint plates, keyed crank, shaft keys, exit ramp

Everything is in `Documents\Strip_Cutter\v3`:

| What | Where |
|---|---|
| Bambu project (2 plates, sliced, not started) | `print_STL_cutter_v9\Strip_Cutter_v9_PETG-CF_0.6_nozzle.3mf` |
| STL files | `print_STL_cutter_v9\` |
| Pictures | `v9_ramp_front.png`, `v9_ramp_side.png` |
| CAD | Fusion doc **Strip Cutter v3 (feeder)**; script `cad\build9.py` |

## Plates
Settings: A1, 0.6 nozzle, Generic PETG-CF, 0.30 mm Strength, 4 walls, 40 % gyroid, **Textured PEI plate**.

| Plate | Parts | Filament | Time |
|---|---|---|---|
| 1 | Main plate | 215 g | 6 h 59 min |
| 2 | Keyed crank, 5 front brackets, exit ramp, 8 shaft keys | 107 g | 3 h 55 min |

The main plate has holes for 3 front brackets; the other 2 are spares. The keys print standing with a 5 mm brim.

## Exit ramp
- Slope 35 degrees. Its top lip sits 0.5 mm in front of the fixed blade and about 10 mm below the cut, under the moving blade's travel.
- Guide walls start 17 mm in front of the main plate, clear of the lever. One wall is vertical, the other leans out at 45 degrees so the part prints on its side without supports.
- It stands on the base on its own foot. Fix it with 2 wood screws through the ear on the motor side.
- It ends on top of the base, 75 mm in front of the main plate. Nothing goes below the base, so the base can be any length. Pieces slide off the end onto the base (or off its edge, if the edge is there).

## Keyed crank
- The hub now has a closed end. It seats on the end of the shaft and is held by an **M4 x 6 screw through the cap, no washer**.
- A printed key sits in the shaft slot and in a keyway in the hub.
- The M4 x 12 grub screw and its nut are kept. The screw now presses on the key, which takes out the play.
- Bore is still 10.7 mm.

Fitting order: key into the shaft slot, slide the crank on with the arm toward the plate, M4 x 6 into the shaft end, drop the M4 nut into the channel from the hub end, then tighten the grub screw onto the key.

## Shaft keys
I don't know the slot's width or depth, so there are four sizes, two of each. The longer the key's head, the wider its tongue.

| Head length | Tongue width | For a slot of about |
|---|---|---|
| 8.0 mm | 2.9 mm | 3.0 mm |
| 9.5 mm | 3.4 mm | 3.5 mm |
| 11.0 mm | 3.9 mm | 4.0 mm |
| 12.5 mm | 4.4 mm | 4.5 mm |

- Head: 5.0 mm wide, in a 5.5 mm keyway.
- Tongue: 7.5 mm long, 1.7 mm deep into the shaft.
- Use the widest key whose tongue goes into the slot. Sand the head or tongue lightly if it is tight.
- If no key fits, the grub screw can go straight into the shaft slot as before.

## Hardware changes from v8
| Item | Qty | Used for |
|---|---|---|
| M4 x 6 screw | 1 | Shaft end, through the crank cap (no washer now) |
| Wood screw, 4 mm countersunk | 2 more | Ramp foot |
