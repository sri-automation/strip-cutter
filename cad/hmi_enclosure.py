"""Strip cutter - HMI enclosure v1: a 150 mm tall stand for the arrow-key front plate (v2).

Two printed parts (PLA), both in this script:
  * TOWER  - a hollow post on the 40 x 140 mm free spot of the wooden base, with a sloped head on top
             (like a desk console): the face leans back 60 degrees from vertical, i.e. it is 30 degrees
             above horizontal. 60 is the most the 40 mm footprint allows: the underside of the head runs
             parallel to the parts behind the plate and already meets the post 25 mm above the wood.
             The v2 front plate (140 x 80, 4 x M3 in the corners) covers the face; M3 nuts sit in
             pockets behind the corners.
  * FOOT   - a 4 mm plate with a hollow plug. Screw it to the wood first (4 wood screws, easy to reach),
             then lower the tower over the plug and fix it with 4 x M3 screws through the tower walls.
Wiring: one open space from the head down the post, a separate closed duct (bottom to 62 mm) for the
mains wires of the power switch, cable exits at the back (and holes through the foot if you drill the
wood), zip-tie anchors on the back wall.
Printing: tower standing upright, no supports (every overhang is 60 degrees from horizontal or steeper,
apart from the small ends of the 4 corner bosses).

Axes: X = width (0..140, left to right as the operator sees it), Y = depth (operator at Y < 0, the post
is Y 0..40), Z = up (wood surface at Z = 0).
Run with build123d 0.13:  python hmi_enclosure.py  -> STEP + STL in ../print_STL_hmi_enclosure_v1
"""
import math, os
from build123d import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'print_STL_hmi_enclosure_v1')

# ---------------- main sizes ----------------
W = 140.0            # width = front plate width = free length on the base
DEPTH = 40.0         # post depth = free width on the base
H = 150.0            # top edge of the face above the wood
FOOT_T = 4.0         # foot plate under the tower
WALL = 3.0
TILT = 60.0          # face leans back from vertical (60 = face 30 deg above horizontal)
FACE_L = 80.0        # front plate height
HEAD_D = 40.0        # length of the roof behind the top edge of the face
R_SIDE = 6.0         # rounded side edges (same as the front plate corners)

th = math.radians(TILT)
U = (math.sin(th), math.cos(th))          # along the face, bottom -> top, in (Y, Z)
N = (math.cos(th), -math.sin(th))         # into the head, perpendicular to the face
B = (DEPTH - HEAD_D * N[0], H)            # top edge of the face
C = (B[0] + HEAD_D * N[0], B[1] + HEAD_D * N[1])   # top-back corner (on the back wall line)
A = (B[0] - FACE_L * U[0], B[1] - FACE_L * U[1])   # bottom (front) edge of the face
F = (0.0, A[1] - A[0] / N[0] * N[1])     # where the 45 deg underside (from A, along N) meets the post front


def face_point(x, s, d=0.0):
    """global point at width x, s mm up the face from its bottom edge, d mm into the head"""
    return Vector(x, A[0] + s * U[0] + d * N[0], A[1] + s * U[1] + d * N[1])


FACE_PLANE = Plane(origin=face_point(0, 0), x_dir=(1, 0, 0), z_dir=(0, N[0], N[1]))   # z points into the head

# front plate corner holes (plate x, plate y = s)
PLATE_HOLES = [(6, 6), (W - 6, 6), (6, FACE_L - 6), (W - 6, FACE_L - 6)]
BOSS_D, BOSS_L = 9.0, 9.0
NUT_AF, NUT_T = 5.65, 2.6              # M3 nut pocket (5.5 mm nut, a snug fit)

# foot / tower joint
PLUG_H = 14.0
PLUG_CLR = 0.25
PLUG_WALL = 5.0
JOINT_Z = FOOT_T + 7.0                 # height of the 4 x M3 joint screws
JOINT_X = (52.0, 104.0)

# wiring
DUCT = dict(x0=13.0, x1=35.0, y0=21.0, z0=FOOT_T, z1=62.0, wall=2.0)   # mains duct (outer), from the bottom up
SLOT_Z = (FOOT_T + PLUG_H + 3.0, FOOT_T + PLUG_H + 13.0)        # cable exits in the back wall


def profile_solid():
    pts = [(0, FOOT_T), F, A, B, C, (DEPTH, FOOT_T)]
    with BuildPart() as p:
        with BuildSketch(Plane.YZ) as sk:
            Polygon(*pts, align=None)
            # round the inside corner under the head (stronger) and the top-back corner (looks)
            vs = sk.vertices()
            fillet([v for v in vs if abs(v.Y - F[1]) < 0.01 and abs(v.X - F[0]) < 0.01], 8.0)
            vs = sk.vertices()
            fillet([v for v in vs if abs(v.Y - C[1]) < 0.01 and abs(v.X - C[0]) < 0.01], 10.0)
        extrude(amount=W)
    return p.part


def side_edges(part):
    """edges on the two side faces, except the face edge and the bottom edge"""
    nrm = Vector(0, N[0], N[1])
    keep = []
    for e in part.edges():
        c = e.center()
        if not (abs(c.X) < 1e-3 or abs(c.X - W) < 1e-3):
            continue
        if abs(c.Z - FOOT_T) < 1e-3:
            continue                                             # bottom
        p0, p1 = e.start_point(), e.end_point()
        if abs((p0 - face_point(p0.X, 0)).dot(nrm)) < 1e-3 and abs((p1 - face_point(p1.X, 0)).dot(nrm)) < 1e-3:
            continue                                             # the face edge (the front plate covers it)
        keep.append(e)
    return keep


def tower():
    outer = profile_solid()
    # all round the two sides (the face edge stays sharp: the front plate sits on it)
    outer = fillet(side_edges(outer), R_SIDE)
    solid_outer = outer
    # open the face and the bottom, walls 3 mm
    face = [f for f in outer.faces() if abs(f.normal_at().dot(Vector(0, -N[0], -N[1])) - 1) < 1e-3
            and abs((f.center() - face_point(0, 0)).dot(Vector(0, N[0], N[1]))) < 1e-3]
    bottom = [f for f in outer.faces() if abs(f.center().Z - FOOT_T) < 1e-3 and f.normal_at().Z < -0.99]
    assert len(face) == 1 and len(bottom) == 1, (len(face), len(bottom))
    shell = offset(outer, amount=-WALL, openings=face + bottom)
    part = shell

    # ---- corner bosses for the front plate, M3 nut pockets at their inner ends ----
    for x, s in PLATE_HOLES:
        pl = Plane(origin=face_point(x, s), x_dir=(1, 0, 0), z_dir=(0, N[0], N[1]))
        boss = pl * Cylinder(BOSS_D / 2, BOSS_L, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # web from the boss to the side wall, so the boss never starts as a floating island when printed
        wx0, ww = (-x, x) if x < W / 2 else (0.0, W - x)
        web = pl * Box(ww, BOSS_D, BOSS_L, align=(Align.MIN, Align.CENTER, Align.MIN)).moved(Location((wx0, 0, 0)))
        part = part + ((boss + web) & solid_outer)
    for x, s in PLATE_HOLES:
        pl = Plane(origin=face_point(x, s), x_dir=(1, 0, 0), z_dir=(0, N[0], N[1]))
        part = part - pl * Cylinder(1.7, BOSS_L + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        pn = Plane(origin=face_point(x, s, BOSS_L - NUT_T), x_dir=(1, 0, 0), z_dir=(0, N[0], N[1]))
        with BuildPart() as nut:
            with BuildSketch(pn):
                RegularPolygon(NUT_AF / math.sqrt(3), 6, rotation=30)
            extrude(amount=NUT_T + 3)
        part = part - nut.part

    # ---- mains duct: a closed channel from under the power switch down to the back exit ----
    d = DUCT
    dz = d['z1'] - d['z0']
    duct = Box(d['x1'] - d['x0'], DEPTH - WALL - d['y0'] + 0.5, dz, align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((d['x0'], d['y0'], d['z0'])))
    hole = Box(d['x1'] - d['x0'] - 2 * d['wall'], DEPTH - WALL - d['y0'] - d['wall'], dz + 2,
               align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((d['x0'] + d['wall'], d['y0'] + d['wall'], d['z0'] - 1)))
    part = part + (duct - hole)

    # ---- zip-tie anchors on the back wall (low-voltage side): a block with a tunnel ----
    yw = DEPTH - WALL                                            # inside face of the back wall
    for x in (62.0, 100.0):
        for z in (52.0, 88.0):
            with BuildPart() as anc:
                with BuildSketch(Plane.YZ.offset(x - 5)):
                    # 45 deg underside, so it prints without support
                    Polygon((yw + 0.5, z), (yw - 6, z + 6.5), (yw - 6, z + 14), (yw + 0.5, z + 14), align=None)
                extrude(amount=10)
            tunnel = Box(14, 2.4, 4.6, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, yw - 3.0, z + 7.2)))
            part = part + (anc.part - tunnel)

    # ---- cable exits in the back wall: mains (into the duct) and two low-voltage slots ----
    zc = (SLOT_Z[0] + SLOT_Z[1]) / 2
    h = SLOT_Z[1] - SLOT_Z[0]
    for x0, x1 in ((d['x0'] + d['wall'] + 1, d['x1'] - d['wall'] - 1), (46.0, 74.0), (82.0, 110.0)):
        with BuildPart() as sl:
            with BuildSketch(Plane.XZ.offset(-(DEPTH + 1))):
                with Locations(((x0 + x1) / 2, zc)):
                    SlotOverall(x1 - x0, h)
            extrude(amount=WALL + 2)
        part = part - sl.part

    # ---- joint screws (M3) through the front and back walls into the foot plug ----
    for x in JOINT_X:
        hole = Cylinder(1.7, DEPTH + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, -1, JOINT_Z), (-90, 0, 0)))
        part = part - hole
    return part, solid_outer


def foot():
    with BuildPart() as p:
        with BuildSketch():
            with Locations((W / 2, DEPTH / 2)):
                RectangleRounded(W, DEPTH, 4.0)
        extrude(amount=FOOT_T)
        # plug that fits inside the tower walls
        ox, oy = WALL + PLUG_CLR, WALL + PLUG_CLR
        pw, pd = W - 2 * ox, DEPTH - 2 * oy
        with BuildSketch(Plane.XY.offset(FOOT_T)):
            with Locations((W / 2, DEPTH / 2)):
                RectangleRounded(pw, pd, 3.5)      # clears the 3 mm inner corner radius of the tower
                RectangleRounded(pw - 2 * PLUG_WALL, pd - 2 * PLUG_WALL, 1.0, mode=Mode.SUBTRACT)
        extrude(amount=PLUG_H)
    part = p.part
    # notch in the plug where the tower's mains duct comes down to the foot
    d = DUCT
    part = part - Box(d['x1'] - d['x0'] + 0.8, DEPTH, PLUG_H + 2, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((d['x0'] - 0.4, d['y0'] - 0.4, FOOT_T)))
    # joint: M3 holes and nut slots (drop the nut in from the top)
    for x in JOINT_X:
        part = part - Cylinder(1.7, DEPTH + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, -1, JOINT_Z), (-90, 0, 0)))
        for y_out, sgn in ((WALL + PLUG_CLR, 1), (DEPTH - WALL - PLUG_CLR, -1)):
            yc = y_out + sgn * (1.4 + NUT_T / 2)
            slot = Box(NUT_AF, NUT_T, FOOT_T + PLUG_H - (JOINT_Z - 3.4) + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, yc, JOINT_Z - 3.4)))
            part = part - slot
    # wood screws: 4 x countersunk (3.5 - 4 mm wood screws)
    for x, y in ((42, 14), (42, 26), (117, 14), (117, 26)):
        part = part - Cylinder(2.1, FOOT_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, -1)))
        part = part - Cone(2.1, 4.3, 2.2, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(Location((x, y, FOOT_T + 0.01)))
    # optional cable holes through the foot (drill the wood under them to run the wires below)
    part = part - Cylinder(5.0, FOOT_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location(((DUCT['x0'] + DUCT['x1']) / 2, 30, -1)))   # mains, inside the duct
    with BuildPart() as sl:
        with BuildSketch(Plane.XY.offset(-1)):
            with Locations((77, DEPTH / 2)):
                SlotOverall(46, 10)
        extrude(amount=FOOT_T + 2)
    part = part - sl.part
    return part


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    print('face: A (bottom edge) Y %.1f Z %.1f, B (top edge) Y %.1f Z %.1f, C Y %.1f Z %.1f, F Z %.1f' % (A + B + C + (F[1],)))
    t, outer = tower()
    f = foot()
    for nm, p in (('tower', t), ('foot', f)):
        bb = p.bounding_box()
        print('%s: %.1f cm3, %.1f x %.1f x %.1f mm, valid %s' % (nm, p.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z, p.is_valid))
    export_step(t, os.path.join(OUT, 'HMI_enclosure_tower.step'))
    export_step(f, os.path.join(OUT, 'HMI_enclosure_foot.step'))
    # print orientation: tower standing, its 140 mm side along the bed's Y (the A1 moves the bed in Y)
    tp = t.rotate(Axis.Z, 90)
    bb = tp.bounding_box(); tp = tp.translate((-bb.min.X, -bb.min.Y, -bb.min.Z))
    export_stl(tp, os.path.join(OUT, 'HMI_enclosure_tower.stl'), tolerance=0.02, angular_tolerance=0.15)
    bb = f.bounding_box(); fp = f.translate((-bb.min.X, -bb.min.Y, -bb.min.Z))
    export_stl(fp, os.path.join(OUT, 'HMI_enclosure_foot.stl'), tolerance=0.02, angular_tolerance=0.15)
    print('ok')
