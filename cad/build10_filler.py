# Strip Cutter v10: gap filler plate (C10_Gap_Filler_PRINT)
# Fills the 2.88 mm space between the main plate front face (x = 0) and the back of the moving knife (x = 2.88),
# above the net opening, so a curled net tip cannot climb behind the moving knife.
# Held by 2 x M4 countersunk screws through holes the user drills in the main plate (nuts behind the plate).
# Coordinates as build9.py (mm): x feed direction, y across, z up.
import adsk.core, adsk.fusion, math, traceback, os

S = 0.1
TF = 2.4                         # filler thickness (8 layers of 0.30); moving knife back face is at 2.88
Z_BOT = 65.6                     # bottom edge: 0.4 below the exit-channel roof (66.0)
PAD_Y, PAD_Z1 = (-13.0, 13.0), 86.0
BAR_Y, BAR_Z = (-44.0, 34.0), (84.0, 100.0)
HOLES = ((-36.0, 92.0), (26.0, 92.0))    # behind these the plate back is free (left of the feed frame / above it)
M4_R, CSK_R = 2.45, 4.7          # M4 clearance 4.9; 90 deg countersink 9.4 at the face -> head about 0.5 below the face
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
        def obox(c, ld, wd, l, w, h):
            return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P3(*c), V3(*ld), V3(*wd), l * S, w * S, h * S))
        def cyl(p0, p1, r, r2=None):
            return tb.createCylinderOrCone(P3(*p0), r * S, P3(*p1), (r if r2 is None else r2) * S)
        def uni(a, *bs):
            for b in bs: tb.booleanOperation(a, b, UN)
            return a
        def sub(a, *bs):
            for b in bs: tb.booleanOperation(a, b, DF)
            return a
        def rrect(t, y0, y1, z0, z1, r, corners):       # plate x 0..t with the listed corners rounded ('00' = y0 z0 ...)
            b = box(0, t, y0, y1, z0, z1)
            for key, (yc, zc, sy, sz) in {'00': (y0, z0, 1, 1), '10': (y1, z0, -1, 1), '01': (y0, z1, 1, -1), '11': (y1, z1, -1, -1)}.items():
                if key in corners:
                    cut = box(-1, t + 1, yc - sy * 0.01, yc + sy * r, zc - sz * 0.01, zc + sz * r)
                    sub(cut, cyl((-2, yc + sy * r, zc + sz * r), (t + 2, yc + sy * r, zc + sz * r), r))
                    sub(b, cut)
            return b

        def filler(t, notch=False):
            b = uni(rrect(t, BAR_Y[0], BAR_Y[1], BAR_Z[0], BAR_Z[1], 4.0, ('00', '10', '01', '11')),
                    rrect(t, PAD_Y[0], PAD_Y[1], Z_BOT, PAD_Z1, 2.0, ('00', '10')))
            # lead-in on the back bottom edge, facing the net opening (45 deg, 0.8 mm)
            sub(b, obox((0, 0, Z_BOT), (0.70710678, 0, -0.70710678), (0, 1, 0), 4.0, 60.0, 2 * 0.8 * 0.70710678))
            for (y, z) in HOLES:
                sub(b, cyl((-1, y, z), (t + 1, y, z), M4_R),
                       cyl((t + 0.02, y, z), (t + 0.02 - (CSK_R - M4_R), y, z), CSK_R + 0.02, M4_R + 0.02))
            if notch:                                   # cut corner marks the thinner plate
                sub(b, obox((t / 2, BAR_Y[1], BAR_Z[1]), (0, 0.70710678, 0.70710678), (1, 0, 0), 2 * 3.5, t + 2, 20.0))
            return b

        # ---- component in the assembly ----
        name = 'C10_Gap_Filler_PRINT'
        body = filler(TF)
        comp = design.allComponents.itemByName(name)
        if comp is not None and comp.features.baseFeatures.count:
            bf = comp.features.baseFeatures.item(0); bf.startEdit()
            bf.updateBody(bf.bodies.item(0), body); bf.finishEdit()
            out.append('patched ' + name)
        else:
            occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component; comp.name = name
            bf = comp.features.baseFeatures.add(); bf.startEdit()
            comp.bRepBodies.add(body, bf); bf.finishEdit()
            out.append('new ' + name)
        bd = comp.bRepBodies.item(0)
        bd.name = 'gap filler plate %.1f mm (PETG-CF, 2 x M4 csk)' % TF
        a = design.appearances.itemByName('PETG blue') or design.appearances.itemByName('PETG-CF black')
        if a: bd.appearance = a
        bb = bd.boundingBox
        out.append('filler x %.2f..%.2f  y %.1f..%.1f  z %.1f..%.1f  vol %.2f cm3' % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
                   bb.minPoint.z * 10, bb.maxPoint.z * 10, bd.volume))

        # ---- STL export: back face on the bed, countersinks up ----
        if globals().get('DO_STL', True):
            em = design.exportManager
            stl_dir = os.path.join(BASE, 'print_STL_cutter_v10'); os.makedirs(stl_dir, exist_ok=True)
            tmp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); tc = tmp.component; tc.name = 'TMP_EXPORT'
            for t, notch, fn in ((TF, False, 'c10_Gap_Filler_2.4mm.stl'), (2.1, True, 'c10_Gap_Filler_2.1mm_cut_corner.stl')):
                b = filler(t, notch)
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
