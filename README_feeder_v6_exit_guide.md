# Feeder v6: exit guide with a long nose (Exit_Guide_PRINT)

On the machine the exit guide's nose ended about 6 mm inside the main-plate window, 10 mm behind the front face of the fixed blade, and the fixed blade edge stood above the guide's floor. The net crossed an open pocket and then met a step. The new exit guide carries the net in a closed channel right up to the blades. It replaces the old exit guide, the gap filler, the shims and the add-on nozzle (v11), which is not needed.

Everything is in `Documents\Strip_Cutter\v3`:

| What | Where |
|---|---|
| Bambu project (1 plate, sliced, not started) | `print_STL_feeder_v6\Feeder_v6_exit_guide_long_nose_PETG-CF_0.6_nozzle.3mf` |
| STL | `print_STL_feeder_v6\v6_Exit_Guide_long_nose.stl` |
| Picture | `v6_exit_guide_long_nose_side_view.png` |
| CAD | Fusion doc **Strip Cutter v3 (feeder)**, component `Exit_Guide_PRINT` (old body kept, hidden, in `Exit_Guide_v51_old_PRINT`); script `cad\build12_exit_guide_long.py` |

## Plate
A1, 0.6 nozzle, Generic PETG-CF, 0.30 mm Strength, Textured PEI plate, tree supports from the build plate only. 18.8 g (1.5 g of it support), 52 min. Prints upright, as the old guide did. Break the support off from under the nose.

## What changed
Only the nose. Everything behind the old nose end is the same as v5.1.

| Item | Old | New |
|---|---|---|
| Nose end, measured from the old nose end | 0 | 9.4 mm further forward |
| Distance left to the fixed blade's front face | 10 mm | 0.6 mm |
| Channel at the tip | 13.2 x 6.2 mm, flared | 13.2 x 4.7 mm, no flare |
| Floor at the tip | level | rises 0.7 mm, to end above the blade edge |
| Underside of the tip | square | follows the 38 degree bevel of the fixed blade |

Nose outside size is unchanged (17.4 x 13.8 mm), so it passes through the same window.

## The one size this depends on
The nose length comes from your measurement: old nose end to the front face of the fixed blade = 10 mm. If the real distance is under 9.4 mm, the tip will stand proud of the fixed blade and the upper blade will hit it; sand the tip back until it sits just behind the fixed blade's front face.

## Fitting
1. Take off the lever with the upper blade, and the gap filler.
2. Loosen the fixed blade and its ledge and slide the blade down 3 to 4 mm.
3. Swap the exit guide in the feeder (same two M4 screws) and refit the feeder so the nose comes through the main-plate window.
4. Check the tip sits just behind the front face of the fixed blade (about 0.6 mm).
5. Slide the fixed blade up until its slope touches the underside of the tip, then tighten the blade and bring the ledge up under it.
6. Check the nose floor is level with or slightly above the blade edge, never below it.
7. Refit the lever and turn the crank by hand through one full cut before switching on.

## In the CAD
The CAD has the feeder about 6.5 mm closer to the blades than your machine, so in the Fusion model the new nose passes through the blades. The part is sized for the machine, not for the model.
