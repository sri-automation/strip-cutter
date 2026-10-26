# Strip Cutter v7 - PRINTED CUTTER (PETG-CF, 0.6 nozzle): lever shear with the two 82 x 28.75 x 2.88 planer blades, wiper-motor crank drive
# Adds new components beside the v5.1 feeder in "Strip Cutter v3 (feeder)". Coordinates as the feeder model (mm):
#   x = feed direction (plywood main plate front face at x = 0), y = across (+y motor side), z = up (base board top z = 0)
# Shear plane x = 2.88: bed knife x 0..2.88 (bevel toward the plate), moving knife x 2.88..5.76 (bevel toward the lever).
# Run with PATCH = True on the v6 model: renames C6_ -> C7_ components and updates their bodies in place (keeps joints J9..J12).
import adsk.core, adsk.fusion, math, traceback

S = 0.1
LOG = []
try:
    PATCH
except NameError:
    PATCH = False

# ---------------- key geometry ----------------
ZB = 59.7                     # bed knife edge (0.1 below the exit-channel floor)
BW, BL, BT = 28.75, 82.0, 2.88
BEV = BT / math.tan(math.radians(38.0))    # bevel height on the blade face (38 deg bevel)
YA = -36.0                    # bed knife y range YA .. YA+82
YP, ZP = -45.0, 54.7          # lever pivot (5 mm below the bed edge)
E_OFF = 5.0                   # moving knife edge: 5 mm below the lever line through the pivot
U0 = 10.0                     # moving knife starts 10 mm from the pivot along the lever
TH_OPEN, TH_CLOSED = 27.0, 10.0            # lever angle (deg): park / fully closed
TH_REF = TH_OPEN              # bodies are modelled at the park (open) position
XL0, XL1 = 2 * BT, 2 * BT + 10.0           # printed lever x 5.76 .. 15.76
LEV_LEN = 112.0
SLOT_U = (15.0, 67.0)         # U-slot centres from the blade end (estimated from photos; not used for drilling)
HOLE_U = (41.0 - 12.7, 41.0 + 12.7)        # M4 threaded holes (estimated; the user marks through the real blade)
HOLE_BACK = 5.8               # threaded holes from the back edge
SLOT_END = 11.35              # U-slot closed end from the cutting edge (measured)
HUB_SCREW_ANG = (120.0, 200.0, 280.0)
DU, DV = 98.0, 18.0             # drive point on the lever (link pin), lever-local
DB_SCREW_ANG = (60.0, 180.0, 300.0)
# ---- drive (wiper motor PM-11G, crank, link) ----
CY, CZ = 125.0, 42.0                        # motor shaft axis (front view: y right, z up)
R_CR, L_LK = 13.3, 103.4                    # crank radius, link length (hole to hole)
PHI_OPEN = math.degrees(math.atan2(0, 1))   # set below from the geometry
SHAFT_ABOVE_BOSS = 29.0                     # shaft tip above the boss-face plane (ESTIMATE - to be measured)
SLOT_FROM_TIP = (12.8, 19.5)                # key slot on the shaft, from the tip (ESTIMATE from photo)
BOSS_R = 44.5 / math.sqrt(3.0)              # 3 x M6 bosses, 44.5 apart -> 25.69 bolt circle radius
BOSS_ANG = (0.0, 120.0, 240.0)              # body pointing up (+z), axis offset to +y (from the photos)
TIP = -8.0 + SHAFT_ABOVE_BOSS               # shaft tip x (bosses against the plate back face x = -8)
X_SS = TIP - 0.5 * (SLOT_FROM_TIP[0] + SLOT_FROM_TIP[1])   # set screw plane
ARM0, ARM1 = 1.5, 9.5                       # crank arm x range (next to the plate)
TP = 8.0                                    # main plate thickness (front face x = 0)
PIV_HEAD = -11.0                            # underside of the M8 pivot bolt head (in the plate's hex pocket)
HUB1 = 30.0                                 # front end of the lever's bearing hub
BRG_R = 8.10                                # 688ZZ seat radius (16.2 dia; check with the fit-test piece)
NOSE = 0.8                                  # raised ring that touches only the bearing inner ring
XB1 = 26.2                                  # top of the drive boss / crank-pin boss
XK0, XK1 = 27.0, 37.8                       # link x range: 2 x 688ZZ (27..37) + 0.8 lip
STOP_U = (13.0, 51.0, 88.0)                 # blade back-edge stop screws (lever-local u)
HUBX = 20.0                                 # crank hub end
BORE_R = 5.175                              # crank bore 10.35 on the 10.07 shaft
SS_X0, SS_X1 = 4.0, 15.0                    # set-screw slot along the shaft
BRK_Y = (-62.0, 48.0, 152.0)                # front brackets
FOOT_SCREWS = [(-30.0, -47.0), (-30.0, 95.0), (-30.0, 165.0)]
TIE_X, TIE_Z = -43.0, 99.0                  # pinch yoke tie bolt
SW_R = 24.5                                 # park switch roller centre radius from the shaft


def run(_context: str):
    try:
        _run()
    except Exception:
        LOG.append('ERROR\n' + traceback.format_exc())
    print('\n'.join(LOG[-60:]))


def _run():
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    tb = adsk.fusion.TemporaryBRepManager.get()
    UN = adsk.fusion.BooleanTypes.UnionBooleanType
    DF = adsk.fusion.BooleanTypes.DifferenceBooleanType
    IN = adsk.fusion.BooleanTypes.IntersectionBooleanType

    def P3(x, y, z): return adsk.core.Point3D.create(x * S, y * S, z * S)
    def V3(x, y, z): return adsk.core.Vector3D.create(x, y, z)
    def box(x0, x1, y0, y1, z0, z1):
        return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                            V3(1, 0, 0), V3(0, 1, 0), abs(x1 - x0) * S, abs(y1 - y0) * S, abs(z1 - z0) * S))
    def obox(c, ld, wd, l, w, h):
        return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P3(*c), V3(*ld), V3(*wd), l * S, w * S, h * S))
    def cyl(p0, p1, r, r2=None):
        return tb.createCylinderOrCone(P3(*p0), r * S, P3(*p1), (r if r2 is None else r2) * S)
    def cylx(x0, x1, y, z, r): return cyl((x0, y, z), (x1, y, z), r)
    def cylz(z0, z1, x, y, r): return cyl((x, y, z0), (x, y, z1), r)
    def uni(*bs):
        a = bs[0]
        for b in bs[1:]:
            if not tb.booleanOperation(a, b, UN): LOG.append('union failed')
        return a
    def sub(a, *bs):
        for b in bs:
            if not tb.booleanOperation(a, b, DF): LOG.append('subtract failed')
        return a
    def inter(a, b):
        tb.booleanOperation(a, b, IN); return a
    def ring_x(x0, x1, y, z, ro, ri): return sub(cylx(x0, x1, y, z, ro), cylx(x0 - 1, x1 + 1, y, z, ri))
    def hexp(axis, a0, a1, c1, c2, af):
        r = af / 2.0 / math.cos(math.pi / 6)
        b = None
        for k in range(3):
            a = math.pi / 3 * k
            ca, sa = math.cos(a), math.sin(a)
            if axis == 'x':
                bb = obox(((a0 + a1) / 2, c1, c2), (1, 0, 0), (0, ca, sa), abs(a1 - a0), 2 * r, af)
            else:
                bb = obox((c1, c2, (a0 + a1) / 2), (ca, sa, 0), (-sa, ca, 0), 2 * r, af, abs(a1 - a0))
            b = bb if b is None else inter(b, bb)
        return b
    def hspace(p, n):           # half space {q: (q - p).n <= 0}; n in the xz or xy plane
        L = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]); n = (n[0] / L, n[1] / L, n[2] / L)
        wd = (0, 1, 0) if abs(n[1]) < 1e-9 else (0, 0, 1)
        B = 400.0
        return obox((p[0] - n[0] * B / 2, p[1] - n[1] * B / 2, p[2] - n[2] * B / 2), n, wd, B, B, B)
    def rot_lever(b, th=TH_REF):  # lever-local (x, YP+u, ZP+v) -> world at lever angle th
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(th), V3(1, 0, 0), P3(0, YP, ZP))
        tb.transform(b, m)
        return b
    def L(u, v): return (YP + u, ZP + v)     # lever-local (y, z) before rotation
    LEDGE_Y = (YA + 11, YA + 41, YA + 71)
    def world_D(th):
        a = math.radians(th) + math.atan2(DV, DU); R = math.hypot(DU, DV)
        return (YP + R * math.cos(a), ZP + R * math.sin(a))
    _do = world_D(TH_OPEN)
    PHI_O = math.atan2(_do[1] - CZ, _do[0] - CY)             # open = crank pointing at the lever pin (extended)
    _uo = (math.cos(PHI_O), math.sin(PHI_O)); _to = (-_uo[1], _uo[0])
    SW_HOLES = [(CY + (SW_R + 7.5) * _uo[0] + t * _to[0], CZ + (SW_R + 7.5) * _uo[1] + t * _to[1]) for t in (12.0 - 4.75, 12.0 + 4.75)]
    LOG.append('PHI_O %.2f deg  TIP x %.1f  set screw x %.2f' % (math.degrees(PHI_O), TIP, X_SS))

    # ---------------- appearances ----------------
    def app_named(n):
        a = design.appearances.itemByName(n)
        return a
    APP = {'STEEL': app_named('Steel'), 'BLADE': app_named('HSS blade'), 'BLUE': app_named('PETG blue'),
           'RUBBER': app_named('Rubber washer'), 'DARK': app_named('Black oxide'), 'AL': app_named('Aluminium plate'),
           'CF': app_named('PETG-CF black')}
    ply = design.appearances.itemByName('Plywood')
    if ply is None:
        base = None
        for i in range(app.materialLibraries.count):
            lib = app.materialLibraries.item(i)
            if 'Appearance' in lib.name:
                for nm in ('Wood - Pine', 'Pine', 'Oak', 'Wood'):
                    for j in range(lib.appearances.count):
                        a = lib.appearances.item(j)
                        if nm.lower() in a.name.lower():
                            base = a; break
                    if base: break
            if base: break
        if base:
            ply = design.appearances.addByCopy(base, 'Plywood')
    APP['PLY'] = ply

    def mkcomp(parent, name, bodies, xform=None):
        if PATCH:
            comp = design.allComponents.itemByName(name)
            if comp is not None and comp.features.baseFeatures.count:
                bf = comp.features.baseFeatures.item(0)
                bf.startEdit()
                for i, (b, bn, ak) in enumerate(bodies):
                    if i < bf.bodies.count:
                        bf.updateBody(bf.bodies.item(i), b)
                    else:
                        comp.bRepBodies.add(b, bf)
                while bf.bodies.count > len(bodies):
                    bf.bodies.item(bf.bodies.count - 1).deleteMe()
                bf.finishEdit()
                for i, (b, bn, ak) in enumerate(bodies):
                    if i < comp.bRepBodies.count:
                        comp.bRepBodies.item(i).name = bn
                        if ak and APP.get(ak):
                            comp.bRepBodies.item(i).appearance = APP[ak]
                LOG.append('patched ' + name)
                return None
        occ = parent.occurrences.addNewComponent(xform if xform else adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = name
        if parent != root:
            try: occ.isGroundToParent = True
            except Exception: pass
        if bodies:
            bf = comp.features.baseFeatures.add()
            bf.startEdit()
            for b, bn, ak in bodies:
                comp.bRepBodies.add(b, bf)
            bf.finishEdit()
            for i, (b, bn, ak) in enumerate(bodies):
                if i < comp.bRepBodies.count:
                    body = comp.bRepBodies.item(i)
                    body.name = bn
                    if ak and APP.get(ak):
                        body.appearance = APP[ak]
        LOG.append(('new ' if not PATCH else 'new (patch) ') + name)
        return occ
    def group(name):
        o = root.occurrences.itemByName(name + ':1')
        if o is not None:
            return o
        o = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        o.component.name = name
        return o

    # ======================= v7: rename the v6 plywood components, drop the parts that are now integrated =======================
    RENAME = {'C6_Main_Plate_PLY': 'C7_Main_Plate_PRINT', 'C6_Base_Board_PLY': 'C7_Base_Board_PLY', 'C6_L_Brackets': 'C7_Front_Brackets_PRINT',
              'C6_Bed_Knife': 'C7_Bed_Knife', 'C6_Bed_Ledge_PRINT': 'C7_Bed_Ledge_PRINT', 'C6_Bed_Knife_Screws': 'C7_Bed_Knife_Bolts_M6',
              'C6_Pivot_Hardware': 'C7_Pivot_Hardware', 'C6_Lever_Assy': 'C7_Lever_Assy', 'C6_Lever_PLY': 'C7_Lever_PRINT',
              'C6_Moving_Knife': 'C7_Moving_Knife', 'C6_Knife_Screws_M4': 'C7_Knife_Screws_M4', 'C6_Pivot_Bearings_688x2': 'C7_Pivot_Bearings_688x2',
              'C6_Drive_Pin_M8': 'C7_Drive_Pin_M8', 'C6_Wiper_Motor_PM11G': 'C7_Wiper_Motor_PM11G', 'C6_Motor_Bolts_M6': 'C7_Motor_Bolts_M6',
              'C6_Crank_Assy': 'C7_Crank_Assy', 'C6_Crank_PRINT': 'C7_Crank_PRINT', 'C6_Crank_Hardware': 'C7_Crank_Hardware',
              'C6_Link_PLY': 'C7_Link_PRINT', 'C6_Park_Switch': 'C7_Park_Switch', 'C6_Knife_Height_Gauge_PRINT': 'C7_Knife_Height_Gauge_PRINT'}
    for old, new in RENAME.items():
        c = design.allComponents.itemByName(old)
        if c is not None and design.allComponents.itemByName(new) is None:
            c.name = new
    lev_occ = root.occurrences.itemByName('C7_Lever_Assy:1')
    if lev_occ is not None:
        for nm in ('C6_Pivot_Hub_PRINT:1', 'C6_Drive_Boss_PRINT:1'):
            o = lev_occ.component.occurrences.itemByName(nm)
            if o is not None: o.deleteMe(); LOG.append('deleted ' + nm)

    def obround_x(x0, x1, y, z, r, dy=0.0, dz=0.0):      # slot through x: radius r, centres +-(dy, dz)
        b = uni(cylx(x0, x1, y - dy, z - dz, r), cylx(x0, x1, y + dy, z + dz, r))
        if dy: uni(b, box(x0, x1, y - dy, y + dy, z - r, z + r))
        if dz: uni(b, box(x0, x1, y - r, y + r, z - dz, z + dz))
        return b
    def tri_rib(xa, xb, y0, y1, za, zb):                 # right triangle in x-z: full height (za..zb) at x = xb, zero at x = xa
        b = box(min(xa, xb), max(xa, xb), y0, y1, za, zb)
        return inter(b, hspace((xa, 0, za), (-(zb - za) * (1 if xb > xa else -1), 0, abs(xb - xa))))

    # ======================= STATIC PARTS =======================
    # --- printed main plate: prints FRONT face down (front = flat reference for both knives); ribs, feet and pockets on the back ---
    mp = uni(box(-TP, 0, -65, 175, 0, 120),
             box(-22, -TP, -65, -29.5, 30, 80),                       # pivot block (M8 head sunk in it)
             box(-40, -TP, -65, -29.5, 0, 6), box(-40, -TP, 84, 175, 0, 6))   # back feet (wood screws into the base)
    for (y0, y1, zt) in ((-65, -60, 30), (-34.5, -29.5, 30), (84, 89, 60), (170, 175, 50)):
        uni(mp, tri_rib(-40, -TP, y0, y1, 6, zt))
    uni(mp, box(-22, -TP, -65, -60, 6, 30), box(-22, -TP, -34.5, -29.5, 6, 30))  # block legs down to the foot
    sub(mp, box(-9, 1, -10.0, 10.4, 53.0, 69.0))                     # window round the exit-guide nose
    sub(mp, cylx(-41, 1, YP, ZP, 4.1), hexp('x', -41, PIV_HEAD, YP, ZP, 13.4))   # M8 pivot bolt, head held in a hex pocket
    for (y, z) in [(-23, 70), (21, 44)]:                             # M4 countersunk into the feed frame (self-tap, 10 deep)
        sub(mp, cylx(-9, 1, y, z, 2.25), cyl((0.02, y, z), (-2.2, y, z), 4.4, 2.25))
    for su in SLOT_U:                                                # bed knife: M6 through the blade U-slots, nut slides in a back pocket
        y = YA + su
        sub(mp, obround_x(-9, 1, y, 40.0, 3.3, dy=5.0), box(-TP - 0.1, -2.8, y - 11.2, y + 11.2, 40.0 - 5.1, 40.0 + 5.1))
    for y in LEDGE_Y:                                                # ledge: M4 + nut
        sub(mp, cylx(-9, 1, y, ZB - BW - 4, 2.2), hexp('x', -TP - 0.1, -4.6, y, ZB - BW - 4, 7.2))
    sub(mp, cylx(-9, 1, CY, CZ, 7.5))                                # 15 mm hole for the motor shaft
    for a in BOSS_ANG:                                               # M6 countersunk into the gearbox bosses
        y, z = CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a))
        sub(mp, cylx(-9, 1, y, z, 3.3), cyl((0.02, y, z), (-3.2, y, z), 6.5, 3.3))
    for (y, z) in SW_HOLES:
        sub(mp, cylx(-9, 1, y, z, 1.0))
    for y0 in BRK_Y:                                                 # front brackets: M5 + nut pocket at the back
        sub(mp, cylx(-9, 1, y0 + 10, 18.0, 2.75), hexp('x', -TP - 0.1, -3.8, y0 + 10, 18.0, 8.2))
    for (x, y) in FOOT_SCREWS:
        sub(mp, cylz(-1, 7, x, y, 2.4), cyl((x, y, 6.02), (x, y, 3.6), 4.8, 2.4))
    mkcomp(root, 'C7_Main_Plate_PRINT', [(mp, 'main plate (PETG-CF, prints front face down)', 'CF')])

    bb = box(-135, 150, -95, 180, -8, 0)
    mkcomp(root, 'C7_Base_Board_PLY', [(bb, 'base board (plywood)', 'PLY')])

    # --- printed front brackets (plate -> base), one M5 into the plate, one wood screw into the base ---
    brk = []
    for y0 in BRK_Y:
        b = uni(box(0, 6, y0, y0 + 20, 0, 30), box(0, 36, y0, y0 + 20, 0, 6),
                tri_rib(36, 6, y0, y0 + 4, 6, 30), tri_rib(36, 6, y0 + 16, y0 + 20, 6, 30))
        sub(b, cylx(-1, 7, y0 + 10, 18.0, 2.75), cylz(-1, 7, 24, y0 + 10, 2.4), cyl((24, y0 + 10, 6.02), (24, y0 + 10, 3.6), 4.8, 2.4))
        brk.append((b, 'front bracket', 'CF'))
    mkcomp(root, 'C7_Front_Brackets_PRINT', brk)

    # --- bed knife (fixed): flat face at x = 2.88 (shear plane), bevel toward the plate, edge at ZB ---
    bk = box(0, BT, YA, YA + BL, ZB - BW, ZB)
    inter(bk, hspace((BT, 0, ZB), (-BEV, 0, BT)))
    for su in SLOT_U:
        y = YA + su
        sub(bk, cylx(-1, BT + 1, y, ZB - SLOT_END - 3.3, 3.3), box(-1, BT + 1, y - 3.3, y + 3.3, ZB - BW - 1, ZB - SLOT_END - 3.3))
    for hu in HOLE_U:
        sub(bk, cylx(-1, BT + 1, YA + hu, ZB - BW + HOLE_BACK, 1.65))
    mkcomp(root, 'C7_Bed_Knife', [(bk, 'bed knife (planer blade 82 x 28.75 x 2.88)', 'BLADE')])

    # --- printed ledge under the bed knife (height adjustable in its slots; set with the gauge) ---
    ld = box(0, 6.5, YA + 3, YA + BL - 3, ZB - BW - 8, ZB - BW)
    for y in LEDGE_Y:
        sub(ld, obround_x(-1, 7.5, y, ZB - BW - 4, 2.25, dz=1.5))
    mkcomp(root, 'C7_Bed_Ledge_PRINT', [(ld, 'bed knife ledge', 'CF')])

    bks = []
    for su in SLOT_U:
        y = YA + su; z = 40.0
        bks.append((uni(ring_x(BT, BT + 1.6, y, z, 6.0, 3.2), cylx(BT + 1.6, BT + 4.9, y, z, 5.25), cylx(BT + 1.6 - 12, BT + 1.61, y, z, 3.0)), 'M6x12 button head + washer', 'STEEL'))
        bks.append((sub(hexp('x', -TP, -3.0, y, z, 10), cylx(-9, -2, y, z, 3.0)), 'M6 nut (in the back pocket)', 'STEEL'))
    for y in LEDGE_Y:
        z = ZB - BW - 4
        bks.append((uni(cylx(6.5, 8.7, y, z, 3.8), cylx(6.5 - 14, 6.51, y, z, 2.0)), 'M4x14 button head (ledge)', 'STEEL'))
    mkcomp(root, 'C7_Bed_Knife_Bolts_M6', bks)

    # --- pivot hardware (static): M8 x 60, head in the plate's hex pocket, nut on the front face ---
    N0 = HUB1                                                         # front bearing face
    pv = [(uni(hexp('x', PIV_HEAD - 5.3, PIV_HEAD, YP, ZP, 13), cylx(PIV_HEAD - 0.01, PIV_HEAD + 60, YP, ZP, 4)), 'M8x60 hex bolt (lever pivot)', 'STEEL'),
          (sub(hexp('x', 0, 6.5, YP, ZP, 13), cylx(-1, 8, YP, ZP, 4)), 'M8 nut (clamps bolt to plate)', 'STEEL'),
          (ring_x(N0, N0 + 1.6, YP, ZP, 8, 4.2), 'M8 washer', 'STEEL'),
          (ring_x(N0 + 1.6, N0 + 7.6, YP, ZP, 8, 4.2), 'rubber washers x2 (knife preload)', 'RUBBER'),
          (ring_x(N0 + 7.6, N0 + 9.2, YP, ZP, 8, 4.2), 'M8 washer', 'STEEL'),
          (sub(hexp('x', N0 + 9.2, N0 + 17.2, YP, ZP, 13), cylx(N0 + 8, N0 + 18, YP, ZP, 4)), 'M8 nylock', 'STEEL')]
    mkcomp(root, 'C7_Pivot_Hardware', pv)

    # ======================= MOVING LEVER GROUP (modelled at park angle TH_REF) =======================
    g = group('C7_Lever_Assy'); gc = g.component
    dy, dz = L(DU, DV)
    lv = uni(cylx(XL0, XL1, *L(0, 0), 20.0), box(XL0, XL1, YP, YP + LEV_LEN - 16, ZP + 2, ZP + 34), cylx(XL0, XL1, *L(LEV_LEN - 16, 18), 16.0),
             cylx(XL1, HUB1, *L(0, 0), 13.0),                                    # bearing hub
             cylx(XL1, XB1, dy, dz, 11.0), cylx(XB1, XB1 + NOSE, dy, dz, 5.25))  # drive-pin boss + nose for the bearing inner ring
    sub(lv, cylx(XL0 - 0.1, 8.0, *L(0, 0), 8.6),                                 # room for the M8 nut on the plate
        cylx(7.99, 13.1, *L(0, 0), BRG_R), cylx(XL0 - 1, HUB1 + 1, *L(0, 0), 6.0), cylx(HUB1 - 5.1, HUB1 + 0.1, *L(0, 0), BRG_R))
    sub(lv, hexp('x', XL0 - 0.1, XL0 + 5.6, dy, dz, 13.3), cylx(XL0, XB1 + NOSE + 1, dy, dz, 4.15))   # M8 head pocket at the back, stud to the front
    for hu in HOLE_U:                                                            # knife clamp screws: slotted (blade hole positions are estimates)
        y, z = L(U0 + hu, BW - E_OFF - HOLE_BACK)
        sub(lv, obround_x(XL0 - 1, XL1 + 1, y, z, 4.0, dy=2.5), obround_x(XL1 - 3.0, XL1 + 1, y, z, 6.5, dy=2.5))
    for u in STOP_U:                                                             # stop grub screws for the blade's back edge
        sub(lv, cylx(XL0 - 1, XL1 + 0.1, *L(u, BW - E_OFF + 2.0), 1.75))
    mkcomp(gc, 'C7_Lever_PRINT', [(rot_lever(lv), 'knife lever (PETG-CF, 2 x 688ZZ)', 'CF')])

    mk = box(BT, 2 * BT, YP + U0, YP + U0 + BL, ZP - E_OFF, ZP - E_OFF + BW)
    inter(mk, hspace((BT, 0, ZP - E_OFF), (BEV, 0, -BT)))
    for su in SLOT_U:
        y = YP + U0 + su
        sub(mk, cylx(BT - 1, 2 * BT + 1, y, ZP - E_OFF + SLOT_END + 3.3, 3.3),
            box(BT - 1, 2 * BT + 1, y - 3.3, y + 3.3, ZP - E_OFF + SLOT_END + 3.3, ZP - E_OFF + BW + 1))
    for hu in HOLE_U:
        sub(mk, cylx(BT - 1, 2 * BT + 1, *L(U0 + hu, BW - E_OFF - HOLE_BACK), 1.65))
    mkcomp(gc, 'C7_Moving_Knife', [(rot_lever(mk), 'moving knife (planer blade)', 'BLADE')])

    ks = []
    XF = XL1 - 3.0
    for hu in HOLE_U:
        y, z = L(U0 + hu, BW - E_OFF - HOLE_BACK)
        ks.append((rot_lever(uni(ring_x(XF, XF + 1.0, y, z, 6.0, 2.2), cylx(XF + 1.0, XF + 5.0, y, z, 3.5), cylx(XF + 1.0 - 10, XF + 1.01, y, z, 2.0))),
                   'M4x10 cap screw + 12 mm washer', 'STEEL'))
    for u in STOP_U:
        y, z = L(u, BW - E_OFF + 2.0)
        ks.append((rot_lever(cylx(XL0 - 2.0, XL0 + 10.0, y, z, 2.0)), 'M4x12 grub screw (blade stop)', 'DARK'))
    mkcomp(gc, 'C7_Knife_Screws_M4', ks)

    def brg(x0, y, z, lever=True):
        b = ring_x(x0, x0 + 5, y, z, 8, 4)
        sub(b, ring_x(x0 + 4.6, x0 + 6, y, z, 6.9, 5.3), ring_x(x0 - 1, x0 + 0.4, y, z, 6.9, 5.3))
        return rot_lever(b) if lever else b
    mkcomp(gc, 'C7_Pivot_Bearings_688x2', [(brg(8.05, *L(0, 0)), '688ZZ', 'STEEL'), (brg(HUB1 - 5.0, *L(0, 0)), '688ZZ', 'STEEL')])

    def pin_stack(y, z, x_head, rot):
        f = (lambda b: rot_lever(b)) if rot else (lambda b: b)
        return [(f(uni(hexp('x', x_head, x_head + 5.3, y, z, 13), cylx(x_head + 5.29, x_head + 5.3 + 45, y, z, 4))), 'M8x45 hex bolt (head trapped)', 'STEEL'),
                (f(ring_x(XK0 + 10.0, XK0 + 12.5, y, z, 5.25, 4.15)), 'printed spacer ring', 'CF'),
                (f(ring_x(XK0 + 12.5, XK0 + 14.1, y, z, 8, 4.2)), 'M8 washer', 'STEEL'),
                (f(sub(hexp('x', XK0 + 14.1, XK0 + 22.1, y, z, 13), cylx(XK0 + 13, XK0 + 23, y, z, 4))), 'M8 nylock', 'STEEL')]
    mkcomp(gc, 'C7_Drive_Pin_M8', pin_stack(dy, dz, XL0, True))

    # ======================= DRIVE: wiper motor, crank, link, park switch =======================
    DO = world_D(TH_OPEN)
    PO = (CY + R_CR * math.cos(PHI_O), CZ + R_CR * math.sin(PHI_O))
    ur = (math.cos(PHI_O), math.sin(PHI_O))
    wm = []
    for a in BOSS_ANG:
        y, z = CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a))
        wm.append((sub(cylx(-30, -TP, y, z, 6.3), cylx(-20, -7, y, z, 2.5)), 'gearbox boss (M6)', 'AL'))
    col = TIP - 36.0
    wm.append((uni(cylx(-44, -28, CY, CZ, 34.0), cylx(-28, col, CY, CZ, 11.0)), 'gearbox (approx.)', 'AL'))
    wm.append((uni(cylz(CZ + 18, CZ + 28, -42, CY + 22, 31.0), cylz(CZ + 28, CZ + 140, -42, CY + 22, 29.0)), 'motor body (approx.)', 'DARK'))
    wm.append((sub(cylx(col, TIP, CY, CZ, 5.0), cylx(TIP - 5, TIP + 1, CY, CZ, 1.7)), 'output shaft 10 mm (M4 in the end)', 'STEEL'))
    mkcomp(root, 'C7_Wiper_Motor_PM11G', wm)
    mb = []
    for a in BOSS_ANG:
        y, z = CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a))
        mb.append((uni(cyl((0.0, y, z), (-3.2, y, z), 6.0, 3.0), cylx(-20, -3.1, y, z, 3.0)), 'M6x20 countersunk', 'STEEL'))
    mkcomp(root, 'C7_Motor_Bolts_M6', mb)

    # --- printed crank (modelled at the knife-open position); the M4 set screw + nut slide along the shaft to find the slot ---
    cg = group('C7_Crank_Assy'); cgc = cg.component
    web_c = (0.5 * (ARM0 + ARM1), CY + 0.5 * R_CR * ur[0], CZ + 0.5 * R_CR * ur[1])
    us = (-ur[0], -ur[1]); ts = (-us[1], us[0])                 # set screw opposite the pin
    ck = uni(cylx(ARM0, ARM1, CY, CZ, 13.0), cylx(ARM0, ARM1, *PO, 11.0),
             obox(web_c, (0, ur[0], ur[1]), (0, -ur[1], ur[0]), R_CR, 20.0, ARM1 - ARM0),
             cylx(ARM1, HUBX, CY, CZ, 11.0), cylx(ARM1, XB1, *PO, 8.5), cylx(XB1, XB1 + NOSE, *PO, 5.25),
             obox((0.5 * (ARM0 + HUBX), CY + 9.25 * us[0], CZ + 9.25 * us[1]), (0, us[0], us[1]), (0, ts[0], ts[1]), 10.5, 14.0, HUBX - ARM0))
    sub(ck, cylx(ARM0 - 1, HUBX + 1, CY, CZ, BORE_R))                         # shaft bore
    sub(ck, cylx(HUBX, XB1 + NOSE + 1, CY, CZ, 6.8))                           # room for the end washer + screw
    sub(ck, cylx(ARM0 - 1, XB1 + NOSE + 1, *PO, 4.15), hexp('x', ARM0 - 0.1, ARM0 + 5.5, *PO, 13.3))
    sub(ck, obox((0.5 * (2.5 + HUBX + 0.1), CY + 8.65 * us[0], CZ + 8.65 * us[1]), (0, us[0], us[1]), (0, ts[0], ts[1]), 3.5, 7.3, HUBX + 0.1 - 2.5))   # M4 nut channel, open at the hub end
    for xs in (SS_X0, SS_X1):
        sub(ck, cyl((xs, CY + 3.5 * us[0], CZ + 3.5 * us[1]), (xs, CY + 16 * us[0], CZ + 16 * us[1]), 2.2))
    sub(ck, obox((0.5 * (SS_X0 + SS_X1), CY + 9.75 * us[0], CZ + 9.75 * us[1]), (0, us[0], us[1]), (0, ts[0], ts[1]), 12.5, 4.4, SS_X1 - SS_X0))   # screw slot along the shaft
    mkcomp(cgc, 'C7_Crank_PRINT', [(ck, 'crank (r 13.3, PETG-CF)', 'CF')])
    ch = pin_stack(PO[0], PO[1], ARM0, False) + [
          (uni(ring_x(TIP, TIP + 1.0, CY, CZ, 6.0, 2.2), cylx(TIP + 1.0, TIP + 3.2, CY, CZ, 3.8), cylx(TIP - 5, TIP + 1.01, CY, CZ, 2.0)), 'M4x6 button head + 12 mm washer', 'STEEL'),
          (cyl((X_SS, CY + 3.9 * us[0], CZ + 3.9 * us[1]), (X_SS, CY + 15.9 * us[0], CZ + 15.9 * us[1]), 2.0), 'M4x12 grub screw (+ M4 nut in the channel)', 'DARK')]
    mkcomp(cgc, 'C7_Crank_Hardware', ch)

    # --- printed link with 2 x 688ZZ at each end (x XK0..XK1; 0.8 lip on the outer face keeps the bearings in) ---
    ld_ = (DO[0] - PO[0], DO[1] - PO[1]); ln = math.hypot(*ld_); ul = (ld_[0] / ln, ld_[1] / ln)
    lk = uni(cylx(XK0, XK1, *PO, 14.0), cylx(XK0, XK1, *DO, 14.0),
             obox((0.5 * (XK0 + XK1), 0.5 * (PO[0] + DO[0]), 0.5 * (PO[1] + DO[1])), (0, ul[0], ul[1]), (0, -ul[1], ul[0]), ln, 22.0, XK1 - XK0))
    for p in (PO, DO):
        sub(lk, cylx(XK0 - 0.1, XK0 + 10.0, *p, BRG_R), cylx(XK0 + 9.9, XK1 + 0.1, *p, 6.9))
    lkb = [(lk, 'link (PETG-CF, %.1f c/c, 4 x 688ZZ)' % ln, 'CF')]
    for p in (PO, DO):
        for x0 in (XK0, XK0 + 5.0):
            lkb.append((brg(x0, p[0], p[1], False), '688ZZ', 'STEEL'))
    mkcomp(root, 'C7_Link_PRINT', lkb)
    LOG.append('link c/c %.2f (want %.2f)' % (ln, L_LK))

    uo = (math.cos(PHI_O), math.sin(PHI_O)); to = (-uo[1], uo[0])
    def at(rad, tan): return (CY + rad * uo[0] + tan * to[0], CZ + rad * uo[1] + tan * to[1])
    swb = obox((3.2, *at(SW_R + 7.5, 12.0)), (0, to[0], to[1]), (0, uo[0], uo[1]), 20.0, 10.0, 6.4)
    for (y, z) in SW_HOLES: sub(swb, cylx(-1, 8, y, z, 1.1))
    swl = obox((3.2, *at(SW_R + 2.2, 9.0)), (0, to[0], to[1]), (0, uo[0], uo[1]), 18.0, 0.6, 4.0)
    swr = cylx(1.0, 5.4, *at(SW_R, 0.0), 2.5)
    mkcomp(root, 'C7_Park_Switch', [(uni(swb, swl, swr), 'KW11 roller microswitch', 'DARK')])

    # --- print-only parts (hidden in the model) ---
    gz = uni(box(-14, 10, -6.3, 6.3, 59.8, 65.4), box(0, 10, -12, 12, 65.4, 68.4))
    og = mkcomp(root, 'C7_Knife_Height_Gauge_PRINT', [(gz, 'knife height gauge', 'CF')])
    if og: og.isLightBulbOn = False
    # thin motor test template: same holes as the main plate (shaft hole snug here), long tab = motor body direction
    tm = uni(cylx(-TP - 2.4, -TP, CY, CZ, 11.0), box(-TP - 2.4, -TP, CY - 3.5, CY + 3.5, CZ, CZ + 26.0))
    for a in BOSS_ANG:
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        y, z = CY + BOSS_R * ca, CZ + BOSS_R * sa
        uni(tm, cylx(-TP - 2.4, -TP, y, z, 9.0), obox((-TP - 1.2, CY + 0.5 * BOSS_R * ca, CZ + 0.5 * BOSS_R * sa), (0, ca, sa), (0, -sa, ca), BOSS_R, 12.0, 2.4))
    sub(tm, cylx(-TP - 3, -TP + 1, CY, CZ, 5.2))
    for a in BOSS_ANG:
        sub(tm, cylx(-TP - 3, -TP + 1, CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a)), 3.3))
    ot = mkcomp(root, 'C7_Motor_Template_PRINT', [(tm, 'motor test template (2.4 mm)', 'CF')])
    if ot: ot.isLightBulbOn = False
    # fit-test coupon (prints with the template): bearing seat, crank bore, M8 clearance - same diameters as the real parts
    ft = box(-200, -195, -8, 44, -12, 12)
    sub(ft, cylx(-201, -194, 6, 0, BRG_R), cylx(-201, -194, 25, 0, BORE_R), cylx(-201, -194, 37, 0, 4.15))
    of = mkcomp(root, 'C7_Fit_Test_PRINT', [(ft, 'fit test: 16.2 bearing / 10.35 shaft / 8.3 bolt', 'CF')])
    if of: of.isLightBulbOn = False
    sp = ring_x(0, 2.5, 0, 0, 5.25, 4.15)
    os_ = mkcomp(root, 'C7_Pin_Spacer_PRINT', [(sp, 'pin spacer ring 10.5 x 8.3 x 2.5', 'CF')])
    if os_: os_.isLightBulbOn = False

    # ======================= pinch yoke v6 (PETG-CF): thicker crossbar + riser, M5 tie bolt along the crossbar =======================
    XR, ZPN, PVX, PVZ, TNX, TNY, STX = -45.0, 77.0, -77.0, 77.0, -20.0, -14.6, -58.0
    Y0, Y1, YP0, YP1 = -19.0, -10.2, 9.6, 17.1
    def cyly(y0, y1, x, z, r): return cyl((x, y0, z), (x, y1, z), r)
    def hexy(y0, y1, x, z, af):
        r = af / 2.0 / math.cos(math.pi / 6); b = None
        for k in range(3):
            a = math.pi / 3 * k; ca, sa = math.cos(a), math.sin(a)
            bb = obox((x, (y0 + y1) / 2, z), (ca, 0, sa), (0, 1, 0), 2 * r, abs(y1 - y0), af)
            b = bb if b is None else inter(b, bb)
        return b
    gus = tri_rib(-29, -35, Y0, Y1, 84, 90)                                  # gusset riser -> arm
    arm = uni(cyly(Y0, 9.0, PVX, PVZ, 8),                                   # pivot tube, rides on the sleeve
              cyly(Y0, -9.6, XR, ZPN, 11),                                  # -y axle boss
              box(-77, -27, Y0, Y1, 70, 84), box(-27, -12, Y0, Y1, 70, 85),
              box(-51, -35, Y0, Y1, 80, 104),                               # riser (was 12 wide, now 16)
              box(-51, -35, Y0, YP1, 94, 104),                              # crossbar 16 x 10 (was 12 x 6)
              cyly(YP0, YP1, XR, ZPN, 10.5), box(XR - 10.5, XR + 10.5, YP0, YP1, ZPN, 104),   # +y plate
              gus)
    sub(arm, cyly(Y0 - 1, 10, PVX, PVZ, 4.7),
        cyly(Y0 - 1, YP1 + 1, XR, ZPN, 4.2),
        hexy(11.7, YP1 + 1, XR, ZPN, 13.3),
        cylz(60, 95, TNX - 2.0, TNY, 2.75), cylz(60, 95, TNX + 2.0, TNY, 2.75), box(TNX - 2.0, TNX + 2.0, TNY - 2.75, TNY + 2.75, 60, 95),
        cylz(60, 95, STX, TNY, 1.7),
        cyly(Y0 - 1, YP1 + 1, TIE_X, TIE_Z, 2.75), hexy(YP1 - 4.3, YP1 + 1, TIE_X, TIE_Z, 8.2))   # M5 tie bolt + nut pocket
    mkcomp(None, 'Pinch_Arm_PRINT', [(arm, 'pinch arm (yoke) v6 PETG-CF', 'CF')])
    pa = root.occurrences.itemByName('Pinch_Arm_Assy:1')
    if pa is not None:
        tie = [(uni(cyly(Y0 - 6.0, Y0 - 1.0, TIE_X, TIE_Z, 4.25), cyly(Y0 - 1.0, Y0, TIE_X, TIE_Z, 5.0),
                    cyly(Y0 - 0.01, Y0 - 1.0 + 40.0, TIE_X, TIE_Z, 2.5)), 'M5x40 cap screw + washer (tie bolt)', 'STEEL'),
               (sub(hexy(YP1 - 4.2, YP1 - 0.2, TIE_X, TIE_Z, 8), cyly(YP1 - 5, YP1 + 1, TIE_X, TIE_Z, 2.5)), 'M5 nut', 'STEEL')]
        mkcomp(pa.component, 'Pinch_Tie_Bolt_M5', tie)
    LOG.append('v7 done')
