# Strip Cutter - feeder exit guide v6: Exit_Guide_PRINT with a long nose that reaches the blades.
# Measured on the machine: the old nose ends 10 mm behind the FRONT face of the fixed blade (old nose end = x 0 here).
# The new nose runs on to x = NL, 0.6 mm short of that face, closed on all four sides; its underside follows the
# 38 deg bevel of the fixed blade; the floor rises to end 0.7 mm above the blade edge (blade pushed up against the tip).
# Coordinates as the feeder model (mm): x feed direction, y across, z up. The rest of the guide is unchanged (v5.1).
import adsk.core, adsk.fusion, math, traceback, os

S = 0.1
D_BLADE = 10.0                   # old nose end -> front face of the fixed blade (user's measurement)
NL = D_BLADE - 0.6               # new nose end
NOSE_Y, NOSE_Z = (-8.5, 8.9), (54.1, 67.9)       # unchanged nose envelope (main-plate window is y -10..10.4, z 53..69)
CH_W, CH_F, CH_R = 6.6, 59.8, 66.0               # channel half width, floor, roof (unchanged up to x = 0)
TIP_F, TIP_R = 60.5, 65.2                        # floor and roof at the tip
K = 3.686 / 2.88                 # fixed blade bevel, rise per mm
ZU0 = 59.8                       # the underside line passes through (D_BLADE, ZU0): the blade edge sits here when it touches the tip
X_STEP, Z_STEP = 5.5, 56.3       # from here on the nose bottom is raised to clear the back of the fixed blade
BASE = os.path.join(os.path.expanduser('~'), 'Documents', 'Strip_Cutter', 'v3')


def run(_context: str):
    out = []
    try:
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
        def hs(p, n):                # half space {q: (q - p).n <= 0}, n in the xz plane
            L = math.hypot(n[0], n[2]); n = (n[0] / L, 0.0, n[2] / L); B = 400.0
            return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P3(p[0] - n[0] * B / 2, p[1], p[2] - n[2] * B / 2),
                                V3(*n), V3(0, 1, 0), B * S, B * S, B * S))
        def uni(a, *bs):
            for b in bs: tb.booleanOperation(a, b, UN)
            return a
        def sub(a, *bs):
            for b in bs: tb.booleanOperation(a, b, DF)
            return a
        def inter(a, *bs):
            for b in bs: tb.booleanOperation(a, b, IN)
            return a

        comp = design.allComponents.itemByName('Exit_Guide_PRINT')
        cur = comp.bRepBodies.item(0)
        bk = design.allComponents.itemByName('Exit_Guide_v51_old_PRINT')
        if bk is None:                                   # keep the v5.1 body in a hidden component
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            bk = occ.component; bk.name = 'Exit_Guide_v51_old_PRINT'
            bf = bk.features.baseFeatures.add(); bf.startEdit()
            bk.bRepBodies.add(tb.copy(cur), bf); bf.finishEdit()
            bk.bRepBodies.item(0).name = 'Exit guide v5.1 (short nose, as printed)'
            occ.isLightBulbOn = False
            out.append('saved the old body in Exit_Guide_v51_old_PRINT (hidden)')
        src = bk.bRepBodies.item(0)
        sb = src.boundingBox
        out.append('old guide x %.1f..%.1f' % (sb.minPoint.x * 10, sb.maxPoint.x * 10))

        b = tb.copy(src)
        uni(b, box(-1.6, NL, NOSE_Y[0], NOSE_Y[1], NOSE_Z[0], NOSE_Z[1]))              # fills the old exit flare and adds the long nose
        sub(b, box(-2.0, 0.01, -CH_W, CH_W, CH_F, CH_R))                               # straight channel through the old nose end
        kf, kr = (TIP_F - CH_F) / NL, (CH_R - TIP_R) / NL
        taper = box(0, NL + 0.3, -CH_W, CH_W, CH_F - 1, CH_R + 1)
        inter(taper, hs((0, 0, CH_F), (kf, 0, -1)), hs((0, 0, CH_R), (kr, 0, 1)))      # floor rises, roof comes down
        sub(b, taper)
        sub(b, box(X_STEP, NL + 1, -9.5, 10.0, 50, Z_STEP))                            # clears the back of the fixed blade
        wedge = box(X_STEP + 1.0, NL + 1, -9.5, 10.0, 50, 62)
        inter(wedge, hs((D_BLADE, 0, ZU0), (-K, 0, 1)))                                # everything below the bevel line
        sub(b, wedge)

        bf = comp.features.baseFeatures.item(0); bf.startEdit()
        bf.updateBody(bf.bodies.item(0), b); bf.finishEdit()
        bd = comp.bRepBodies.item(0)
        bd.name = 'Exit guide v6 (long nose to the blades)'
        bb = bd.boundingBox
        out.append('new guide x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f  vol %.2f cm3  lumps %d' % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
                   bb.minPoint.z * 10, bb.maxPoint.z * 10, bd.volume, bd.lumps.count))

        em = design.exportManager
        stl_dir = os.path.join(BASE, 'print_STL_feeder_v6'); os.makedirs(stl_dir, exist_ok=True)
        tmp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); tc = tmp.component; tc.name = 'TMP_EXPORT'
        e = tb.copy(bd)
        q = e.boundingBox; tr = adsk.core.Matrix3D.create()
        tr.translation = V3(-(q.minPoint.x + q.maxPoint.x) / 2, -(q.minPoint.y + q.maxPoint.y) / 2, -q.minPoint.z); tb.transform(e, tr)
        bf = tc.features.baseFeatures.add(); bf.startEdit(); tc.bRepBodies.add(e, bf); bf.finishEdit()
        eb = tc.bRepBodies.item(tc.bRepBodies.count - 1)
        for fn, body in (('v6_Exit_Guide_long_nose.stl', eb), ('v6_Exit_Guide_long_nose_assembly_position.stl', bd)):
            opt = em.createSTLExportOptions(body, os.path.join(stl_dir, fn))
            opt.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            opt.isBinaryFormat = True
            em.execute(opt)
        q = eb.boundingBox
        out.append('stl v6_Exit_Guide_long_nose.stl  %.1f x %.1f x %.1f mm' % ((q.maxPoint.x - q.minPoint.x) * 10, (q.maxPoint.y - q.minPoint.y) * 10, (q.maxPoint.z - q.minPoint.z) * 10))
        tmp.deleteMe()
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
