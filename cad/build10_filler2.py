# Strip Cutter v10b: gap filler v2 - one solid plate, 3.3 mm (the stack 2.4 + 0.9 that worked), with side walls.
# The net now leaves through a window in the filler: roof as before, a wall on each side that reaches down to the
# fixed blade, and a low sill in the bevel pocket of the fixed blade. Same two M4 countersunk holes as v1.
# Coordinates as build9.py (mm): x feed direction (main plate front face x = 0), y across, z up.
import adsk.core, adsk.fusion, math, traceback, os

S = 0.1
TF = 3.3                         # 11 layers of 0.30
Z_ROOF = 65.6                    # window roof (0.4 below the exit-channel roof at 66.0), as v1
WIN_Y = 8.0                      # window half width (channel mouth is +-7.16)
SILL_Z = 59.0                    # top of the sill under the net (channel floor is 59.8, so the net never meets a step)
BODY_Y, BODY_Z1 = (-17.5, 22.0), 86.0     # left wall stops short of the M4 screw head at y -23
BAR_Y, BAR_Z = (-44.0, 34.0), (84.0, 100.0)
HOLES = ((-36.0, 92.0), (26.0, 92.0))
M4_R, CSK_R = 2.45, 4.7
# fixed blade: edge at z 59.7 on the shear plane, 38 deg bevel facing the plate -> its top is z = 56.0 + 1.283 x for x 0..2.88
BEV_Z0, BEV_K, BEV_CLR = 56.0, 3.686 / 2.88, 1.0      # walls keep 1.0 mm (vertical) above the bevel
FLAT_Z = 60.4                    # wall bottom next to the shear plane (0.7 above the fixed blade edge)
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
        def rrect(t, y0, y1, z0, z1, r, corners):
            b = box(0, t, y0, y1, z0, z1)
            for key, (yc, zc, sy, sz) in {'00': (y0, z0, 1, 1), '10': (y1, z0, -1, 1), '01': (y0, z1, 1, -1), '11': (y1, z1, -1, -1)}.items():
                if key in corners:
                    cut = box(-1, t + 1, yc - sy * 0.01, yc + sy * r, zc - sz * 0.01, zc + sz * r)
                    sub(cut, cyl((-2, yc + sy * r, zc + sz * r), (t + 2, yc + sy * r, zc + sz * r), r))
                    sub(b, cut)
            return b
        q = 0.70710678
        def filler(t):
            z0 = BEV_Z0 + BEV_CLR
            b = uni(rrect(t, BAR_Y[0], BAR_Y[1], BAR_Z[0], BAR_Z[1], 4.0, ('00', '10', '01', '11')),
                    box(0, t, BODY_Y[0], BODY_Y[1], z0, BODY_Z1))
            sub(b, box(-1, t + 1, -WIN_Y, WIN_Y, SILL_Z, Z_ROOF))                      # window for the net
            # nothing may sit in the fixed blade's bevel pocket closer than BEV_CLR: remove below z = z0 + k x, but only under FLAT_Z
            L = math.hypot(1.0, BEV_K); n = (BEV_K / L, 0.0, -1.0 / L)
            cutb = obox((n[0] * 10.0, 0.0, z0 + n[2] * 10.0), (1.0 / L, 0.0, BEV_K / L), (0, 1, 0), 60.0, 120.0, 20.0)
            tb.booleanOperation(cutb, box(-5, 20, -60, 60, 30, FLAT_Z), IN)
            sub(b, cutb)
            # lead-ins on the back edges of the window (roof and both sides), 45 deg x 0.8
            sub(b, obox((0, 0, Z_ROOF), (q, 0, -q), (0, 1, 0), 4.0, 2 * WIN_Y, 2 * 0.8 * q))
            zc, zl = 0.5 * (SILL_Z + Z_ROOF), Z_ROOF - SILL_Z
            sub(b, obox((0, WIN_Y, zc), (0, 0, 1), (q, -q, 0), zl, 4.0, 2 * 0.8 * q),
                   obox((0, -WIN_Y, zc), (0, 0, 1), (q, q, 0), zl, 4.0, 2 * 0.8 * q))
            for (y, z) in HOLES:
                sub(b, cyl((-1, y, z), (t + 1, y, z), M4_R),
                       cyl((t + 0.02, y, z), (t + 0.02 - (CSK_R - M4_R), y, z), CSK_R + 0.02, M4_R + 0.02))
            return b

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
        bd.name = 'gap filler v2, %.1f mm, with side walls (PETG-CF, 2 x M4 csk)' % TF
        bb = bd.boundingBox
        out.append('filler x %.2f..%.2f  y %.1f..%.1f  z %.1f..%.1f  vol %.2f cm3  lumps %d' % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10,
                   bb.minPoint.z * 10, bb.maxPoint.z * 10, bd.volume, bd.lumps.count))
        # clearance check against the fixed blade and the exit guide (modelled positions)
        for nm in ('C7_Bed_Knife', 'Exit_Guide_PRINT', 'C7_Main_Plate_PRINT'):
            c = design.allComponents.itemByName(nm)
            if c is None: continue
            t1 = tb.copy(bd); t2 = tb.copy(c.bRepBodies.item(0))
            tb.booleanOperation(t1, t2, IN)
            out.append('overlap with %s: %.3f mm3' % (nm, t1.volume * 1000 if t1.faces.count else 0.0))

        em = design.exportManager
        stl_dir = os.path.join(BASE, 'print_STL_cutter_v10'); os.makedirs(stl_dir, exist_ok=True)
        tmp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); tc = tmp.component; tc.name = 'TMP_EXPORT'
        fn = 'c10_Gap_Filler_v2_3.3mm_side_walls.stl'
        b = filler(TF)
        m = adsk.core.Matrix3D.create(); m.setToRotation(-math.pi / 2, V3(0, 1, 0), adsk.core.Point3D.create(0, 0, 0)); tb.transform(b, m)
        qb = b.boundingBox; tr = adsk.core.Matrix3D.create()
        tr.translation = V3(-(qb.minPoint.x + qb.maxPoint.x) / 2, -(qb.minPoint.y + qb.maxPoint.y) / 2, -qb.minPoint.z); tb.transform(b, tr)
        bf = tc.features.baseFeatures.add(); bf.startEdit(); tc.bRepBodies.add(b, bf); bf.finishEdit()
        eb = tc.bRepBodies.item(tc.bRepBodies.count - 1)
        opt = em.createSTLExportOptions(eb, os.path.join(stl_dir, fn))
        opt.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opt.isBinaryFormat = True
        em.execute(opt)
        qb = eb.boundingBox
        out.append('stl %s  %.1f x %.1f x %.2f mm  %.2f cm3' % (fn, (qb.maxPoint.x - qb.minPoint.x) * 10, (qb.maxPoint.y - qb.minPoint.y) * 10, (qb.maxPoint.z - qb.minPoint.z) * 10, eb.volume))
        tmp.deleteMe()
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
