"""Strip cutter v5 - HMI front plate v2 (fit check, thin).

Changes from v1:
  * buttons as a cross / D-pad: UP, DOWN, LEFT (= STOP / BACK), RIGHT (= OK / START)
  * the 1.8" TFT is held by four M3 screws through its own corner holes. Short printed spacers
    (bosses) on the back of the plate set the board depth so the glass sits 0.2 mm behind the
    plate and is never pressed. Screw goes in from the front, nut on the back of the board.

Model axes: front view = looking from +Z. Front face at z = 0, back face at z = -T,
back-side features at negative z. The STL is flipped front-face-down for printing.

TFT board coordinates used below (measured on the user's photos, checked against the caliper):
  u = along the 58.11 side from the SD-card (4-pin) end, v = along the 34.04 side.
  holes: u = 2.95 / 55.15 (52.2 apart), v = 2.77 / 31.27 (28.5 apart), hole ~3.1 mm
  glass + white frame: u = 5.5 ... 49.1 (43.6 long), full width
  visible black area centre: u = 25.97 -> active area centre 3.1 mm from the board centre toward the SD end
  front side, 8-pin end: SMD part at v 6.5-9.2, header pins v 8-25.8 at u ~55.5,
                          glass ribbon (flex) u 48.5-52, v 8.4-30.8
"""
from build123d import *
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'v2')
os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# ---------------- plate ----------------
T = 2.0
W, H, R = 140.0, 80.0, 6.0
ENGRAVE = 0.6
HOLE_D = 3.4
HOLES = [(6, 6), (W - 6, 6), (6, H - 6), (W - 6, H - 6)]

# ---------------- TFT (landscape, 8-pin header on the LEFT seen from the front) ----------------
PCB_L, PCB_W, PCB_T = 58.11, 34.04, 1.6
PCB_C = (38.5, 51.0)
U0, V0 = PCB_L / 2, PCB_W / 2          # board centre in u, v
def tft_xy(u, v):
    """board (u, v) -> plate (x, y). SD end (u = 0) is on the right, v = 0 edge at the top."""
    return (PCB_C[0] + (U0 - u), PCB_C[1] + (V0 - v))

AA_SHIFT = 3.1
win_c = (PCB_C[0] + AA_SHIFT, PCB_C[1])
WIN_L, WIN_W, WIN_R = 37.0, 30.0, 1.0
CHAMF = 1.0

GLASS_H = 2.55          # top of the glass above the board's front face (caliper)
GLASS_GAP = 0.20        # air between glass and plate - the glass is never pressed
BOSS_H = GLASS_H + GLASS_GAP          # 2.75
SCREW_D = 3.6           # M3 with +-0.35 play to absorb small hole-position errors
BOSS_R = 3.1
TFT_HOLES_UV = [(2.95, 2.77), (2.95, 31.27), (55.15, 2.77), (55.15, 31.27)]
# boss clipping (in u, v) to stay off the glass, the ribbon, the SMD part and the header pins
def boss_clip(u, v):
    if u < 10:                       # SD end: glass starts at u = 5.5
        return dict(umax=4.45)
    if v < 10:                       # 8-pin end, SMD part side
        return dict(umin=52.6, vmax=5.9)
    return dict(umin=52.6, vmin=27.3)  # 8-pin end, header-pin / ribbon side

# ---------------- buttons, power switch ----------------
BTN_D = 12.3
DPAD_C = (104.0, 40.0)
DPAD_R = 17.0
BTNS = {'UP': (DPAD_C[0], DPAD_C[1] + DPAD_R), 'DOWN': (DPAD_C[0], DPAD_C[1] - DPAD_R),
        'LEFT': (DPAD_C[0] - DPAD_R, DPAD_C[1]), 'RIGHT': (DPAD_C[0] + DPAD_R, DPAD_C[1])}
ROCKER_D = 20.3
ROCKER_C = (24.0, 17.0)


def text_cut(s, x, y, size, align=(Align.CENTER, Align.CENTER), depth=ENGRAVE, z_top=0.0, rot=0):
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(z_top - depth)):
            with Locations(Location((x, y, 0), (0, 0, rot))):
                Text(s, font_size=size, font_path=FONT, align=align)
        extrude(amount=depth + 0.01)
    return p.part


def tri_cut(x, y, direction, size=3.6, depth=ENGRAVE):
    """small engraved triangle pointing 'up', 'down', 'left' or 'right', centred on (x, y)"""
    h = size * 0.87
    base = [(-size / 2, -h / 3), (size / 2, -h / 3), (0, 2 * h / 3)]     # pointing up
    rot = {'up': 0, 'left': 90, 'down': 180, 'right': 270}[direction]
    import math
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = [(x + px * c - py * s, y + px * s + py * c) for px, py in base]
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(-depth)):
            Polygon(*pts, align=None)
        extrude(amount=depth + 0.01)
    return p.part


def boss(u, v):
    x, y = tft_xy(u, v)
    clip = boss_clip(u, v)
    # clip box in u, v -> x, y   (x decreases as u grows, y decreases as v grows)
    umin, umax = clip.get('umin', -50), clip.get('umax', 150)
    vmin, vmax = clip.get('vmin', -50), clip.get('vmax', 150)
    x1, x2 = tft_xy(umax, 0)[0], tft_xy(umin, 0)[0]
    y1, y2 = tft_xy(0, vmax)[1], tft_xy(0, vmin)[1]
    cyl = Cylinder(BOSS_R, BOSS_H + 0.2, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(Location((x, y, -T + 0.2)))
    box = Box(x2 - x1, y2 - y1, 20).moved(Location(((x1 + x2) / 2, (y1 + y2) / 2, -T)))
    return cyl & box


def front_plate():
    with BuildPart() as plate:
        with BuildSketch(Plane.XY.offset(-T)):
            with Locations((W / 2, H / 2)):
                RectangleRounded(W, H, R)
        extrude(amount=T)
    part = plate.part
    for u, v in TFT_HOLES_UV:
        part = part + boss(u, v)
    with BuildPart() as cuts:
        # display window
        with BuildSketch(Plane.XY.offset(-T - 1)):
            with Locations(win_c):
                RectangleRounded(WIN_L, WIN_W, WIN_R)
        extrude(amount=T + 2)
        # 45 deg bevel on the front edge of the window
        with BuildSketch(Plane.XY.offset(-CHAMF)):
            with Locations(win_c):
                RectangleRounded(WIN_L, WIN_W, WIN_R)
        with BuildSketch(Plane.XY.offset(0.01)):
            with Locations(win_c):
                RectangleRounded(WIN_L + 2 * CHAMF + 0.02, WIN_W + 2 * CHAMF + 0.02, WIN_R + CHAMF)
        loft()
        # through holes: buttons, power switch, corner holes, TFT screws (through the bosses)
        with BuildSketch(Plane.XY.offset(-T - BOSS_H - 1)):
            with Locations(*BTNS.values()):
                Circle(BTN_D / 2)
            with Locations(ROCKER_C):
                Circle(ROCKER_D / 2)
            with Locations(*HOLES):
                Circle(HOLE_D / 2)
            with Locations(*[tft_xy(u, v) for u, v in TFT_HOLES_UV]):
                Circle(SCREW_D / 2)
        extrude(amount=T + BOSS_H + 2)
    part = part - cuts.part
    # front engraving
    dx, dy = DPAD_C
    marks = [tri_cut(dx, dy + 4.9, 'up'), tri_cut(dx, dy - 4.9, 'down'),
             tri_cut(dx - 4.9, dy, 'left'), tri_cut(dx + 4.9, dy, 'right'),
             text_cut('STOP', BTNS['LEFT'][0], BTNS['LEFT'][1] - 12.6, 3.2),
             text_cut('OK', BTNS['RIGHT'][0], BTNS['RIGHT'][1] - 12.6, 3.2),
             text_cut('POWER', ROCKER_C[0] + 14.5, ROCKER_C[1], 3.4, (Align.MIN, Align.CENTER)),
             text_cut('STRIP CUTTER', 13.0, 74.6, 3.4, (Align.MIN, Align.CENTER))]
    for c in marks:
        part = part - c
    # back marking: where the 8-pin header goes (hidden behind the board)
    hx = tft_xy(50.5, 0)[0]
    part = part - text_cut('8-PIN', hx, PCB_C[1], 3.0, depth=0.4, z_top=-T, rot=90)
    return part


if __name__ == '__main__':
    fp = front_plate()
    bb = fp.bounding_box()
    print('front plate v2: volume %.1f cm3, bbox %.1f x %.1f x %.2f, valid %s'
          % (fp.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z, fp.is_valid))
    for u, v in TFT_HOLES_UV:
        print('  TFT screw at', tuple(round(c, 2) for c in tft_xy(u, v)))
    print('  window centre', win_c, ' buttons', BTNS)
    export_step(fp, os.path.join(OUT, 'HMI_front_plate_v2.step'))
    p = fp.rotate(Axis.X, 180)
    b = p.bounding_box()
    p = p.translate((-b.min.X, -b.min.Y, -b.min.Z))
    export_stl(p, os.path.join(OUT, 'HMI_front_plate_v2.stl'), tolerance=0.01, angular_tolerance=0.1)
    print('ok')
