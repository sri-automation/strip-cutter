"""Strip cutter v5 - HMI front plate, fit-check version (thin), plus a hole-size gauge card.

Model axes: front view = looking down -Z (from +Z). Front face at z = 0, back face at z = -T,
back-side features go to negative z. Exported STLs are flipped front-face-down for printing.

Parts measured by the user (caliper):
  rocker KCD1 round: bezel 22.98, depth 28.27 (hole Ø20 nominal)
  push button red (PBS-11 type): head 17.78, length 38.09 (hole Ø12 nominal)
  1.8" TFT ST7735 red board: PCB 58.11 x 34.04, panel 43.6-44.3 long, glass 2.55 above the PCB,
  mounting holes ~52.1 x 30.8 (not used: the board is located by its outline)
"""
from build123d import *
import os

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# ---------------- dimensions ----------------
T = 2.0                       # plate thickness (fit check)
W, H, R = 130.0, 80.0, 6.0    # plate outline
ENGRAVE = 0.6                 # text depth on the front

# TFT (landscape, 8-pin header on the LEFT seen from the front)
PCB_L, PCB_W = 58.11, 34.04
PCB_C = (44.0, 50.0)          # PCB centre on the plate
AA_SHIFT = 3.5                # active area centre is 3.5 mm toward the SD (4-pin) end = right
WIN_L, WIN_W, WIN_R = 37.0, 30.0, 1.0   # window (active area 35.04 x 28.03 + ~1 mm)
CHAMF = 1.0                   # 45 deg bevel on the front edge of the window
GLASS_GAP = 2.55              # PCB front face sits this far behind the plate (panel thickness)
PCB_T = 1.6
CLR_L, CLR_W = 0.35, 0.40     # clearance per side around the PCB (crush ribs take up the play)
WALL = 1.6
FRAME_H = GLASS_GAP + PCB_T + 1.25      # frame wall height behind the plate
RIB_R, RIB_IN = 0.6, 0.50     # crush ribs: radius, how far they reach in from the wall face

# buttons and power switch
BTN_D = 12.3                  # Ø12 thread, printed holes come out a little small
BTN_Y = 19.0
BTNS = [(22.0, 'STOP'), (58.0, 'UP'), (82.0, 'DOWN'), (106.0, 'OK')]
ROCKER_D = 20.3
ROCKER_C = (106.0, 50.0)
HOLE_D = 3.4                  # M3 corner holes
HOLES = [(6, 6), (W - 6, 6), (6, H - 6), (W - 6, H - 6)]

win_c = (PCB_C[0] + AA_SHIFT, PCB_C[1])


def text_cut(s, x, y, size, align=(Align.CENTER, Align.CENTER), depth=ENGRAVE, z_top=0.0, rot=0):
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(z_top - depth)) as sk:
            with Locations(Location((x, y, 0), (0, 0, rot))):
                Text(s, font_size=size, font_path=FONT, align=align)
        extrude(amount=depth + 0.01)
    return p.part


def triangle_cut(x, y, up=True, size=6.0, depth=ENGRAVE):
    h = size * 0.87
    pts = [(x - size / 2, y - h / 3), (x + size / 2, y - h / 3), (x, y + 2 * h / 3)] if up else \
          [(x - size / 2, y + h / 3), (x + size / 2, y + h / 3), (x, y - 2 * h / 3)]
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(-depth)):
            Polygon(*pts, align=None)
        extrude(amount=depth + 0.01)
    return p.part


def front_plate():
    with BuildPart() as plate:
        # base plate
        with BuildSketch(Plane.XY.offset(-T)):
            with Locations((W / 2, H / 2)):
                RectangleRounded(W, H, R)
        extrude(amount=T)
        # TFT locating frame on the back
        fl, fw = PCB_L + 2 * CLR_L, PCB_W + 2 * CLR_W
        with BuildSketch(Plane.XY.offset(-T)) as fr:
            with Locations(PCB_C):
                Rectangle(fl + 2 * WALL, fw + 2 * WALL)
                Rectangle(fl, fw, mode=Mode.SUBTRACT)
            # finger gap in the bottom wall to lift the board out
            with Locations((PCB_C[0], PCB_C[1] - fw / 2 - WALL / 2)):
                Rectangle(12, WALL + 0.2, mode=Mode.SUBTRACT)
        extrude(amount=-FRAME_H)
        # crush ribs (half cylinders on the inner wall faces)
        ribs = []
        for dx in (-fl / 4, fl / 4):
            ribs.append((PCB_C[0] + dx, PCB_C[1] + fw / 2 + RIB_R - RIB_IN))
            ribs.append((PCB_C[0] + dx, PCB_C[1] - fw / 2 - RIB_R + RIB_IN))
        ribs.append((PCB_C[0] - fl / 2 - RIB_R + RIB_IN, PCB_C[1]))
        ribs.append((PCB_C[0] + fl / 2 + RIB_R - RIB_IN, PCB_C[1]))
        with BuildSketch(Plane.XY.offset(-T)):
            with Locations(*ribs):
                Circle(RIB_R)
        extrude(amount=-FRAME_H)
        # display window with a 45 deg bevel on the front
        with BuildSketch(Plane.XY.offset(-T - 0.01)):
            with Locations(win_c):
                RectangleRounded(WIN_L, WIN_W, WIN_R)
        extrude(amount=T + 0.02, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(-CHAMF)) as s1:
            with Locations(win_c):
                RectangleRounded(WIN_L, WIN_W, WIN_R)
        with BuildSketch(Plane.XY.offset(0.01)) as s2:
            with Locations(win_c):
                RectangleRounded(WIN_L + 2 * CHAMF + 0.02, WIN_W + 2 * CHAMF + 0.02, WIN_R + CHAMF)
        loft(mode=Mode.SUBTRACT)
        # button holes, power switch hole, corner holes
        with BuildSketch(Plane.XY.offset(-T - 0.01)):
            with Locations(*[(x, BTN_Y) for x, _ in BTNS]):
                Circle(BTN_D / 2)
            with Locations(ROCKER_C):
                Circle(ROCKER_D / 2)
            with Locations(*HOLES):
                Circle(HOLE_D / 2)
        extrude(amount=T + 0.02, mode=Mode.SUBTRACT)
    part = plate.part
    # front labels (engraved)
    cuts = [text_cut('STOP', 22.0, 5.5, 4.2), text_cut('OK', 106.0, 5.5, 4.2),
            triangle_cut(58.0, 5.6, True, 5.2), triangle_cut(82.0, 5.4, False, 5.2),
            text_cut('POWER', ROCKER_C[0], 34.0, 3.6),
            text_cut('STRIP CUTTER', 13.0, 73.5, 3.6, (Align.MIN, Align.CENTER))]
    for c in cuts:
        part = part - c
    # back marking where the 8-pin header goes (hidden behind the board)
    part = part - text_cut('8-PIN', PCB_C[0] - PCB_L / 2 + 6.0, PCB_C[1], 3.2, depth=0.4, z_top=-T, rot=90)
    return part


def gauge_card():
    GW, GH, GT = 130.0, 64.0, 2.0
    rock = [19.8, 20.0, 20.2, 20.4, 20.6]
    btn = [11.8, 12.0, 12.2, 12.4, 12.6]
    xs = [15 + 25 * i for i in range(5)]
    with BuildPart() as g:
        with BuildSketch(Plane.XY.offset(-GT)):
            with Locations((GW / 2, GH / 2)):
                RectangleRounded(GW, GH, 4)
        extrude(amount=GT)
        for x, d in zip(xs, rock):
            with BuildSketch(Plane.XY.offset(-GT - 0.01)):
                with Locations((x, 42)):
                    Circle(d / 2)
            extrude(amount=GT + 0.02, mode=Mode.SUBTRACT)
        for x, d in zip(xs, btn):
            with BuildSketch(Plane.XY.offset(-GT - 0.01)):
                with Locations((x, 13)):
                    Circle(d / 2)
            extrude(amount=GT + 0.02, mode=Mode.SUBTRACT)
    part = g.part
    for x, d in zip(xs, rock):
        part = part - text_cut('%.1f' % d, x, 57.5, 3.4)
    for x, d in zip(xs, btn):
        part = part - text_cut('%.1f' % d, x, 24.0, 3.4)
    part = part - text_cut('POWER SWITCH HOLES', GW / 2, 29.5, 2.6)
    part = part - text_cut('BUTTON', 3.0, 4.0, 2.4, (Align.MIN, Align.CENTER))
    return part


if __name__ == '__main__':
    fp = front_plate()
    gc = gauge_card()
    print('front plate volume %.1f cm3, gauge %.1f cm3' % (fp.volume / 1000, gc.volume / 1000))
    export_step(fp, os.path.join(OUT, 'HMI_front_plate_fitcheck.step'))
    export_step(gc, os.path.join(OUT, 'HMI_hole_gauge.step'))
    # print orientation: front face down (rotate 180 deg about X), then sit on z = 0
    for part, name in ((fp, 'HMI_front_plate_fitcheck'), (gc, 'HMI_hole_gauge')):
        p = part.rotate(Axis.X, 180)
        bb = p.bounding_box()
        p = p.translate((-bb.min.X, -bb.min.Y, -bb.min.Z))
        export_stl(p, os.path.join(OUT, name + '.stl'), tolerance=0.01, angular_tolerance=0.1)
    print('ok', win_c, 'frame height', FRAME_H)
