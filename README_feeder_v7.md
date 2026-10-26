# Feeder v7: strong pinch arm and exit guide v7

Two problems are fixed here:

- **Pinch arm:** the printed arm crushed under the M4 pressure screw and washer.
- **Exit guide:** it stopped the top roller from coming down, the net jammed just after the rollers, and the nose hit the fixed blade.

Both parts are on one A1 plate.

Everything is in `Documents\Strip_Cutter\v3`:

| What | Where |
|---|---|
| Bambu project (1 plate, sliced, not started) | `print_STL_feeder_v7\Feeder_v7_arm_and_exit_guide_PETG-CF_0.6_nozzle.3mf` |
| STLs (print orientation) | `print_STL_feeder_v7\v7_Pinch_Arm_strong.stl`, `print_STL_feeder_v7\v7_Exit_Guide.stl` |
| STLs (in machine position, for checking) | `print_STL_feeder_v7\*_assembly_position.stl` |
| Pictures | `print_STL_feeder_v7\v7_pinch_arm_before_after.png`, `print_STL_feeder_v7\v7_exit_guide_before_after.png` |
| CAD | Fusion doc **Strip Cutter v3 (feeder)**, components `Pinch_Arm_PRINT` and `Exit_Guide_PRINT`. The old bodies are kept, hidden, in `Pinch_Arm_v6_old_PRINT` and `Exit_Guide_v51_old_PRINT`. Script: `cad\build13_arm_and_guide.py` |

## Plate settings

| Setting | Value |
|---|---|
| Printer, nozzle | A1, 0.6 mm |
| Filament | Generic PETG-CF |
| Plate | Textured PEI |
| Profile | 0.30 mm Strength |
| Walls | 6 |
| Top / bottom shell layers | 5 / 4 |
| Sparse infill | 60 % gyroid |
| Supports | Tree (auto), max bridge length 12 mm |
| Exit guide only | Supports from the build plate only, so none inside the channel |
| Pinch arm only | A support blocker in the pressure-screw slot, so the slot roof prints as a bridge and the slot stays empty |
| Weight and time | 47.1 g (3.9 g of it support), about 1 h 57 min |

The pinch arm prints lying on the face that runs along the frame wall, as the earlier arms did. The exit guide prints upright, as before.

Cleaning the parts after printing:

- **Pinch arm:** the tree supports stand between the two cheeks, under the upper cheek. One trunk goes down through the roller-axle hole in the lower cheek. Push it out with a screwdriver or a drill bit.
- **Exit guide:** break the supports off under the nose and under the outside of the floor.

## Pinch arm: what changed

| Item | v6 (now on the machine) | v7 |
|---|---|---|
| Material under the knob | Thin tab, 8.8 mm wide, x -27 to -12, z 70 to 85 | Solid block from the riser at the back (x -35) to the front (x -10.5), z 70 to 93, the full width of the arm |
| Seat for the washer | 8.8 mm wide, at z 85 | 14.5 mm wide (extra wing on the guide side), at z 93, which is **8 mm higher** |
| Screw slot | 5.8 mm wide, 1.5 mm walls | 4.8 mm wide (M4 is a sliding fit), same 10 mm length. Walls are 2 mm on the frame side and 7.7 mm on the guide side under the washer |

The frame-side wall can't be thicker than 2 mm, because the screw sits only 4.4 mm from the arm face that runs along the frame wall. The load now goes into the deep block in front of and behind the screw, and into the wide wing, not into that thin wall.

**The pressure screw has to be 8 mm longer.** The washer seat is 8 mm higher than before. If you use an M4 x 30 now, use an M4 x 40 and set the pressure again. Keep a 16 mm washer under the head.

## Exit guide: what changed

| Item | v6 (now on the machine) | v7 |
|---|---|---|
| Side faces where the pinch arm swings | 0.2 mm from the arm | Trimmed to 1.4 mm clearance. The outer parts of the cheek on the motor side are removed. The clearances for the arm's washers and the top roller are 1 to 3 mm deeper |
| Channel roof just after the rollers | z 66.0 (opening 6.2 mm) | z 68.5 (opening 8.7 mm). It slopes down to 66.4 near the main plate and to 65.4 at the tip |
| Nose length | 9.4 mm past the old nose end | 6.9 mm past it, so **2.5 mm shorter** |
| Nose underside | Follows the bevel of the fixed blade | Same bevel, moved back 2.5 mm with the tip |

In the CAD, the arm can now swing down 4 degrees from its CAD position (the top roller about 2.2 mm lower) before it touches anything. It is clear of the exit guide, the frame and the main plate. At about 6 degrees the frame floor stops it, as it did before.

## Fitting

1. **Pinch arm**
   1. Take off the old arm.
   2. Fit the new one with the same pivot pin and roller.
   3. Fit the longer pressure screw with its washer, and set the pressure.
2. **Exit guide**
   1. Take off the lever with the upper blade.
   2. Loosen the fixed blade and slide it down 3 to 4 mm.
   3. Swap the exit guide (same two M4 screws) and refit the feeder so the nose comes through the main-plate window.
   4. Check that the tip stops just behind the front face of the fixed blade and does not touch it.
   5. Slide the fixed blade up until its slope touches the underside of the tip. Tighten the blade and bring its ledge up under it.
   6. Check that the nose floor is level with the blade edge or slightly above it, never below.
   7. Refit the lever and turn the crank by hand through one full cut before switching on.
3. **Check the roller grip:** with no net in, press the arm down by hand. The top roller should touch the drive roller without the arm touching the exit guide.

## In the CAD

On your machine the feeder sits about 6.5 mm further from the blades than in the Fusion model. In the model, the nose therefore passes through the blades. The part is sized for the machine, not for the model.

The nose length assumes the old nose end is 7.5 mm from the front face of the fixed blade. You measured 10 mm, but v6 (built for 10 mm) hit the blade.

- **If v7 still touches the blade:** sand the tip back.
- **If it ends more than about 1 mm short of the blade:** that is fine. The bevel underside still guides the net over the blade edge.
