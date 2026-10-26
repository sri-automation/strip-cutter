# Cutter v11: exit guide extension nozzle

The printed exit guide on the machine ends about 10 mm behind the front face of the fixed blade, and the fixed blade edge stood higher than the guide's floor. The net crossed an open pocket (the window in the main plate plus the gap in front of it) and then met a step, so it could escape in every direction. The nozzle closes that pocket in one piece. It replaces the gap filler and the shims.

Everything is in `Documents\Strip_Cutter\v3`:

| What | Where |
|---|---|
| Bambu project (1 plate, sliced, not started) | `print_STL_cutter_v11\Strip_Cutter_v11_exit_nozzle_PETG-CF_0.6_nozzle.3mf` |
| STL | `print_STL_cutter_v11\c11_Exit_Nozzle_3.3mm.stl` |
| Picture | `v11_exit_nozzle_side_view.png` |
| Model script (Python, manifold3d; not in the Fusion document) | `cad\build11_exit_nozzle.py` |

## Plate
A1, 0.6 nozzle, Generic PETG-CF, 0.30 mm Strength, Textured PEI plate, top shell layers 8. 9.1 g, 26 min. Prints with the blade-side face on the bed and the tube pointing up, no supports.

## What it is
- Tube, 5.5 mm long, goes back through the main-plate window to the end of the exit guide. Outside 17.4 x 11.6 mm (window is 20.4 x 16).
- Flange in the gap, 3.3 mm thick, same two M4 countersunk holes as the gap filler.
- Channel narrows from 15.2 x 8.0 mm at the back to 14.0 x 4.8 mm at the front.
- Floor rises 1.5 mm along the nozzle and ends 0.5 mm above the fixed blade edge.
- Underside of the tip follows the 38 degree bevel of the fixed blade.

## Sizes I assumed (from your answers, not measured exactly)
| Item | Assumed | From |
|---|---|---|
| Front of the fixed blade, from the main plate face | 3.6 mm | further out than the 3.3 filler, less than 3.9 |
| End of the exit guide, from the main plate face | 6.4 mm behind it | 10 mm from the fixed blade front |
| Gap behind the upper blade | 3.3 mm flange fits | the 3.3 mm filler fitted, 0.6 mm more did not |

## Fitting
1. Take off the lever with the upper blade, the gap filler and any shim.
2. Loosen the fixed blade and its ledge and slide the blade down 2 to 3 mm.
3. Push the nozzle's tube into the window and screw the flange on with the two M4 x 16 countersunk screws. It must sit flat on the main plate.
   - If the tube stops against the exit guide before the flange is flat, file the tube's end shorter.
4. Slide the fixed blade up until its slope touches the underside of the nozzle tip, then tighten the blade and bring the ledge up under it.
5. Check the nozzle floor is level with or slightly above the fixed blade edge, never below it.
6. Refit the lever and turn the crank by hand through one full cut before switching on.
