# Strip Cutter v10: shims for the gap filler plate (same outline and holes, no countersink).
# They go BEHIND the countersunk filler, against the main plate, to set the total thickness in 0.3 mm steps.
# Tongue ends 0.9 mm higher than the filler's (z 66.5), level with the roof of the net opening, so the filler's lead-in chamfer still guides the net.
import adsk.core, adsk.fusion, math, traceback, os

S = 0.1
Z_BOT = 66.5
PAD_Y, PAD_Z1 = (-13.0, 13.0), 86.0
BAR_Y, BAR_Z = (-44.0, 34.0), (84.0, 100.0)
HOLES = ((-36.0, 92.0), (26.0, 92.0))
M4_R = 2.45
SHIMS = ((0.6, 1), (0.9, 2), (1.2, 3))          # thickness, number of notches in the top edge
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
        def P3(x, y, z): return adsk.core.Point3D.create(x * S, y * S, z * S)
        def V3(x, y, z): return adsk.core.Vector3D.create(x, y, z)
        def box(x0, x1, y0, y1, z0, z1):
            return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                                V3(1, 0, 0), V3(0, 1, 0), abs(x1 - x0) * S, abs(y1 - y0) * S, abs(z1 - z0) * S))
        def cyl(p0, p1, r):
            return tb.createCylinderOrCone(P3(*p0), r * S, P3(*p1), r * S)
        def uni(a, *bs):
            for b in bs: tb.booleanOperation(a, b, UN)
            return a
        def sub(a, *bs):
            for b in bs: tb.booleanOperation(a, b, DF)
            return a
        def rrect(t, y0, y1, z0, z1, r, corners):
            b = box(0, t, y0, y1, z0, z1)
            for key, (yc, zc, sy, sz) in {'00': (y0, z0, 1, 1), '10': (y1, z0, -1, 1), '01': (y0, z1, 1, -1), '11': (y1, z1, -1, -1)}.items():
                if key in corners:
                    cut = box(-1, t + 1, yc - sy * 0.01, yc + sy * r, zc - sz * 0.01, zc + sz * r)
                    sub(cut, cyl((-2, yc + sy * r, zc + sz * r), (t + 2, yc + sy * r, zc + sz * r), r))
                    sub(b, cut)
            return b
        def shim(t, notches):
            b = uni(rrect(t, BAR_Y[0], BAR_Y[1], BAR_Z[0], BAR_Z[1], 4.0, ('00', '10', '01', '11')),
                    rrect(t, PAD_Y[0], PAD_Y[1], Z_BOT, PAD_Z1, 2.0, ('00', '10')))
            for (y, z) in HOLES:
                sub(b, cyl((-1, y, z), (t + 1, y, z), M4_R))
            for i in range(notches):                    # notches in the top edge mark the thickness
                yn = -5.0 + 7.0 * (i - (notches - 1) / 2.0)
                sub(b, cyl((-1, yn, BAR_Z[1]), (t + 1, yn, BAR_Z[1]), 2.2))
            return b

        em = design.exportManager
        stl_dir = os.path.join(BASE, 'print_STL_cutter_v10'); os.makedirs(stl_dir, exist_ok=True)
        tmp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); tc = tmp.component; tc.name = 'TMP_EXPORT'
        for t, n in SHIMS:
            fn = 'c10_Shim_%.1fmm_%d_notch%s.stl' % (t, n, '' if n == 1 else 'es')
            b = shim(t, n)
            m = adsk.core.Matrix3D.create(); m.setToRotation(-math.pi / 2, V3(0, 1, 0), adsk.core.Point3D.create(0, 0, 0)); tb.transform(b, m)
            q = b.boundingBox; tr = adsk.core.Matrix3D.create()
            tr.translation = V3(-(q.minPoint.x + q.maxPoint.x) / 2, -(q.minPoint.y + q.maxPoint.y) / 2, -q.minPoint.z); tb.transform(b, tr)
            bf = tc.features.baseFeatures.add(); bf.startEdit(); tc.bRepBodies.add(b, bf); bf.finishEdit()
            eb = tc.bRepBodies.item(tc.bRepBodies.count - 1)
            opt = em.createSTLExportOptions(eb, os.path.join(stl_dir, fn))
            opt.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            opt.isBinaryFormat = True
            em.execute(opt)
            q = eb.boundingBox
            out.append('stl %s  %.1f x %.1f x %.2f mm  %.2f cm3' % (fn, (q.maxPoint.x - q.minPoint.x) * 10, (q.maxPoint.y - q.minPoint.y) * 10, (q.maxPoint.z - q.minPoint.z) * 10, eb.volume))
        tmp.deleteMe()
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
