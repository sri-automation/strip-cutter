# Cutter v7: printed PETG-CF parts (0.6 mm hardened nozzle)

Everything is in `Documents\Strip_Cutter\v3`:

| What | Where |
|---|---|
| Bambu project (3 plates, sliced, not started) | `print_STL_cutter_v7\Strip_Cutter_v7_PETG-CF_0.6_nozzle.3mf` |
| STL files | `print_STL_cutter_v7\` |
| Main plate and front bracket (draft, print later) | `print_STL_cutter_v7\later_after_template_test\` |
| Pictures | `v7_printed_cutter_front.png`, `v7_printed_cutter_back.png`, `v7_pinch_yoke.png` |
| CAD | Fusion doc **Strip Cutter v3 (feeder)**; script `cad\build7.py` |

## Bambu project settings
- **Printer:** Bambu Lab A1, 0.6 nozzle.
- **Filament:** Generic PETG-CF. If your spool is Bambu-brand, switch to **Bambu PETG-CF** in the filament list (I enabled both).
- **Process:** 0.30 mm Strength @BBL A1 0.6 nozzle, with 4 walls, 40 % gyroid infill, 5 top and 4 bottom layers.
- **On the printer itself:** after fitting the nozzle, set the nozzle to **0.6 mm hardened steel** on the A1's screen. Bambu Studio refuses to send the job if the printer still reports 0.4 mm stainless.
- **Dry the PETG-CF** before printing if the spool has been open; wet CF filament prints weak and stringy.

| Plate | Parts | Filament | Time |
|---|---|---|---|
| 1 | Motor test template + fit-test coupon | 9 g | 26 min |
| 2 | Pinch yoke (tree supports on) | 24 g | 1 h 08 min |
| 3 | Knife lever, link, crank, bed-knife ledge, height gauge, 3 pin spacers | 85 g | 3 h 01 min |

**Print plate 1 first.** It tells us whether the other parts and the main plate will fit.

## Plate 1: what to test and tell me
**Motor template** (2.4 mm thick, same holes as the real plate):
1. Slide it over the shaft onto the 3 bosses. The long tab should point along the motor body.
2. Do all three M6 screws start in the bosses by hand? If one doesn't, tell me which and roughly how far off.
3. With the template sitting flat on the bosses, measure **how far the shaft tip stands above the template's top face**. I'm assuming 26.6 mm (29 mm above the bosses).
4. Measure where the **slot in the shaft starts and ends, from the shaft end**. I'm assuming 13 to 19.5 mm.
5. Tell me how far the gearbox housing reaches from the shaft centre toward the stepper side, so I can confirm the 10 mm gap to the NEMA23.

**Fit-test coupon** (three holes, same diameters as the real parts):
- **16.2 mm hole:** a 688ZZ bearing should press in by hand or with light vise pressure and stay put.
- **10.35 mm hole:** should slide on the motor shaft without wobble.
- **8.3 mm hole:** an M8 bolt should pass freely.

Tell me tight / good / loose for each. If the bearing or shaft fit is off, I'll correct the lever, link and crank before you print plate 3.

## What changed from the plywood version
- **Knife lever:** one printed piece, 10 mm thick, replacing the plywood lever, hub and drive boss.
  - Two 688ZZ bearings sit 17 mm apart in a built-in hub.
  - The blade sits on the face that prints on the bed, so the seat is flat.
  - Three M4 grub screws poke 2 mm out of the back and act as stops for the blade's back edge. They set the edge parallel and at the right height with no measuring.
  - The two blade clamp holes are slots (8 × 13 mm), because I only know the blade's threaded-hole positions from photos.
  - The M8 drive bolt's head is trapped in a hex pocket at the back.
- **Link:** printed, 103.4 mm between centres, with two 688ZZ bearings at each end and a lip that keeps them in. The pins no longer rub on plastic.
- **Crank:** same 13.3 mm radius. The M4 set screw and its nut now slide along the shaft in a channel, so the screw can be moved to wherever the slot in your shaft actually is.
- **Main plate:** printed, 240 × 120 × 8 mm, printed front face down so the face both knives reference is flat. On the back it has a 22 mm thick block behind the lever pivot with a hex pocket for the M8 head, feet with gussets for wood screws into the base, and pockets for all nuts. Three separate front brackets bolt on with M5.
  - **This is a draft.** I'll finalise it after your template results, including moving the motor seats so the shaft tip lands where the crank needs it.
- **Checked in Fusion** through a full crank turn and with the pinch arm fully up and fully down: nothing collides.

## Pinch yoke: why it probably broke and what I changed
- **Likely cause:** the yoke prints on its side, so the crossbar over the roller has its layers stacked along its length. Tightening the M8 axle pulls the two side plates together and bends that crossbar across the layers, which is the weak direction. I told you to tighten that nut firmly, which made it worse.
- **Fix:**
  - Crossbar is now 16 × 10 mm (was 12 × 6) and the riser is 16 mm wide.
  - An **M5 × 40 bolt runs through the crossbar** from side to side with a nut sunk in the far plate. It keeps the layers in compression, so the crossbar can't split.
  - A small gusset joins the riser to the arm.
- **If it broke somewhere else** (the arm, the pivot tube, the slot for the knob screw), tell me where and I'll reinforce that spot instead.
- **When fitting:** tighten the M5 tie bolt first, then the M8 axle only until the roller has no side play.

## Strength numbers
| Part | Load | Stress | Note |
|---|---|---|---|
| Lever (10 × 32 mm section) | 200 N at the drive pin | about 6 MPa | PETG-CF is good for 50+ MPa along the layers |
| Lever tip deflection | 200 N | about 0.6 mm | |
| Link at the bearing eye | 300 N | about 2.4 MPa | |
| Crank set-screw nut on its channel wall | 3 N·m | about 21 MPa | Bearing pressure |

## Hardware for the parts on plates 2 and 3
| Item | Qty | Used for |
|---|---|---|
| 688ZZ bearing (8 × 16 × 5) | 6 | 2 in the lever hub, 4 in the link |
| M8 × 45 hex bolt | 2 | Lever drive pin, crank pin |
| M8 nylock nut | 2 | Link pins |
| M8 washer | 2 | Link pins (on top of the printed spacer ring) |
| M4 × 10 cap screw | 2 | Blade clamp, into the blade's threaded holes |
| M4 washer, 12 mm OD | 3 | 2 for the blade clamp, 1 for the shaft end |
| M4 × 12 grub screw | 4 | 3 blade stops in the lever, 1 crank set screw |
| M4 nut | 1 | Crank set screw |
| M4 × 6 screw | 1 | Shaft end |
| M5 × 40 cap screw + washer + nut | 1 | Yoke tie bolt |

The pivot bolt, bed-knife bolts, motor bolts and bracket screws belong to the main plate; I'll list them when that part is final.

## Fitting notes for plate 3
- **Blade on the lever:** screw the 3 grub screws in from the front until they stick out about 2 mm at the back. Push the blade's back edge against them, bevel toward the lever, and clamp with the two M4 × 10 screws and large washers. The screw tips must stay below the blade's flat face.
- **Drive bolt:** put the M8 × 45 into its hex pocket before fitting the blade; the blade end covers part of the pocket.
- **Bearings:** press them in square. In the link they go in from the open side and stop against the lip.
- **Each link pin stacks as:** printed boss, two bearings (in the link), printed spacer ring, M8 washer, nylock. Tighten until the bearing inner rings are clamped; the link then turns on the bearings only.
- **Crank:** drop the M4 nut into the channel from the hub end, start the grub screw through the side slot, slide the crank on, and move the screw along until it drops into the shaft slot.
