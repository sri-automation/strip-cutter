# Strip Cutter v3/v4/v5 (printed; feeder v5: two-sided yoke, open entry trough, exit guide with nip side cheeks, 628 top roller) - model builder for Autodesk Fusion
# Run with PART = 'A' (new document: plates, frame, static parts) then PART = 'B' (rollers, moving groups).
import adsk.core, adsk.fusion, math, traceback

S = 0.1  # mm -> cm
LOG = []
try:
    PART
except NameError:
    PART = 'ALL'
try:
    PATCH
except NameError:
    PATCH = False          # True: update the bodies of an existing model in place (keeps joints)

# ---------------- key geometry (mm) ----------------
XR, ZD, ZPN = -45.0, 45.0, 77.0           # roller axes (x, z); centre distance 32
PVX, PVZ = -77.0, 77.0                    # pinch-arm pivot
TNX, TNY = -20.0, -14.6                   # pressure screw (x, y)
STX = -58.0                               # gap-stop screw (x), y = TNY
ARM_R = 32.0                              # pivot -> roller axle
R_TIP, R_ROOT, NT = 15.0, 14.2, 56       # serrated tread
R_EFF = 14.6                              # effective feed radius
ZP_LO, ZP_HI = 75.0, 82.0                 # pinch axle z range (gap 0 .. 7 mm)
FL = 24.5                                 # stepper flange face (y)
Py = -48.0
th12 = math.radians(12.0); vEdge = -24.0
u7 = (7 - Py + vEdge * math.sin(th12)) / math.cos(th12)
Pz = 59 - u7 * math.sin(th12) - vEdge * math.cos(th12)
Cy, Cz = 4.0, 186.5
RCR, LK, EU, EV = 16.0, 68.0, 96.0, 20.0
LC = 75.0
T = 2.72; W2 = 6.0; ZT = 60 + T
Re = math.hypot(EU, EV); beta = math.atan2(EV, EU)
EARS = [30, 150, 250]
FEET = [(-102, -68), (27, -68), (-102, 76), (27, 76)]
LX0, LX1 = 23.0, 31.0                     # link plane (x)


def lever_state(phi):
    K = (Cy + RCR * math.cos(phi), Cz + RCR * math.sin(phi))
    dx, dy = K[0] - Py, K[1] - Pz
    d = math.hypot(dx, dy)
    a = (Re * Re - LK * LK + d * d) / (2 * d)
    h = math.sqrt(max(0.0, Re * Re - a * a))
    xm, ym = Py + a * dx / d, Pz + a * dy / d
    s1 = (xm + h * dy / d, ym - h * dx / d); s2 = (xm - h * dy / d, ym + h * dx / d)
    E = max([s1, s2], key=lambda p: p[0])
    return math.atan2(E[1] - Pz, E[0] - Py) - beta, E, K


_best = None
for _k in range(7200):
    _th, _E, _K = lever_state(math.radians(_k * 0.05))
    if _best is None or _th > _best[0]:
        _best = (_th, _k * 0.05, _E, _K)
TH_O, PH_O, E_O, K_O = _best


def run(_context: str):
    try:
        _run()
    except Exception:
        LOG.append('ERROR\n' + traceback.format_exc())
    print('\n'.join(LOG[-80:]))


def _run():
    app = adsk.core.Application.get()
    if PART in ('A', 'ALL') and not PATCH:
        d0 = app.activeDocument
        if d0 is not None and not d0.isSaved and d0.name.startswith('Untitled'):
            try:
                if adsk.fusion.Design.cast(d0.products.itemByProductType('DesignProductType')).rootComponent.occurrences.itemByName('Feed_Frame_PRINT:1'):
                    d0.close(False)
            except Exception:
                pass
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    if PART in ('A', 'ALL') and not PATCH:
        try:
            design.designIntent = adsk.fusion.DesignIntentTypes.HybridDesignIntentType
        except Exception as e:
            LOG.append('intent: %s' % e)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        try:
            design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        except Exception:
            pass
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
    def cyly(y0, y1, x, z, r): return cyl((x, y0, z), (x, y1, z), r)
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
    def ring_y(y0, y1, x, z, ro, ri): return sub(cyly(y0, y1, x, z, ro), cyly(y0 - 1, y1 + 1, x, z, ri))
    def ring_z(z0, z1, x, y, ro, ri): return sub(cylz(z0, z1, x, y, ro), cylz(z0 - 1, z1 + 1, x, y, ri))
    def hexp(axis, a0, a1, c1, c2, af):
        r = af / 2.0 / math.cos(math.pi / 6)
        b = None
        for k in range(3):
            a = math.pi / 3 * k
            ca, sa = math.cos(a), math.sin(a)
            if axis == 'x':
                bb = obox(((a0 + a1) / 2, c1, c2), (1, 0, 0), (0, ca, sa), abs(a1 - a0), 2 * r, af)
            elif axis == 'y':
                bb = obox((c1, (a0 + a1) / 2, c2), (ca, 0, sa), (0, 1, 0), 2 * r, abs(a1 - a0), af)
            else:
                bb = obox((c1, c2, (a0 + a1) / 2), (ca, sa, 0), (-sa, ca, 0), 2 * r, af, abs(a1 - a0))
            b = bb if b is None else inter(b, bb)
        return b
    def csk_x(y, z, rh=2.25):   # countersink from front face x=0 into -x
        return uni(cylx(-9, 1, y, z, rh), cyl((0.02, y, z), (-2.0, y, z), 4.25, 2.25))
    def hspace(p, n):           # half space {q: (q - p).n <= 0}; n lies in the xz or the xy plane
        L = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]); n = (n[0] / L, n[1] / L, n[2] / L)
        wd = (0, 1, 0) if abs(n[1]) < 1e-9 else (0, 0, 1)
        B = 400.0
        return obox((p[0] - n[0] * B / 2, p[1] - n[1] * B / 2, p[2] - n[2] * B / 2), n, wd, B, B, B)
    def funnel(xa, wa, fa, ra, xb, wb, fb, rb):   # channel solid tapering from section a to section b (xa < xb)
        s = box(xa, xb, -60, 60, 0, 160)
        for h in (hspace((xa, 0, fa), (fb - fa, 0, -(xb - xa))), hspace((xa, 0, ra), (-(rb - ra), 0, xb - xa)),
                  hspace((xa, wa, 0), (-(wb - wa), xb - xa, 0)), hspace((xa, -wa, 0), (-(wb - wa), -(xb - xa), 0))):
            inter(s, h)
        return s
    R2 = 1 / math.sqrt(2)

    # ---------------- appearances ----------------
    def get_apps():
        need = {'AL': 'Aluminium plate', 'STEEL': 'Steel', 'BLADE': 'HSS blade', 'DARK': 'Black oxide',
                'CF': 'PETG-CF black', 'BLUE': 'PETG blue', 'RUBBER': 'Rubber washer', 'MOTOR': 'Motor black',
                'WIPER': 'Wiper grey', 'NET': 'Red net (PE)', 'BIN': 'Bin grey'}
        out = {k: design.appearances.itemByName(v) for k, v in need.items()}
        if all(out.values()):
            return out
        applib = None
        for i in range(app.materialLibraries.count):
            lib = app.materialLibraries.item(i)
            if 'Appearance' in lib.name:
                applib = lib; break
        libnames = {}
        if applib:
            for i in range(applib.appearances.count):
                a = applib.appearances.item(i); libnames[a.name] = a
        def find_app(cands):
            for c in cands:
                if c in libnames: return libnames[c]
            for c in cands:
                for n, a in libnames.items():
                    if c.lower() in n.lower(): return a
            return None
        spec = {
            'AL': (['Aluminum - Satin', 'Aluminum'], None),
            'STEEL': (['Steel - Satin', 'Steel'], None),
            'BLADE': (['Steel - Polished', 'Chrome', 'Steel'], None),
            'DARK': (['Paint - Enamel Glossy (Black)', 'Plastic - Matte (Black)'], (30, 30, 32)),
            'CF': (['Plastic - Matte (Black)', 'Plastic - Glossy (Red)', 'Plastic'], (46, 47, 50)),
            'BLUE': (['Plastic - Glossy (Red)', 'Plastic - Glossy', 'Plastic'], (28, 96, 205)),
            'RUBBER': (['Rubber - Black', 'Plastic - Matte (Black)', 'Plastic'], (18, 18, 18)),
            'MOTOR': (['Paint - Enamel Glossy (Black)', 'Plastic - Matte (Black)'], (28, 28, 30)),
            'WIPER': (['Paint - Enamel Glossy (Black)', 'Plastic - Matte (Black)'], (70, 74, 80)),
            'NET': (['Plastic - Glossy (Red)', 'Plastic - Glossy', 'Plastic'], (214, 28, 36)),
            'BIN': (['Plastic - Matte (Black)', 'Plastic'], (150, 160, 175)),
        }
        for k, v in need.items():
            if out[k]:
                continue
            base = find_app(spec[k][0])
            if base is None:
                LOG.append('no appearance ' + k); continue
            a = design.appearances.addByCopy(base, v)
            rgb = spec[k][1]
            if rgb:
                for j in range(a.appearanceProperties.count):
                    p = a.appearanceProperties.item(j)
                    if p.objectType == adsk.core.ColorProperty.classType() and p.name == 'Color':
                        try: p.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                        except Exception: pass
                        break
            out[k] = a
        return out
    APP = get_apps()

    def mkcomp(parent, name, bodies, xform=None):
        if PATCH:
            comp = design.allComponents.itemByName(name)
            if comp is None and name == 'Bearing_628ZZ_x2':
                for old in ('Bearing_688ZZ_x2', 'Bearing_608ZZ_x2'):
                    comp = design.allComponents.itemByName(old)
                    if comp is not None:
                        comp.name = name; break
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
        if PATCH and parent != root:
            try: occ.isGroundToParent = True
            except Exception: pass
        if PATCH and parent == root:
            try: occ.isGrounded = True
            except Exception: pass
            LOG.append('new ' + name)
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
        return occ
    def group(name, xform=None):
        if PATCH:
            return root.occurrences.itemByName(name + ':1')
        occ = root.occurrences.addNewComponent(xform if xform else adsk.core.Matrix3D.create())
        occ.component.name = name
        return occ
    def mat(tx=0, ty=0, tz=0):
        m = adsk.core.Matrix3D.create(); m.translation = V3(tx * S, ty * S, tz * S); return m
    def frame_mat(origin, xax, yax, zax):
        m = adsk.core.Matrix3D.create(); m.setWithCoordinateSystem(P3(*origin), V3(*xax), V3(*yax), V3(*zax)); return m

    # =====================================================================
    if PART in ('A', 'ALL'):
        # ---------- aluminium plates ----------
        bp = box(-110, 35, -76, 84, -8, 0)
        for (x, y) in FEET:
            sub(bp, cylz(-9, 1, x, y, 3.3))
        for (x, y) in [(-80, 13.5), (-40, -12), (-40, 12), (-20, 3), (-60, 62), (-30, 62), (-36, -64), (26, 56)]:
            sub(bp, cylz(-9, 1, x, y, 2.75))          # M5 clearance, nut underneath
        for (x, y) in [(23, -32), (23, 32)]:
            sub(bp, cylz(-9, 1, x, y, 2.25))          # M4 clearance, nut underneath
        mkcomp(root, 'Base_Plate_Al8', [(bp, 'Base plate', 'AL')])

        mp = box(-8, 0, -76, 66, 0, 232)
        sub(mp, box(-9, 1, -9, 9, 54, 68), cylx(-9, 1, Py, Pz, 5.25), cylx(-9, 1, Cy, Cz, 16))
        for a in EARS:
            sub(mp, cylx(-9, 1, Cy + 38 * math.cos(math.radians(a)), Cz + 38 * math.sin(math.radians(a)), 3.25))
        for y in (-20, 8.5, 37):
            sub(mp, cylx(-9, 1, y, 23.5, 2.1))        # M5 tapped (knife stack)
        for (y, z) in [(-4, 73), (5, 73), (-23, 70), (21, 44)]:
            sub(mp, csk_x(y, z))                      # M4 countersunk into printed parts
        for (y, z) in [(-64, 26), (56, 26)]:
            sub(mp, cylx(-9, 1, y, z, 2.75))          # M5 to printed L-brackets
        mkcomp(root, 'Main_Plate_Al8', [(mp, 'Main plate', 'AL')])

        # ---------- printed L-brackets ----------
        def gusset(x_heel, dirx, y0, y1):
            L = math.hypot(32, 32)
            g = obox((x_heel + dirx * 16, (y0 + y1) / 2, 24), (dirx / math.sqrt(2), 0, -1 / math.sqrt(2)), (0, 1, 0), L, abs(y1 - y0), L)
            lim = box(min(x_heel, x_heel + dirx * 32), max(x_heel, x_heel + dirx * 32), y0, y1, 8, 40)
            return inter(lim, g)
        a1 = uni(box(-16, -8, -70, -50, 0, 40), box(-48, -8, -70, -50, 0, 8), gusset(-16, -1, -56, -52))
        sub(a1, cylx(-17, -7, -64, 26, 2.75), cylz(-1, 9, -36, -64, 2.75), cylz(4, 9, -36, -64, 5))
        mkcomp(root, 'Bracket_A1_PRINT', [(a1, 'L bracket', 'CF')])
        a2 = uni(box(0, 8, 50.5, 65.5, 0, 40), box(0, 40, 50.5, 65.5, 0, 8), gusset(8, 1, 62, 65.5))
        sub(a2, cylx(-1, 9, 56, 26, 2.75), cylz(-1, 9, 26, 56, 2.75), cylz(4, 9, 26, 56, 5))
        mkcomp(root, 'Bracket_A2_PRINT', [(a2, 'L bracket', 'CF')])

        # ---------- printed feed frame (v3) ----------
        def teardrop_y(y0, y1, x, z, r):
            d = uni(cyly(y0, y1, x, z, r),
                    obox((x, (y0 + y1) / 2, z + r / math.sqrt(2)), (1 / math.sqrt(2), 0, 1 / math.sqrt(2)), (0, 1, 0), r, abs(y1 - y0), r))
            return d
        ff = uni(box(-86, -8, -27, 24.5, 0, 8),                  # slab
                 box(-86, -8, -27, -19.5, 0, 88),                # wall A (arm pivot side)
                 box(-27, -12, -19.5, -9.0, 0, 64),              # pressure-screw column
                 box(-61, -55, -19.5, -10.5, 0, 66),             # gap-stop column (stop screw lands here)
                 box(-76, -8, 17.5, 24.5, 0, 76),                # stepper wall
                 box(-14.5, -9, -19.5, 17.5, 8, 48),             # tie wall (die block sits on it)
                 box(-70, -20, 24.5, 76, 0, 16.6))               # stepper cradle
        sub(ff, box(-35, -7, -28, -18, 84, 90))                  # clearance for rubber washers
        sub(ff, box(XR - 7.2, XR + 7.2, -28, -18, 66.5, 95))   # slot for the axle nylock: 14.4 wide, stops the nut spinning (hold-free tightening)
        sub(ff, cyly(-28, -18, PVX, PVZ, 2.75))                  # M5 arm pivot
        sub(ff, teardrop_y(17, 25, XR, ZD, 19.3))                # stepper pilot (teardrop: prints without support)
        for dx in (-23.3, 23.3):
            for dz in (-23.3, 23.3):
                sub(ff, cyly(17, 25, XR + dx, ZD + dz, 3.1))
        sub(ff, cylz(40, 64.1, TNX, TNY, 2.25), box(TNX - 3.65, TNX + 3.65, TNY - 4.3, -8.9, 56, 59.6))   # M4 + nut slot open to +y
        for (x, y) in [(-80, 13.5), (-40, -12), (-40, 12), (-20, 3)]:
            sub(ff, cylz(-1, 9, x, y, 2.75), cylz(3.5, 9, x, y, 4.8))
        for (x, y) in [(-60, 62), (-30, 62)]:
            sub(ff, cylz(-1, 17, x, y, 2.75), cylz(7, 17, x, y, 4.8))
        sub(ff, cylx(-18.1, -7.9, -23, 70, 1.7), cylx(-18.1, -7.9, 21, 44, 1.7))   # M4 self-tap from main plate (full machine)
        for z in (53, 67):
            sub(ff, cyly(16, 25, -12.5, z, 2.25))                # M4 clearance: exit guide screws (clear of the main-plate screw at z 70)
        for (x, y) in [(-78, -14), (-66, -14)]:
            sub(ff, cylz(1, 8.1, x, y, 1.7))                     # M4 self-tap for entry guide
        mkcomp(root, 'Feed_Frame_PRINT', [(ff, 'Feed frame', 'BLUE')])

        def pinch_sweep(y0, y1, r):
            return uni(cyly(y0, y1, XR, ZP_LO, r), cyly(y0, y1, XR, ZP_HI, r), box(XR - r, XR + r, y0, y1, ZP_LO, ZP_HI))

        # ---------- exit guide v5 = v4 die block + nip side cheeks: the net is held at +-6.6 up to ~4 mm before and after the
        #            nip, and at the nip itself it can move at most to +-8.5 while lying flat on ledges beside the drive tread
        #            (it can no longer drop into the pocket beside the drive roller and wrap round the hub) ----------
        EXF, EXR, EXW = 59.8, 66.0, 6.6
        # v5.1: the top roller must be able to come fully down onto the drive roller (axle z 75.0) and 0.3-0.8 mm past it
        #       (print tolerance, runout, preload), and the M8 washers may be up to 20 mm OD (shop washers vary)
        ZLR, ZLH = 74.7, 74.5                                                    # lowest axle used for roller / yoke+washer clearances
        def sweep_lo(y0, y1, r, zl=ZLH):                                         # space swept by a circle on the top-roller axle
            return uni(cyly(y0, y1, XR, zl, r), cyly(y0, y1, XR, ZP_HI, r), box(XR - r, XR + r, y0, y1, zl, ZP_HI))
        db = uni(box(-26, -8, -8.5, 13, 48, 78), box(-16, -8, 13, 17.5, 48, 78), box(-8, 0, -8.5, 8.9, 54.1, 67.9),
                 box(-37, -26, -8.5, 9.0, 48, 72),
                 box(-37, -26, 9.0, 13, 48, 66), box(-37, -27.5, -10, -8.5, 48, 66), box(-11.5, -8, -10, -8.5, 48, 78),
                 box(-59.5, -37, -10, -EXW, 48, 66),                             # -y cheek (wall A side), down to z 48 = print bed
                 box(-59.5, -37, EXW, 13, 48, 66))                               # +y cheek (motor side), arches over the hub
        sub(db, cyly(-7.5, 7.5, XR, ZD, R_TIP + 0.45))                          # drive tread (tread ends at +-7, ledges from +-7.5)
        sub(db, cyly(5.0, 17.4, XR, ZD, 10.0), cyly(8.6, 15.5, XR, ZD, 13.2))  # drive hub, M3 screw head sweep
        sub(db, sweep_lo(-8.5, 8.5, R_TIP + 0.5, ZLR))                          # top roller: touching the drive roller and 0.8 past
        sub(db, sweep_lo(-9.9, -7.9, 10.6), sweep_lo(7.9, 9.9, 10.6))           # M8 washers up to 20 OD
        sub(db, sweep_lo(-20, -9.1, 11.8), sweep_lo(9.1, 18, 11.3))             # yoke boss (-y) and yoke plate (+y), 0.8 clear
        sub(db, box(-61, -53.5, -7.6, 7.6, 40, 59.85))                          # entry-guide tongue
        sub(db, box(-24.5, -1.5, -EXW, EXW, EXF, EXR))                          # straight channel
        sub(db, funnel(-40, EXW, 57.8, 73.0, -29, EXW, 59.1, 67.2))             # steep entry (floor / roof) from the nip
        sub(db, funnel(-29.01, EXW, 59.1, 67.2, -24, EXW, EXF, EXR))            # gentle taper into the channel
        sub(db, funnel(-1.51, EXW, EXF, EXR, 0.6, EXW + 0.9, EXF - 0.3, EXR + 0.9))   # small exit flare
        sub(db, box(-61, -40, -EXW, EXW, 40, 90))                               # net path between the cheeks (open top)
        sub(db, funnel(-59.51, 7.3, 40, 90, -57.5, EXW, 40, 90))                # side lead-in where the cheeks start
        sub(db, funnel(-41.0, 7.8, 40, 90, -37.5, EXW, 40, 90))                 # side lead-in where the lips restart after the nip
        for y in (-4, 5):
            sub(db, cylx(-20.1, -7.9, y, 73, 1.7))               # main plate screws (full machine)
        sub(db, cyly(4, 17.6, -12.5, 53, 1.7))                   # M4 x 20 from the stepper wall (self-tap)
        sub(db, cyly(8.3, 17.6, -12.5, 67, 1.7))                 # M4 x 16 (a 20 would reach the channel roof)
        mkcomp(root, 'Exit_Guide_PRINT', [(db, 'Exit guide / die block', 'BLUE')])

        # ---------- entry guide v4: open-top trough (twists pass freely), flared + chamfered mouth ----------
        EF, EW, XM = 59.7, 6.6, -118.0
        eg = uni(box(-84, -62, -19, 8, 8, 14),                  # base plate: 2 x M4x12 into the slab
                 box(-84, -60, -9.5, 9.0, 14, EF),               # body under the floor
                 box(-86.5, -84, -9.5, 9.0, 54, EF),             # filler between the outer floor and the body
                 box(-86.5, -60, -9.5, 9.0, EF - 1, 68),         # low walls inside the frame (pivot tube above at z 69)
                 box(XM, -86.5, -16.5, 16.5, 54, 74),            # outer trough, tall walls
                 box(-60, -54, -7.3, 7.3, 56, EF))               # tongue into the nip
        gus = inter(box(XM, -84, -15, 15, 20, 54), hspace((-84, 0, 20), (-1, 0, -1)))   # 45 deg gusset (no supports)
        uni(eg, gus)
        sub(eg, cyly(-10, 10, XR, ZD, R_TIP + 0.8), pinch_sweep(-10, 10, R_TIP + 0.8))
        sub(eg, box(-100, -50, -EW, EW, EF, 90))                 # straight channel, open top
        flare = inter(box(XM - 1, -99.99, -60, 60, EF, 90),
                      hspace((XM - 1, 12.3, 0), (-(EW - 12.3), -99.99 - XM + 1, 0)))
        inter(flare, hspace((XM - 1, -12.3, 0), (-(EW - 12.3), -(-99.99 - XM + 1), 0)))
        sub(eg, flare)                                            # mouth 24 wide -> 13.2
        c = 3.0 * math.sqrt(2); c2 = 2.0 * math.sqrt(2)
        sub(eg, obox((XM, 0, EF), (R2, 0, R2), (0, 1, 0), c, 24.4, c))                  # 3 mm chamfer on the floor lip
        for s_ in (-1, 1):
            sub(eg, obox((XM, s_ * 12.0, 67), (R2, R2, 0), (-R2, R2, 0), c2, c2, 20))    # 2 mm chamfer on the wall lips
            sub(eg, obox((-73.25, s_ * EW, 68), (1, 0, 0), (0, R2, R2), 26.5, 1.2 * math.sqrt(2), 1.2 * math.sqrt(2)))   # wall tops inside
            sub(eg, obox((-93.25, s_ * EW, 74), (1, 0, 0), (0, R2, R2), 13.5, 1.2 * math.sqrt(2), 1.2 * math.sqrt(2)))   # wall tops outside
        sub(eg, cylz(7, 15, -78, -14, 2.25), cylz(7, 15, -66, -14, 2.25))
        mkcomp(root, 'Entry_Guide_PRINT', [(eg, 'Entry guide', 'BLUE')])

        # ---------- +y pivot bracket: second support for the arm pivot, clamped by the stepper's top-left M5 ----------
        BY0, BY1 = 9.5, 17.5
        SBX, SBZ = XR - 23.3, ZD + 23.3
        dl = math.hypot(SBX - PVX, SBZ - PVZ); du = ((SBX - PVX) / dl, 0, (SBZ - PVZ) / dl)
        br = uni(cyly(BY0, BY1, PVX, PVZ, 8.5), cyly(BY0, BY1, SBX, SBZ, 7.5),
                 obox(((PVX + SBX) / 2, (BY0 + BY1) / 2, (PVZ + SBZ) / 2), du, (0, 1, 0), dl, BY1 - BY0, 15))
        sub(br, cyly(BY0 - 1, BY1 + 1, PVX, PVZ, 2.75), hexp('y', 13.2, BY1 + 1, PVX, PVZ, 8.3),     # rod + M5 nut pocket (opens to the wall)
            cyly(BY0 - 1, BY1 + 1, SBX, SBZ, 2.75), cyly(BY0 - 1, 13.5, SBX, SBZ, 5.2))            # stepper bolt, head counterbore
        mkcomp(root, 'Pivot_Bracket_R_PRINT', [(br, 'pivot bracket (motor side)', 'BLUE')])
        mkcomp(root, 'Pivot_Sleeve_PRINT', [(ring_y(-19.5, BY0, PVX, PVZ, 4.5, 2.7), 'pivot sleeve 9/5.4 x 29', 'BLUE')])

        # ---------- exit tie plate (demo only: ties wall tops at the exit end; the Al main plate does this in the full machine) ----------
        tp = box(-8, -3, -27, 24.5, 38, 76)
        sub(tp, box(-9, -2, -9.1, 9.5, 53.5, 68.5), cylx(-9, -2, -23, 70, 2.25), cylx(-9, -2, 21, 44, 2.25))
        mkcomp(root, 'Exit_Tie_Plate_DEMO_PRINT', [(tp, 'exit tie plate (demo)', 'BLUE')])
        mkcomp(root, 'Exit_Tie_Screws_M4', [(uni(hexp('x', -3, -0.2, y, z, 7), cylx(-15, -2.99, y, z, 2)), 'M4x12 (tie)', 'STEEL')
                                            for (y, z) in ((-23, 70), (21, 44))])

        # (optional KW11 strip sensor removed in v4: the entry guide is now an open trough; remount on the outer trough wall later)

        # ---------- stepper ----------
        st_body = inter(box(-73.2, -16.8, FL + 6.5, FL + 50, 16.8, 73.2), cyly(FL + 6, FL + 51, XR, ZD, 37.5))
        for dx in (-23.3, 23.3):
            for dz in (-23.3, 23.3):
                sub(st_body, cyly(FL + 6, FL + 16, XR + dx, ZD + dz, 6.5))      # corner relief behind the flange (as on real motors)
        st_cap1 = inter(box(-73.2, -16.8, FL, FL + 6.5, 16.8, 73.2), cyly(FL - 1, FL + 7, XR, ZD, 37.5))
        for dx in (-23.3, 23.3):
            for dz in (-23.3, 23.3):
                sub(st_cap1, cyly(FL - 1, FL + 7, XR + dx, ZD + dz, 2.6))
        st_cap2 = inter(box(-73.2, -16.8, FL + 50, FL + 56, 16.8, 73.2), cyly(FL + 49, FL + 57, XR, ZD, 37.5))
        mkcomp(root, 'Stepper_23HS5628_NEMA23', [(st_body, 'stator', 'MOTOR'), (st_cap1, 'front cap', 'AL'),
                                                 (st_cap2, 'rear cap', 'AL'), (cyly(FL - 1.6, FL, XR, ZD, 19.0), 'pilot', 'AL'),
                                                 (box(-16.8, -11, FL + 40, FL + 54, 36, 54), 'connector', 'DARK')])
        smh = []
        for dx in (-23.3, 23.3):
            for dz in (-23.3, 23.3):
                if dx < 0 and dz > 0:      # top-left bolt also clamps the pivot bracket: M5x25, head in the bracket counterbore
                    smh.append((uni(hexp('y', 10, 13.5, XR + dx, ZD + dz, 8), cyly(13.49, 38.5, XR + dx, ZD + dz, 2.5),
                                    ring_y(31, 32, XR + dx, ZD + dz, 5, 2.7), hexp('y', 32, 36, XR + dx, ZD + dz, 8)), 'M5x25 + washer + nut (bracket)', 'STEEL'))
                else:
                    smh.append((uni(hexp('y', 14, 17.5, XR + dx, ZD + dz, 8), cyly(17.49, 37.5, XR + dx, ZD + dz, 2.5),
                                    ring_y(31, 32, XR + dx, ZD + dz, 5, 2.7), hexp('y', 32, 36, XR + dx, ZD + dz, 8)), 'M5x20 + washer + nut', 'STEEL'))
        mkcomp(root, 'Stepper_Mount_Screws_M5', smh)
        mkcomp(root, 'Exit_Guide_Screws_M4', [(uni(hexp('y', 24.5, 27.3, -12.5, 53, 7), cyly(4.5, 24.51, -12.5, 53, 2)), 'M4x20', 'STEEL'),
                                              (uni(hexp('y', 24.5, 27.3, -12.5, 67, 7), cyly(8.5, 24.51, -12.5, 67, 2)), 'M4x16', 'STEEL')])
        mkcomp(root, 'Entry_Guide_Screws_M4', [(uni(hexp('z', 14, 16.8, x, -14, 7), cylz(2, 14.01, x, -14, 2)), 'M4x12', 'STEEL') for x in (-78, -66)])

        # ---------- knife stack ----------
        bsp = box(0, 3, -32.5, 49.5, 16, 60)
        bfl = box(3, 6, -32.5, 49.5, 16, 31)
        bcl = box(6, 11, -32.5, 49.5, 16, 51)
        bscr = []
        for y in (-20, 8.5, 37):
            sub(bsp, cylx(-1, 4, y, 23.5, 2.75)); sub(bfl, cylx(2, 7, y, 23.5, 2.75)); sub(bcl, cylx(5, 12, y, 23.5, 2.75))
            bscr.append((uni(ring_x(11, 12, y, 23.5, 5, 2.7), cylx(12, 17, y, 23.5, 4.25), cylx(-8, 12.01, y, 23.5, 2.5)), 'M5x20 SHCS + washer', 'DARK'))
        mkcomp(root, 'Bed_Spacer_PRINT', [(bsp, 'bed spacer 3mm', 'CF')])
        mkcomp(root, 'Bed_Knife_HSS_82x29x3', [(box(3, 6, -32.5, 49.5, 31, 60), 'fixed knife (planer blade)', 'BLADE')])
        mkcomp(root, 'Bed_Filler_PRINT', [(bfl, 'filler 3mm', 'CF')])
        mkcomp(root, 'Bed_Clamp_PRINT', [(bcl, 'clamp bar 5mm', 'CF')])
        mkcomp(root, 'Bed_Screws_M5', bscr)

        # ---------- lever pivot hardware ----------
        mkcomp(root, 'Lever_Pivot_M10_Bolt', [
            (uni(hexp('x', 23.2, 29.6, Py, Pz, 16), cylx(-26.8, 23.21, Py, Pz, 5)), 'M10x50 hex bolt', 'STEEL'),
            (ring_x(19.0, 21.0, Py, Pz, 10, 5.3), 'M10 washer', 'STEEL'),
            (ring_x(21.0, 23.2, Py, Pz, 9, 5.2), 'M10 spring washer (knife preload)', 'DARK'),
            (ring_x(-10, -8, Py, Pz, 10, 5.3), 'M10 washer', 'STEEL'),
            (sub(hexp('x', -20, -10, Py, Pz, 17), cylx(-21, -9, Py, Pz, 5)), 'M10 nylock', 'STEEL')])
        mkcomp(root, 'Pivot_Spacer_PRINT', [(ring_x(0, 9, Py, Pz, 10, 5.25), 'pivot spacer 9mm', 'CF')])

        # ---------- wiper motor placeholder ----------
        dy_, dz_ = math.cos(math.radians(210)), math.sin(math.radians(210))
        wm = uni(cylx(-60, -10, Cy, Cz, 40), obox((-35, Cy + 47.5 * dy_, Cz + 47.5 * dz_), (0, dy_, dz_), (0, -dz_, dy_), 95, 70, 50))
        wb = None
        for a in EARS:
            ya, za = Cy + 38 * math.cos(math.radians(a)), Cz + 38 * math.sin(math.radians(a))
            uni(wm, cylx(-18, -8, ya, za, 7))
            b_ = uni(cylx(-12, 0, ya, za, 3), cylx(0, 5, ya, za, 5))
            wb = b_ if wb is None else uni(wb, b_)
        mkcomp(root, 'Wiper_Motor_12V_(yours)', [
            (wm, 'gearbox (placeholder - verify)', 'WIPER'), (cylx(-10, -1, Cy, Cz, 14), 'output boss', 'WIPER'),
            (cyl((-37, Cy + 95 * dy_, Cz + 95 * dz_), (-37, Cy + 185 * dy_, Cz + 185 * dz_), 28), 'motor can (park switch inside)', 'MOTOR'),
            (cyl((-37, Cy + 185 * dy_, Cz + 185 * dz_), (-37, Cy + 193 * dy_, Cz + 193 * dz_), 22), 'end cap', 'WIPER'),
            (wb, 'M6 mount bolts', 'DARK')])

        # ---------- pinch pivot + pressure hardware (static) ----------
        nut4 = hexp('z', 56, 59.2, TNX, TNY, 7)
        r30 = adsk.core.Matrix3D.create(); r30.setToRotation(math.pi / 6, V3(0, 0, 1), P3(TNX, TNY, 0)); tb.transform(nut4, r30)
        mkcomp(root, 'Pinch_Pivot_and_Pressure_Hardware', [
            (uni(hexp('y', -31.5, -28, PVX, PVZ, 8), cyly(-28.01, 17.0, PVX, PVZ, 2.5)), 'M5x45 bolt (pivot rod)', 'STEEL'),
            (ring_y(-28, -27, PVX, PVZ, 5, 2.7), 'M5 washer', 'STEEL'),
            (sub(hexp('y', 13.3, 17.3, PVX, PVZ, 8), cyly(12, 18, PVX, PVZ, 2.5)), 'M5 nut (in bracket pocket)', 'STEEL'),
            (uni(cylz(55, 95.01, TNX, TNY, 2), hexp('z', 95, 97.8, TNX, TNY, 7)), 'M4x40 hex bolt (pressure)', 'STEEL'),
            (nut4, 'M4 nut (in slot)', 'STEEL'),
            (ring_z(85, 94, TNX, TNY, 8, 2.7), 'rubber washers x3 (spring)', 'RUBBER'),
            (ring_z(94, 95, TNX, TNY, 6, 2.2), 'M4 washer', 'STEEL')])
        kn = sub(cylz(95.2, 104, TNX, TNY, 7.5), hexp('z', 95, 98.1, TNX, TNY, 7.3), cylz(94, 105, TNX, TNY, 2.2))
        for i in range(8):
            a = 2 * math.pi * i / 8
            sub(kn, cylz(94, 105, TNX + 8.1 * math.cos(a), TNY + 8.1 * math.sin(a), 1.4))
        mkcomp(root, 'Pressure_Knob_PRINT', [(kn, 'knob', 'BLUE')])

        # ---------- chute, bin, feet, supply ----------
        L_ch = math.hypot(52, 30); ds = (52 / L_ch, -30 / L_ch); nrm = (-ds[1], ds[0]); top_c = (38.0, 35.0)
        ch = obox((top_c[0] - 1.5 * nrm[0], 0, top_c[1] - 1.5 * nrm[1]), (ds[0], 0, ds[1]), (0, 1, 0), L_ch, 60, 3)
        for ysw in (-28.5, 28.5):
            uni(ch, obox((top_c[0] + 7.5 * nrm[0], ysw, top_c[1] + 7.5 * nrm[1]), (ds[0], 0, ds[1]), (0, 1, 0), L_ch, 3, 15))
        for (ya, yb) in ((-30, -27), (27, 30)):
            uni(ch, box(14, 32, ya, yb, 0, 46))
        for (ya, yb) in ((-38, -24), (24, 38)):
            uni(ch, box(14, 32, ya, yb, 0, 4))
        sub(ch, cylz(-1, 5, 23, -32, 2.25), cylz(-1, 5, 23, 32, 2.25), box(-10, 200, -50, 50, -40, 0), box(-10, 11.6, -50, 50, 0, 80))
        mkcomp(root, 'Outfeed_Chute_PRINT', [(ch, 'chute', 'BLUE')])
        mkcomp(root, 'Collection_Bin', [(sub(box(66, 186, -60, 60, -23, 5), box(68, 184, -58, 58, -21, 6)), 'bin (any tub)', 'BIN')])
        feet = []
        for (x, y) in FEET:
            f = sub(cylz(-23, -8, x, y, 10), cylz(-24, -7, x, y, 3.3), hexp('z', -24, -15, x, y, 10.2))   # M6x20: nut sits at the pocket top
            feet.append((f, 'foot', 'BLUE'))
        mkcomp(root, 'Feet_PRINT_x4', feet)
        mkcomp(root, 'Net_Strip_Supply_12x2.7', [(box(-160, 6, -W2, W2, 60, ZT), 'red packaging net 12 x 2.7', 'NET')])
        LOG.append('PART A done: %d components' % root.occurrences.count)

    # =====================================================================
    if PART in ('B', 'ALL'):
        scratch = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        scomp = scratch.component
        def polyprofile_body(pts, width):
            sk = scomp.sketches.add(scomp.xZConstructionPlane)
            sk.isComputeDeferred = True
            lines = sk.sketchCurves.sketchLines
            first = None; prevpt = None
            p0 = sk.modelToSketchSpace(P3(pts[0][0], 0, pts[0][1]))
            for (gx, gz) in pts[1:]:
                p = sk.modelToSketchSpace(P3(gx, 0, gz))
                ln = lines.addByTwoPoints(p0 if prevpt is None else prevpt, p)
                if first is None: first = ln
                prevpt = ln.endSketchPoint
            lines.addByTwoPoints(prevpt, first.startSketchPoint)
            sk.isComputeDeferred = False
            prof = max([sk.profiles.item(i) for i in range(sk.profiles.count)], key=lambda pr: pr.areaProperties().area)
            ei = scomp.features.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ei.setSymmetricExtent(adsk.core.ValueInput.createByReal(width * S), True)
            ext = scomp.features.extrudeFeatures.add(ei)
            return tb.copy(ext.bodies.item(0))
        star = []
        for i in range(2 * NT):
            r = R_TIP if i % 2 == 0 else R_ROOT
            a = math.pi * i / NT
            star.append((r * math.cos(a), r * math.sin(a)))
        tread = polyprofile_body(star, 14)                   # y -7..7 (drive roller)
        tread16 = polyprofile_body(star, 16)                 # y -8..8 (top roller, 628 version as assembled)
        scratch.deleteMe()

        # --- drive rotor: serrated roller + hub on the stepper shaft (M3 screw + nut) ---
        g_drive = group('Drive_Rotor'); dc = g_drive.component
        def drive_roller(bore_r):
            d = uni(tb.copy(tread), cyly(6.99, 16, 0, 0, 9.5))
            sub(d, cyly(-8, 17, 0, 0, bore_r))                   # shaft bore
            sub(d, cyl((0, 12, 2.0), (0, 12, 10), 1.7))          # M3 radial screw
            sub(d, box(-2.9, 2.9, 8.6, 16.1, 4.4, 7.0))          # M3 nut slot (open at the hub end), nut flats face +-x
            return d
        mkcomp(dc, 'Drive_Roller_PRINT', [(drive_roller(3.275), 'drive roller, serrated (6.35 shaft)', 'BLUE')], mat(XR, 0, ZD))
        nut3 = hexp('z', ZD + 4.5, ZD + 6.9, XR, 12, 5.5)
        r30b = adsk.core.Matrix3D.create(); r30b.setToRotation(math.pi / 6, V3(0, 0, 1), P3(XR, 12, 0)); tb.transform(nut3, r30b)
        mkcomp(dc, 'Stepper_Shaft_6.35', [(cyly(FL - 21, FL - 1.6, XR, ZD, 3.175), 'motor shaft', 'STEEL'),
                                         (uni(cylz(ZD + 3.4, ZD + 9.51, XR, 12, 1.5), cylz(ZD + 9.5, ZD + 12.5, XR, 12, 2.75)), 'M3x8 socket screw', 'DARK'),
                                         (nut3, 'M3 nut', 'STEEL')])

        # --- pinch yoke (v4): -y arm as v3 + full-width pivot tube (both walls) + crossbar over the roller + +y plate ---
        g_arm = group('Pinch_Arm_Assy'); ac = g_arm.component
        Y0, Y1 = -19.0, -10.2
        YP0, YP1 = 9.6, 17.1
        arm = uni(cyly(Y0, 9.0, PVX, PVZ, 8),                                   # pivot tube, rides on the sleeve
                  cyly(Y0, -9.6, XR, ZPN, 11),                                  # -y axle boss
                  box(-77, -27, Y0, Y1, 70, 84), box(-27, -12, Y0, Y1, 70, 85),
                  box(-51, -39, Y0, Y1, 80, 100),                               # riser
                  box(-51, -39, Y0, YP1, 94, 100),                              # crossbar (2 mm above the roller tips)
                  cyly(YP0, YP1, XR, ZPN, 10.5), box(XR - 10.5, XR + 10.5, YP0, YP1, ZPN, 100))   # +y plate
        sub(arm, cyly(Y0 - 1, 10, PVX, PVZ, 4.7),                               # 9.4 bore on the 9.0 sleeve
            cyly(Y0 - 1, YP1 + 1, XR, ZPN, 4.2),                                # M8 axle
            hexp('y', 11.7, YP1 + 1, XR, ZPN, 13.3),                            # M8 head pocket (head flush inside the plate)
            cylz(60, 95, TNX - 2.0, TNY, 2.75), cylz(60, 95, TNX + 2.0, TNY, 2.75), box(TNX - 2.0, TNX + 2.0, TNY - 2.75, TNY + 2.75, 60, 95),   # 9.5 x 5.5 slot
            cylz(60, 95, STX, TNY, 1.7))
        mkcomp(ac, 'Pinch_Arm_PRINT', [(arm, 'pinch arm (yoke)', 'BLUE')])
        nyl8 = sub(hexp('y', -27, -19, XR, ZPN, 13), cyly(-28, -18, XR, ZPN, 4))
        r30c = adsk.core.Matrix3D.create(); r30c.setToRotation(math.pi / 6, V3(0, 1, 0), P3(XR, 0, ZPN)); tb.transform(nyl8, r30c)
        mkcomp(ac, 'Pinch_Axle_M8', [
            (uni(hexp('y', 11.7, 17.0, XR, ZPN, 13), cyly(-28.3, 11.71, XR, ZPN, 4)), 'M8x40 bolt (axle, head in the yoke pocket)', 'STEEL'),
            (nyl8, 'M8 nylock (sits in the frame slot, cannot spin)', 'STEEL'),
            (ring_y(-9.6, -8, XR, ZPN, 8, 4.2), 'M8 washer', 'STEEL'),
            (ring_y(8, 9.6, XR, ZPN, 8, 4.2), 'M8 washer', 'STEEL')])
        if PATCH:
            o_sp = ac.occurrences.itemByName('Top_Roller_Spacer_PRINT:1')
            if o_sp: o_sp.deleteMe(); LOG.append('removed 688 spacers')
        mkcomp(ac, 'Gap_Stop_Screw_M4', [
            (uni(cylz(66, 91.01, STX, TNY, 2), hexp('z', 91, 93.8, STX, TNY, 7)), 'M4x25 hex bolt (gap stop)', 'STEEL'),
            (sub(hexp('z', 84, 87.2, STX, TNY, 7), cylz(83, 88, STX, TNY, 2)), 'M4 lock nut', 'STEEL')])

        # --- pinch rotor: free roller on 2 x 628ZZ (8 x 24 x 8), pressed in from each face (as assembled) ---
        g_pin = group('Pinch_Rotor'); pcmp = g_pin.component
        pr = sub(tb.copy(tread16), cyly(-9, 9, 0, 0, 12.075))
        mkcomp(pcmp, 'Pinch_Roller_PRINT', [(pr, 'pinch roller, serrated, 2x628ZZ pressed in', 'BLUE')], mat(XR, 0, ZPN))
        def brg_y(y0):
            b = ring_y(y0, y0 + 8, XR, ZPN, 12, 4)
            sub(b, ring_y(y0 + 7.6, y0 + 9, XR, ZPN, 10.5, 6.5), ring_y(y0 - 1, y0 + 0.4, XR, ZPN, 10.5, 6.5))
            return b
        mkcomp(pcmp, 'Bearing_628ZZ_x2', [(brg_y(-8), '628ZZ', 'STEEL'), (brg_y(0), '628ZZ', 'STEEL')])

        # --- crank rotor ---
        g_crank = group('Crank_Rotor'); cc = g_crank.component
        Ky, Kz = K_O
        disc = cylx(4, 14, Cy, Cz, 25)
        sub(disc, cylx(7, 15, Cy, Cz, 9), cylx(3, 15, Cy, Cz, 5), cylx(3, 15, Ky, Kz, 3.4))
        mkcomp(cc, 'Crank_Arm_r16_(orig_arm_or_Al_disc)', [(disc, 'crank r16', 'AL')])
        mkcomp(cc, 'Crank_Pin_Spacer_PRINT', [(ring_x(14, 23, Ky, Kz, 8, 4.25), 'crank pin spacer 9mm', 'CF')])
        mkcomp(cc, 'Crank_Hardware', [(cylx(-1, 7.01, Cy, Cz, 5), 'wiper output shaft (yours)', 'STEEL'),
                                      (sub(hexp('x', 7.5, 13.5, Cy, Cz, 14), cylx(7, 14, Cy, Cz, 4)), 'shaft nut', 'STEEL'),
                                      (ring_x(30, 31.6, Ky, Kz, 8, 4.2), 'M8 washer', 'STEEL'),
                                      (uni(hexp('x', 31.6, 36.9, Ky, Kz, 13), cylx(1.6, 31.61, Ky, Kz, 4)), 'M8x30 bolt (crank pin)', 'STEEL')])

        # --- link: printed, 2 x 608 ---
        ex, ez = E_O[0] - Ky, E_O[1] - Kz
        ll = math.hypot(ex, ez); ey = (ex / ll, ez / ll)
        g_link = group('Link_Assy', frame_mat((0, Ky, Kz), (1, 0, 0), (0, ey[0], ey[1]), (0, -ey[1], ey[0])))
        lc = g_link.component
        lk = uni(cylx(LX0, LX1, 0, 0, 16.5), cylx(LX0, LX1, LK, 0, 16.5), box(LX0, LX1, 0, LK, -10, 10))
        for s_ in (0, LK):
            sub(lk, cylx(LX0 - 0.1, LX0 + 7.05, s_, 0, 11.05), cylx(LX0 - 1, LX1 + 1, s_, 0, 9.5))
        mkcomp(lc, 'Link_PRINT_68cc', [(lk, 'link (2x608)', 'CF')])
        def brg_x(s_):
            b = ring_x(LX0, LX0 + 7, s_, 0, 11, 4)
            sub(b, ring_x(LX0 + 6.5, LX0 + 8, s_, 0, 9.3, 6.2), ring_x(LX0 - 1, LX0 + 0.5, s_, 0, 9.3, 6.2))
            return b
        mkcomp(lc, 'Link_Bearings_608ZZ_x2', [(brg_x(0), '608ZZ', 'STEEL'), (brg_x(LK), '608ZZ', 'STEEL')])

        # --- lever assembly (X=x, Y=u, Z=v) ---
        c_, s_ = math.cos(TH_O), math.sin(TH_O)
        g_lev = group('Lever_Assy', frame_mat((0, Py, Pz), (1, 0, 0), (0, c_, s_), (0, -s_, c_)))
        lvc = g_lev.component
        lev = box(9, 19, -12, 108, -12, 28)
        sub(lev, cylx(8, 20, 0, 0, 7), cylx(8, 20, EU, EV, 3.4))
        SCRU = (33.0, 60.5, 88.0)
        for u in SCRU:
            sub(lev, cylx(8, 20, u, 11, 1.65))
        mkcomp(lvc, 'Lever_Al_Flat40x10x120', [(lev, 'lever', 'AL')])
        mkcomp(lvc, 'Pivot_Bush_PRINT', [(ring_x(9, 18.9, 0, 0, 7, 5.15), 'printed bush 14/10.3 x 9.9', 'CF')])
        blade = box(6, 9, 23.5, 105.5, -24, 5)
        bd = (3.0, 4.28); bn = math.hypot(*bd); bdir = (bd[0] / bn, bd[1] / bn); hdir = (bdir[1], -bdir[0])
        sub(blade, obox((7.5 + 5 * hdir[0], 64.5, -21.86 + 5 * hdir[1]), (0, 1, 0), (bdir[0], 0, bdir[1]), 100, 20, 10))
        mkcomp(lvc, 'Moving_Blade_HSS_82x29x3', [(blade, 'moving knife (planer blade)', 'BLADE')])
        bsps = box(6, 9, 23.5, 105.5, 5, 17)
        bclp = box(1, 6, 23.5, 105.5, -5, 17)
        scr = None
        for u in SCRU:
            sub(bsps, cylx(5, 10, u, 11, 2.25))
            sub(bclp, cylx(0, 7, u, 11, 2.25), cyl((0.99, u, 11), (2.76, u, 11), 4.0, 2.25))
            s1 = uni(cyl((1.0, u, 11), (2.75, u, 11), 4.0, 2.25), cylx(2.74, 17, u, 11, 2.0))
            scr = s1 if scr is None else uni(scr, s1)
        mkcomp(lvc, 'Blade_Spacer_PRINT', [(bsps, 'blade spacer 3mm', 'CF')])
        mkcomp(lvc, 'Blade_Clamp_PRINT', [(bclp, 'blade clamp bar 5mm', 'CF')])
        mkcomp(lvc, 'Blade_Screws_M4_CSK', [(scr, 'M4x16 countersunk', 'DARK')])
        mkcomp(lvc, 'Lever_Pin_Spacer_PRINT', [(ring_x(19, 23, EU, EV, 8, 4.25), 'lever pin spacer 4mm', 'CF')])
        mkcomp(lvc, 'Lever_Pin_Hardware', [(ring_x(30, 31.6, EU, EV, 8, 4.2), 'M8 washer', 'STEEL'),
                                           (uni(hexp('x', 31.6, 36.9, EU, EV, 13), cylx(11.6, 31.61, EU, EV, 4)), 'M8x20 bolt (link pin)', 'STEEL')])

        # --- net pieces ---
        mkcomp(root, 'Strip_Feed_Piece', [(box(6 - LC, 6, -W2 - 0.03, W2 + 0.03, 59.97, ZT + 0.03), 'feeding net', 'NET')])
        for i in range(3):
            mkcomp(root, 'Cut_Piece_%d' % (i + 1), [(box(6, 6 + LC, -W2 - 0.02, W2 + 0.02, 59.98, ZT + 0.02), 'cut piece', 'NET')])

        if PATCH:
            LOG.append('PATCH B done'); return
        moving = ('Drive_Rotor', 'Pinch_Arm_Assy', 'Pinch_Rotor', 'Crank_Rotor', 'Link_Assy', 'Lever_Assy', 'Strip_Feed_Piece')
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            for c in o.childOccurrences:
                c.isGroundToParent = True
            nm = o.component.name
            if nm in moving or nm.startswith('Cut_Piece'):
                continue
            o.isGrounded = True
        def zmat(tx, ty, tz, rz):
            m = adsk.core.Matrix3D.create()
            m.setToRotation(math.radians(rz), V3(0, 0, 1), P3(6 + LC / 2, 0, 61))
            t = m.translation
            m.translation = V3(t.x + tx * S, t.y + ty * S, t.z + tz * S)
            return m
        root.occurrences.itemByName('Cut_Piece_2:1').transform2 = zmat(86, -22, -80, 8)
        root.occurrences.itemByName('Cut_Piece_3:1').transform2 = zmat(82, 20, -80, -6)
        try:
            design.snapshots.add()
        except Exception:
            pass
        LOG.append('PART B done: %d components, open theta %.3f at phi %.2f' % (root.occurrences.count, math.degrees(TH_O), PH_O))
        app.activeViewport.fit()
