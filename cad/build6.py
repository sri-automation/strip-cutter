# Strip Cutter v6 - PLYWOOD DEMO CUTTER (lever shear with the user's two 82 x 28.75 x 2.88 planer blades)
# Adds new components beside the v5.1 feeder in "Strip Cutter v3 (feeder)". Coordinates as the feeder model (mm):
#   x = feed direction (plywood main plate front face at x = 0), y = across (+y motor side), z = up (base board top z = 0)
# Shear plane x = 2.88: bed knife x 0..2.88 (bevel toward the plate), moving knife x 2.88..5.76 (bevel toward the lever).
# PATCH = True updates the bodies of existing C6_ components in place (keeps joints).
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
XL0, XL1 = 2 * BT, 2 * BT + 8.0            # plywood lever x 5.76 .. 13.76
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
XB1 = 26.4                                  # top of the drive boss / crank-pin boss
XK0, XK1 = XB1 + 1.6, XB1 + 1.6 + 8.0       # plywood link x range (one M8 washer under it)
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
           'RUBBER': app_named('Rubber washer'), 'DARK': app_named('Black oxide'), 'AL': app_named('Aluminium plate')}
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

    # ======================= STATIC PARTS =======================
    # --- plywood main plate (8 mm), against the end of the feed frame ---
    mp = box(-8, 0, -65, 175, 0, 120)
    sub(mp, box(-9, 1, -10.0, 10.4, 53.0, 69.0))                    # window round the exit-guide nose
    sub(mp, cylx(-9, 1, YP, ZP, 4.1))                                # M8 pivot bolt
    for (y, z) in [(-23, 70), (21, 44)]:                             # M4 countersunk into the feed frame
        sub(mp, cylx(-9, 1, y, z, 2.25), cyl((0.02, y, z), (-2.2, y, z), 4.4, 2.25))
    sub(mp, cylx(-9, 1, CY, CZ, 7.5))                                  # 15 mm hole for the motor shaft
    for a in BOSS_ANG:                                                 # M6 countersunk into the gearbox bosses
        y, z = CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a))
        sub(mp, cylx(-9, 1, y, z, 3.25), cyl((0.02, y, z), (-3.2, y, z), 6.4, 3.25))
    for (y, z) in SW_HOLES:                                            # park switch screws
        sub(mp, cylx(-9, 1, y, z, 1.1))
    mkcomp(root, 'C6_Main_Plate_PLY', [(mp, 'main plate (8 mm plywood)', 'PLY')])

    # --- plywood base board (8 mm) under feeder + cutter ---
    bb = box(-135, 150, -95, 180, -8, 0)
    mkcomp(root, 'C6_Base_Board_PLY', [(bb, 'base board (8 mm plywood)', 'PLY')])
    # L-brackets (user's wood brackets, placeholder 40 x 40 x 20 x 2)
    brk = []
    for y0 in (-62, 48, 152):
        brk.append((uni(box(0, 2, y0, y0 + 20, 0, 25), box(0, 25, y0, y0 + 20, 0, 2)), 'L-bracket (yours)', 'STEEL'))
    mkcomp(root, 'C6_L_Brackets', brk)

    # --- bed knife (fixed): flat face at x = 2.88 (shear plane), bevel toward the plate, edge at ZB ---
    bk = box(0, BT, YA, YA + BL, ZB - BW, ZB)
    inter(bk, hspace((BT, 0, ZB), (-BEV, 0, BT)))                   # 38 deg bevel on the plate side
    for su in SLOT_U:
        y = YA + su
        sub(bk, cylx(-1, BT + 1, y, ZB - SLOT_END - 3.3, 3.3), box(-1, BT + 1, y - 3.3, y + 3.3, ZB - BW - 1, ZB - SLOT_END - 3.3))
    for hu in HOLE_U:
        sub(bk, cylx(-1, BT + 1, YA + hu, ZB - BW + HOLE_BACK, 1.65))
    mkcomp(root, 'C6_Bed_Knife', [(bk, 'bed knife (planer blade 82 x 28.75 x 2.88)', 'BLADE')])

    # --- printed ledge under the bed knife (sets its height; takes the cutting load) ---
    ld = box(0, 6.5, YA + 3, YA + BL - 3, ZB - BW - 8, ZB - BW)
    for y in (YA + 11, YA + 41, YA + 71):
        zc = ZB - BW - 4
        sub(ld, cylx(-1, 7.5, y, zc + 1.5, 1.9), cylx(-1, 7.5, y, zc - 1.5, 1.9), box(-1, 7.5, y - 1.9, y + 1.9, zc - 1.5, zc + 1.5))  # 3.8 x 6.8 slot
    mkcomp(root, 'C6_Bed_Ledge_PRINT', [(ld, 'bed knife ledge', 'BLUE')])

    # --- bed knife screws: 3.5 x 12 wood screws + M6 washers through the U-slots ---
    bks = []
    for su in SLOT_U:
        y = YA + su; z = 40.0
        bks.append((uni(ring_x(BT, BT + 1.6, y, z, 6.0, 3.2), cylx(BT + 1.6, BT + 4.1, y, z, 3.5), cylx(BT + 1.6 - 12, BT + 1.61, y, z, 1.75)),
                    'wood screw 3.5x12 + M6 washer', 'STEEL'))
    mkcomp(root, 'C6_Bed_Knife_Screws', bks)

    # --- pivot hardware (static: bolt clamped to the plate) ---
    pv = [(uni(hexp('x', -14.9, -9.6, YP, ZP, 13), cylx(-9.61, 51.0, YP, ZP, 4)), 'M8x60 hex bolt (lever pivot)', 'STEEL'),
          (ring_x(-9.6, -8.0, YP, ZP, 12, 4.2), 'M8 large washer (back)', 'STEEL'),
          (sub(hexp('x', 0, 6.5, YP, ZP, 13), cylx(-1, 8, YP, ZP, 4)), 'M8 nut (clamps bolt to plate)', 'STEEL'),
          (ring_x(32.0, 33.6, YP, ZP, 8, 4.2), 'M8 washer', 'STEEL'),
          (ring_x(33.6, 39.6, YP, ZP, 8, 4.2), 'rubber washers x2 (knife preload)', 'RUBBER'),
          (ring_x(39.6, 41.2, YP, ZP, 8, 4.2), 'M8 washer', 'STEEL'),
          (sub(hexp('x', 41.2, 49.2, YP, ZP, 13), cylx(40, 50, YP, ZP, 4)), 'M8 nylock', 'STEEL')]
    mkcomp(root, 'C6_Pivot_Hardware', pv)

    # ======================= MOVING LEVER GROUP (modelled at park angle TH_REF) =======================
    g = group('C6_Lever_Assy'); gc = g.component
    # plywood lever: disc round the pivot + bar, rounded end
    lv = uni(cylx(XL0, XL1, *L(0, 0), 20.0), box(XL0, XL1, YP, YP + LEV_LEN - 16, ZP + 2, ZP + 34), cylx(XL0, XL1, *L(LEV_LEN - 16, 18), 16.0))
    sub(lv, cylx(XL0 - 1, XL1 + 1, *L(0, 0), 8.25))                  # 16.5 hole: clears the M8 nut that clamps the bolt to the plate
    for hu in HOLE_U:
        sub(lv, cylx(XL0 - 1, XL1 + 1, *L(U0 + hu, BW - E_OFF - HOLE_BACK), 2.25))   # M4 to the knife (mark from the blade)
    for a in HUB_SCREW_ANG:
        sub(lv, cylx(XL0 - 1, XL1 + 1, *L(16 * math.cos(math.radians(a)), 16 * math.sin(math.radians(a))), 1.4))  # pilot for hub screws
    dy0, dz0 = L(DU, DV)
    for a in DB_SCREW_ANG:
        sub(lv, cylx(XL0 - 1, XL1 + 1, dy0 + 11 * math.cos(math.radians(a)), dz0 + 11 * math.sin(math.radians(a)), 1.4))
    mkcomp(gc, 'C6_Lever_PLY', [(rot_lever(lv), 'lever (8 mm plywood)', 'PLY')])

    # moving knife: flat face x 2.88 (touches the bed knife), bevel on the lever side, edge at v = -E_OFF
    mk = box(BT, 2 * BT, YP + U0, YP + U0 + BL, ZP - E_OFF, ZP - E_OFF + BW)
    inter(mk, hspace((BT, 0, ZP - E_OFF), (BEV, 0, -BT)))
    for su in SLOT_U:
        y = YP + U0 + su
        sub(mk, cylx(BT - 1, 2 * BT + 1, y, ZP - E_OFF + SLOT_END + 3.3, 3.3),
            box(BT - 1, 2 * BT + 1, y - 3.3, y + 3.3, ZP - E_OFF + SLOT_END + 3.3, ZP - E_OFF + BW + 1))
    for hu in HOLE_U:
        sub(mk, cylx(BT - 1, 2 * BT + 1, *L(U0 + hu, BW - E_OFF - HOLE_BACK), 1.65))
    mkcomp(gc, 'C6_Moving_Knife', [(rot_lever(mk), 'moving knife (planer blade)', 'BLADE')])

    # M4 x 12 + 2 washers from the lever front into the knife's threaded holes (tip stays 0.5 short of the flat face)
    ks = []
    for hu in HOLE_U:
        y, z = L(U0 + hu, BW - E_OFF - HOLE_BACK)
        ks.append((rot_lever(uni(ring_x(XL1, XL1 + 1.6, y, z, 4.5, 2.2), cylx(XL1 + 1.6, XL1 + 4.4, y, z, 3.6), cylx(XL1 + 1.6 - 12, XL1 + 1.61, y, z, 2.0))),
                   'M4x12 + 2 washers', 'STEEL'))
    mkcomp(gc, 'C6_Knife_Screws_M4', ks)

    # printed pivot hub: tube through the lever hole (2 x 688ZZ, 14 mm apart) + flange screwed to the lever front
    HB1 = XL1 + 18.24                                                # hub front end (x 32.0)
    hub = uni(cylx(XL1, HB1, *L(0, 0), 12.0), cylx(XL1, XL1 + 4.0, *L(0, 0), 22.0))   # prints flange-down, no supports
    sub(hub, cylx(XL1 - 0.1, XL1 + 5.24, *L(0, 0), 8.075), cylx(HB1 - 5.0, HB1 + 0.1, *L(0, 0), 8.075), cylx(XL1 - 1, HB1 + 1, *L(0, 0), 6.25))
    for a in HUB_SCREW_ANG:
        y, z = L(16 * math.cos(math.radians(a)), 16 * math.sin(math.radians(a)))
        sub(hub, cylx(XL1 - 1, XL1 + 5, y, z, 1.9), cylx(XL1 + 2.5, XL1 + 5, y, z, 3.6))
    mkcomp(gc, 'C6_Pivot_Hub_PRINT', [(rot_lever(hub), 'pivot hub (2 x 688ZZ)', 'BLUE')])
    def brg(x0):
        b = ring_x(x0, x0 + 5, *L(0, 0), 8, 4)
        sub(b, ring_x(x0 + 4.6, x0 + 6, *L(0, 0), 6.9, 5.3), ring_x(x0 - 1, x0 + 0.4, *L(0, 0), 6.9, 5.3))
        return rot_lever(b)
    mkcomp(gc, 'C6_Pivot_Bearings_688x2', [(brg(XL1 + 0.24), '688ZZ', 'STEEL'), (brg(HB1 - 5.0), '688ZZ', 'STEEL')])

    # printed drive-pin boss on the lever front: traps an M8 bolt head (stud points +x for the link), 3 wood screws
    dy, dz = L(DU, DV)
    db = cylx(XL1, XB1, dy, dz, 14.0)
    sub(db, hexp('x', XL1 - 0.1, XL1 + 5.5, dy, dz, 13.3), cylx(XL1, XB1 + 1, dy, dz, 4.15))
    for a in DB_SCREW_ANG:
        yy, zz = dy + 11 * math.cos(math.radians(a)), dz + 11 * math.sin(math.radians(a))
        sub(db, cylx(XL1 - 1, XB1 + 1, yy, zz, 1.9), cylx(XL1 + 6.0, XB1 + 1, yy, zz, 3.6))
    mkcomp(gc, 'C6_Drive_Boss_PRINT', [(rot_lever(db), 'drive-pin boss', 'BLUE')])
    mkcomp(gc, 'C6_Drive_Pin_M8', [(rot_lever(uni(hexp('x', XL1, XL1 + 5.3, dy, dz, 13), cylx(XL1 + 5.29, XL1 + 5.3 + 45, dy, dz, 4))), 'M8x45 hex bolt (link pin, head trapped)', 'STEEL'),
                                   (rot_lever(ring_x(XB1, XK0, dy, dz, 8, 4.2)), 'M8 washer', 'STEEL'),
                                   (rot_lever(ring_x(XK1, XK1 + 1.6, dy, dz, 8, 4.2)), 'M8 washer', 'STEEL'),
                                   (rot_lever(sub(hexp('x', XK1 + 1.6, XK1 + 9.6, dy, dz, 13), cylx(XK1, XK1 + 11, dy, dz, 4))), 'M8 nylock', 'STEEL')])


    # ======================= DRIVE: wiper motor, crank, link, park switch =======================
    DO = world_D(TH_OPEN)
    PO = (CY + R_CR * math.cos(PHI_O), CZ + R_CR * math.sin(PHI_O))
    ur = (math.cos(PHI_O), math.sin(PHI_O))
    # --- wiper motor (APPROXIMATE outline for clearance only) ---
    wm = []
    for a in BOSS_ANG:
        y, z = CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a))
        wm.append((sub(cylx(-30, -8, y, z, 6.3), cylx(-20, -7, y, z, 2.5)), 'gearbox boss (M6)', 'AL'))
    col = TIP - 36.0
    wm.append((uni(cylx(-44, -28, CY, CZ, 34.0), cylx(-28, col, CY, CZ, 11.0)), 'gearbox (approx.)', 'AL'))
    wm.append((uni(cylz(CZ + 18, CZ + 28, -42, CY + 22, 31.0), cylz(CZ + 28, CZ + 140, -42, CY + 22, 29.0)), 'motor body (approx.)', 'DARK'))
    wm.append((sub(cylx(col, TIP, CY, CZ, 5.0), cylx(TIP - 5, TIP + 1, CY, CZ, 1.7)), 'output shaft 10 mm (M4 in the end)', 'STEEL'))
    mkcomp(root, 'C6_Wiper_Motor_PM11G', wm)
    mb = []
    for a in BOSS_ANG:
        y, z = CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a))
        mb.append((uni(cyl((0.0, y, z), (-3.2, y, z), 6.0, 3.0), cylx(-20, -3.1, y, z, 3.0)), 'M6x20 countersunk', 'STEEL'))
    mkcomp(root, 'C6_Motor_Bolts_M6', mb)

    # --- printed crank (modelled at the knife-open position) ---
    cg = group('C6_Crank_Assy'); cgc = cg.component
    web_c = (0.5 * (ARM0 + ARM1), CY + 0.5 * R_CR * ur[0], CZ + 0.5 * R_CR * ur[1])
    ck = uni(cylx(ARM0, ARM1, CY, CZ, 13.0), cylx(ARM0, ARM1, *PO, 11.0),
             obox(web_c, (0, ur[0], ur[1]), (0, -ur[1], ur[0]), R_CR, 20.0, ARM1 - ARM0),
             cylx(ARM1, TIP - 0.3, CY, CZ, 10.5), cylx(ARM1, XB1, *PO, 8.0))
    us = (-ur[0], -ur[1]); ts = (-us[1], us[0])                 # set screw opposite the pin
    xs0, xs1 = max(ARM0, X_SS - 5.0), X_SS + 5.0
    blk_c = ((xs0 + xs1) / 2, CY + 9.0 * us[0], CZ + 9.0 * us[1])
    uni(ck, obox(blk_c, (0, us[0], us[1]), (0, ts[0], ts[1]), 10.0, 13.0, xs1 - xs0))
    sub(ck, cylx(ARM0 - 1, TIP + 1, CY, CZ, 5.125))                          # 10.25 bore
    sub(ck, cylx(TIP - 0.3, XB1 + 1, CY, CZ, 6.8))                           # room for the end washer + screw
    sub(ck, cylx(ARM0 - 1, XB1 + 1, *PO, 4.15), hexp('x', ARM0 - 0.1, ARM0 + 5.5, *PO, 13.3))
    sub(ck, cyl((X_SS, CY + 3.5 * us[0], CZ + 3.5 * us[1]), (X_SS, CY + 16 * us[0], CZ + 16 * us[1]), 2.15))
    nut_c = (X_SS, CY + 8.8 * us[0] + 5.5 * ts[0], CZ + 8.8 * us[1] + 5.5 * ts[1])
    sub(ck, obox(nut_c, (0, us[0], us[1]), (0, ts[0], ts[1]), 3.6, 18.0, 7.3))   # side-loaded M4 nut slot
    mkcomp(cgc, 'C6_Crank_PRINT', [(ck, 'crank (r 13.3)', 'BLUE')])
    ch = [(uni(hexp('x', ARM0, ARM0 + 5.3, *PO, 13), cylx(ARM0 + 5.29, ARM0 + 5.3 + 45, *PO, 4)), 'M8x45 hex bolt (crank pin, head trapped)', 'STEEL'),
          (ring_x(XB1, XK0, *PO, 8, 4.2), 'M8 washer', 'STEEL'), (ring_x(XK1, XK1 + 1.6, *PO, 8, 4.2), 'M8 washer', 'STEEL'),
          (sub(hexp('x', XK1 + 1.6, XK1 + 9.6, *PO, 13), cylx(XK1, XK1 + 11, *PO, 4)), 'M8 nylock', 'STEEL'),
          (uni(ring_x(TIP, TIP + 1.0, CY, CZ, 6.0, 2.2), cylx(TIP + 1.0, TIP + 3.2, CY, CZ, 3.8), cylx(TIP - 5, TIP + 1.01, CY, CZ, 2.0)), 'M4x8 button head + 12 mm washer', 'STEEL'),
          (cyl((X_SS, CY + 4.2 * us[0], CZ + 4.2 * us[1]), (X_SS, CY + 14.2 * us[0], CZ + 14.2 * us[1]), 2.0), 'M4x10 grub screw (+ M4 nut in slot)', 'DARK')]
    mkcomp(cgc, 'C6_Crank_Hardware', ch)

    # --- plywood link (x XK0..XK1), modelled at the open position ---
    ld_ = (DO[0] - PO[0], DO[1] - PO[1]); ln = math.hypot(*ld_); ul = (ld_[0] / ln, ld_[1] / ln)
    lk = uni(cylx(XK0, XK1, *PO, 11.0), cylx(XK0, XK1, *DO, 11.0),
             obox((0.5 * (XK0 + XK1), 0.5 * (PO[0] + DO[0]), 0.5 * (PO[1] + DO[1])), (0, ul[0], ul[1]), (0, -ul[1], ul[0]), ln, 22.0, XK1 - XK0))
    sub(lk, cylx(XK0 - 1, XK1 + 1, *PO, 4.1), cylx(XK0 - 1, XK1 + 1, *DO, 4.1))
    mkcomp(root, 'C6_Link_PLY', [(lk, 'link (8 mm plywood, %.1f c/c)' % ln, 'PLY')])
    LOG.append('link c/c %.2f (want %.2f)' % (ln, L_LK))

    # --- park microswitch (KW11 roller type) pressed by the crank tip at knife-open ---
    uo = (math.cos(PHI_O), math.sin(PHI_O)); to = (-uo[1], uo[0])
    def at(rad, tan): return (CY + rad * uo[0] + tan * to[0], CZ + rad * uo[1] + tan * to[1])
    swb = obox((3.2, *at(SW_R + 7.5, 12.0)), (0, to[0], to[1]), (0, uo[0], uo[1]), 20.0, 10.0, 6.4)
    for (y, z) in SW_HOLES: sub(swb, cylx(-1, 8, y, z, 1.1))
    swl = obox((3.2, *at(SW_R + 2.2, 9.0)), (0, to[0], to[1]), (0, uo[0], uo[1]), 18.0, 0.6, 4.0)
    swr = cylx(1.0, 5.4, *at(SW_R, 0.0), 2.5)
    mkcomp(root, 'C6_Park_Switch', [(uni(swb, swl, swr), 'KW11 roller microswitch', 'DARK')])

    # knife-height gauge (print only; sits in the exit channel, its underside = channel floor): hidden in the model
    gz = uni(box(-14, 10, -6.3, 6.3, 59.8, 65.4), box(0, 10, -12, 12, 65.4, 68.4))
    og = mkcomp(root, 'C6_Knife_Height_Gauge_PRINT', [(gz, 'knife height gauge', 'BLUE')])
    if og: og.isLightBulbOn = False

    # hide the parts this replaces in the demo
    for nm in ('Exit_Tie_Plate_DEMO_PRINT', 'Exit_Tie_Screws_M4'):
        o = root.occurrences.itemByName(nm + ':1')
        if o: o.isLightBulbOn = False
    LOG.append('PART C done')
