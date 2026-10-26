# Strip Cutter - feeder v7: stronger pinch arm at the pressure knob + exit guide v7.
# Pinch_Arm_PRINT: the tab under the knob was 8.8 mm wide with a 5.8 mm slot (1.5 mm walls). Now:
#   - solid deep block from the riser (x -35) to x -10.5, z 70..93 (was 70..85, x -27..-12), same width as the arm,
#   - a wing on the +y side above the exit guide (z 86..93) so the knob/washer seat is 14.5 mm wide,
#   - slot 4.8 mm wide (was 5.8) -> 2 mm walls on the -y side, 7.7 mm on the +y side; seat raised 8 mm to z 93.
# Exit_Guide_PRINT (built from the v5.1 body kept in Exit_Guide_v51_old_PRINT):
#   - side faces trimmed to |y| <= 8.8 above z 60 where the pinch arm swings, washer and roller clearances 1..3 mm deeper,
#   - channel roof raised after the rollers (68.5 instead of 66.0 in the body),
#   - long nose kept but 2.5 mm shorter (old nose end -> fixed blade face taken as 7.5 mm instead of 10).
import adsk.core, adsk.fusion, math, traceback, os

S = 0.1
BASE = os.path.join(os.path.expanduser('~'), 'Documents', 'Strip_Cutter', 'v3')
# pinch arm
Y0, Y1 = -19.0, -10.2
TNX, TNY = -20.0, -14.6
PVX, PVZ, XR = -77.0, 77.0, -45.0
SEAT_Z = 93.0
# exit guide
D_BLADE = 7.5
NL = D_BLADE - 0.6
NOSE_Y, NOSE_Z = (-8.5, 8.9), (54.1, 67.9)
CH_W, CH_F = 6.6, 59.8
K = 3.686 / 2.88
ZU0, Z_STEP = 59.8, 56.3
X_STEP = D_BLADE - 4.5
TIP_F, TIP_R = 60.5, 65.4
TRIM_Y = 8.8


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
        def cyl(p0, p1, r): return tb.createCylinderOrCone(P3(*p0), r * S, P3(*p1), r * S)
        def cyly(y0, y1, x, z, r): return cyl((x, y0, z), (x, y1, z), r)
        def cylz(z0, z1, x, y, r): return cyl((x, y, z0), (x, y, z1), r)
        def hs(p, n):                # half space {q: (q - p).n <= 0}, n in the xz plane
            L = math.hypot(n[0], n[2]); n = (n[0] / L, 0.0, n[2] / L); B = 400.0
            return tb.createBox(adsk.core.OrientedBoundingBox3D.create(P3(p[0] - n[0] * B / 2, p[1], p[2] - n[2] * B / 2),
                                V3(*n), V3(0, 1, 0), B * S, B * S, B * S))
        def below(p0, p1):           # half space under the line through p0, p1 (x, z)
            k = (p1[1] - p0[1]) / (p1[0] - p0[0])
            return hs((p0[0], 0, p0[1]), (-k, 0, 1))
        def uni(a, *bs):
            for b in bs: tb.booleanOperation(a, b, UN)
            return a
        def sub(a, *bs):
            for b in bs: tb.booleanOperation(a, b, DF)
            return a
        def inter(a, *bs):
            for b in bs: tb.booleanOperation(a, b, IN)
            return a
        def backup(name, bkname, label):
            comp = design.allComponents.itemByName(name)
            bk = design.allComponents.itemByName(bkname)
            if bk is None:
                occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                bk = occ.component; bk.name = bkname
                bf = bk.features.baseFeatures.add(); bf.startEdit()
                bk.bRepBodies.add(tb.copy(comp.bRepBodies.item(0)), bf); bf.finishEdit()
                bk.bRepBodies.item(0).name = label
                occ.isLightBulbOn = False
                out.append('kept the old body in %s (hidden)' % bkname)
            return comp, bk.bRepBodies.item(0)
        def put(comp, body, name):
            bf = comp.features.baseFeatures.item(0); bf.startEdit()
            bf.updateBody(bf.bodies.item(0), body); bf.finishEdit()
            bd = comp.bRepBodies.item(0); bd.name = name
            bb = bd.boundingBox
            out.append('%s: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f  %.2f cm3  lumps %d' % (comp.name, bb.minPoint.x * 10, bb.maxPoint.x * 10,
                       bb.minPoint.y * 10, bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10, bd.volume, bd.lumps.count))
            return bd

        # ---------------- pinch arm ----------------
        acomp, asrc = backup('Pinch_Arm_PRINT', 'Pinch_Arm_v6_old_PRINT', 'pinch arm v6 (thin knob tab, as printed)')
        arm = tb.copy(asrc)
        uni(arm, box(-35.0, -10.5, Y0, Y1, 70.0, SEAT_Z),                # deep solid block: riser -> front (stays clear of the main plate when the arm swings down)
                 box(-30.0, -11.0, Y1 - 0.02, -4.5, 86.0, SEAT_Z))        # +y wing above the exit guide: wide seat
        r = 2.4; dx = 2.6                                                # slot 4.8 wide, same length as before (9.8)
        sub(arm, cylz(60, 100, TNX - dx, TNY, r), cylz(60, 100, TNX + dx, TNY, r), box(TNX - dx, TNX + dx, TNY - r, TNY + r, 60, 100))
        bd_arm = put(acomp, arm, 'pinch arm v7 (strong knob seat, PETG-CF)')

        # ---------------- exit guide v7 ----------------
        gcomp, gsrc = backup('Exit_Guide_PRINT', 'Exit_Guide_v51_old_PRINT', 'Exit guide v5.1 (short nose, as printed)')
        g = tb.copy(gsrc)
        uni(g, box(-1.6, NL, NOSE_Y[0], NOSE_Y[1], NOSE_Z[0], NOSE_Z[1]))                       # long nose (fills the old flare)
        # channel: roof raised after the rollers, floor unchanged up to x = 0
        p1 = inter(box(-40.5, -29.0, -CH_W, CH_W, 61.0, 74.0), below((-40.0, 73.0), (-29.0, 68.5)))
        p2 = box(-29.02, -16.0, -CH_W, CH_W, 61.0, 68.5)
        p3 = inter(box(-16.02, -6.0, -CH_W, CH_W, 61.0, 68.6), below((-16.0, 68.5), (-6.0, 66.4)))
        p4 = box(-6.02, 0.01, -CH_W, CH_W, 61.0, 66.4)
        sub(g, p1, p2, p3, p4, box(-2.0, 0.01, -CH_W, CH_W, CH_F, 66.4))
        taper = box(0, NL + 0.3, -CH_W, CH_W, CH_F - 1, 67.0)
        inter(taper, hs((0, 0, CH_F), ((TIP_F - CH_F) / NL, 0, -1)), below((0.0, 66.4), (NL, TIP_R)))     # floor rises, roof comes down
        sub(g, taper)
        # tip underside: clears the back of the fixed blade, then follows its bevel
        sub(g, box(X_STEP, NL + 1, -9.5, 10.0, 50, Z_STEP))
        sub(g, inter(box(X_STEP + 1.0, NL + 1, -9.5, 10.0, 50, 62), hs((D_BLADE, 0, ZU0), (-K, 0, 1))))
        # room for the pinch arm: side faces trimmed above z 60, deeper clearances for its washers and the top roller
        sub(g, box(-62, -7.5, -12.0, -TRIM_Y, 60, 80), box(-62, -26.0, TRIM_Y, 14.0, 60, 80))
        for (ya, yb) in ((7.9, 9.9), (-9.9, -7.9)):
            sub(g, cyly(ya, yb, XR, 71.5, 10.6), box(XR - 10.6, XR + 10.6, ya, yb, 71.5, 82))
        sub(g, cyly(-8.5, 8.5, XR, 73.7, 15.5), box(XR - 15.5, XR + 15.5, -8.5, 8.5, 73.7, 82))
        bd_g = put(gcomp, g, 'Exit guide v7 (arm clearance, taller channel, nose 2.5 mm shorter)')

        # ---------------- checks: arm swung down 0..8 deg about its pivot against the guide, frame and plate ----------------
        others = {}
        for nm in ('Exit_Guide_PRINT', 'Feed_Frame_PRINT', 'C7_Main_Plate_PRINT', 'Drive_Roller_PRINT'):
            c = design.allComponents.itemByName(nm)
            if c is not None: others[nm] = c.bRepBodies.item(0)
        for ang in (0.0, 2.0, 4.0, 6.0, 8.0):
            a = tb.copy(bd_arm)
            m = adsk.core.Matrix3D.create(); m.setToRotation(math.radians(ang), V3(0, 1, 0), P3(PVX, 0, PVZ)); tb.transform(a, m)
            row = []
            for nm, ob in others.items():
                t1 = tb.copy(a); tb.booleanOperation(t1, tb.copy(ob), IN)
                v = t1.volume * 1000 if t1.faces.count else 0.0
                row.append('%s %.1f' % (nm.split('_')[0] + ('' if nm != 'Drive_Roller_PRINT' else 'R'), v))
            out.append('arm %3.0f deg down (roller %.1f mm lower): overlap mm3: %s' % (ang, 32 * math.sin(math.radians(ang)), ', '.join(row)))

        # ---------------- export ----------------
        em = design.exportManager
        stl_dir = os.path.join(BASE, 'print_STL_feeder_v7'); os.makedirs(stl_dir, exist_ok=True)
        tmp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); tc = tmp.component; tc.name = 'TMP_EXPORT'
        def export(body, fn, rot_x_deg):
            e = tb.copy(body)
            if rot_x_deg:
                m = adsk.core.Matrix3D.create(); m.setToRotation(math.radians(rot_x_deg), V3(1, 0, 0), P3(0, 0, 0)); tb.transform(e, m)
            q = e.boundingBox; tr = adsk.core.Matrix3D.create()
            tr.translation = V3(-(q.minPoint.x + q.maxPoint.x) / 2, -(q.minPoint.y + q.maxPoint.y) / 2, -q.minPoint.z); tb.transform(e, tr)
            bf = tc.features.baseFeatures.add(); bf.startEdit(); tc.bRepBodies.add(e, bf); bf.finishEdit()
            eb = tc.bRepBodies.item(tc.bRepBodies.count - 1)
            opt = em.createSTLExportOptions(eb, os.path.join(stl_dir, fn))
            opt.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            opt.isBinaryFormat = True
            em.execute(opt)
            q = eb.boundingBox
            out.append('stl %s  %.1f x %.1f x %.1f mm' % (fn, (q.maxPoint.x - q.minPoint.x) * 10, (q.maxPoint.y - q.minPoint.y) * 10, (q.maxPoint.z - q.minPoint.z) * 10))
        export(bd_arm, 'v7_Pinch_Arm_strong.stl', 90)          # -y face on the bed, as the earlier yoke prints
        export(bd_g, 'v7_Exit_Guide.stl', 0)                    # upright, as v5.1 / v6
        for body, fn in ((bd_arm, 'v7_Pinch_Arm_assembly_position.stl'), (bd_g, 'v7_Exit_Guide_assembly_position.stl')):
            opt = em.createSTLExportOptions(body, os.path.join(stl_dir, fn))
            opt.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(opt)
        tmp.deleteMe()
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
