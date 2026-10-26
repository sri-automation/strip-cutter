# Strip Cutter v3 - hide non-feeder parts, export print-oriented feeder STLs, save document
import adsk.core, adsk.fusion, math, traceback, os

S = 0.1
BASE = os.path.join(os.path.expanduser('~'), 'Documents', 'Strip_Cutter', 'v3')
FEEDER_SHOW = ('Feed_Frame_PRINT', 'Exit_Guide_PRINT', 'Entry_Guide_PRINT', 'Drive_Rotor', 'Pinch_Arm_Assy', 'Pinch_Rotor',
               'Stepper_23HS5628_NEMA23', 'Stepper_Mount_Screws_M5', 'Exit_Guide_Screws_M4', 'Entry_Guide_Screws_M4',
               'Pinch_Pivot_and_Pressure_Hardware', 'Pressure_Knob_PRINT', 'Strip_Feed_Piece', 'Net_Strip_Supply_12x2.7',
               'Pivot_Bracket_R_PRINT', 'Pivot_Sleeve_PRINT', 'Exit_Tie_Plate_DEMO_PRINT', 'Exit_Tie_Screws_M4')
PRINTS = globals().get('PRINTS_OVR') or [
          ('Pinch_Arm_PRINT', 'y+', 'v4_Pinch_Yoke'), ('Pivot_Bracket_R_PRINT', 'y-', 'v4_Pivot_Bracket'),
          ('Pivot_Sleeve_PRINT', 'y+', 'v4_Pivot_Sleeve'), ('Entry_Guide_PRINT', 'z', 'v4_Entry_Guide'),
          ('Exit_Guide_PRINT', 'y+', 'v4_Exit_Guide'), ('Exit_Tie_Plate_DEMO_PRINT', 'x+', 'v4_Exit_Tie_Plate')]
DO_CAD = globals().get('DO_CAD', True)


def run(_context: str):
    out = []
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        tb = adsk.fusion.TemporaryBRepManager.get()
        UN = adsk.fusion.BooleanTypes.UnionBooleanType; DF = adsk.fusion.BooleanTypes.DifferenceBooleanType
        def P3(x, y, z): return adsk.core.Point3D.create(x * S, y * S, z * S)
        em = design.exportManager
        stl_dir = os.path.join(BASE, globals().get('STL_SUB','print_STL_feeder_v4')); os.makedirs(stl_dir, exist_ok=True)
        tmp_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        tcomp = tmp_occ.component; tcomp.name = 'TMP_EXPORT'
        def orient(b, mode):
            m = adsk.core.Matrix3D.create(); O = adsk.core.Point3D.create(0, 0, 0)
            if mode == 'x+': m.setToRotation(-math.pi / 2, adsk.core.Vector3D.create(0, 1, 0), O)
            elif mode == 'x-': m.setToRotation(math.pi / 2, adsk.core.Vector3D.create(0, 1, 0), O)
            elif mode == 'y+': m.setToRotation(math.pi / 2, adsk.core.Vector3D.create(1, 0, 0), O)
            elif mode == 'y-': m.setToRotation(-math.pi / 2, adsk.core.Vector3D.create(1, 0, 0), O)
            tb.transform(b, m)
            bb = b.boundingBox; t = adsk.core.Matrix3D.create()
            t.translation = adsk.core.Vector3D.create(-(bb.minPoint.x + bb.maxPoint.x) / 2, -(bb.minPoint.y + bb.maxPoint.y) / 2, -bb.minPoint.z)
            tb.transform(b, t)
            return b
        def export_body(tbody, fn):
            bf = tcomp.features.baseFeatures.add(); bf.startEdit()
            tcomp.bRepBodies.add(tbody, bf); bf.finishEdit()
            body = tcomp.bRepBodies.item(tcomp.bRepBodies.count - 1)
            opt = em.createSTLExportOptions(body, os.path.join(stl_dir, fn))
            opt.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
            opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            opt.isBinaryFormat = True
            em.execute(opt)
            bb = body.boundingBox
            return (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10, (bb.maxPoint.z - bb.minPoint.z) * 10, body.volume * 1000
        for nm, mode, fn in PRINTS:
            comp = design.allComponents.itemByName(nm)
            sz = export_body(orient(tb.copy(comp.bRepBodies.item(0)), mode), fn + '.stl')
            out.append('stl %-28s %.1f x %.1f x %.1f mm  %.1f cm3' % (fn, sz[0], sz[1], sz[2], sz[3] / 1000))
            if False and nm == 'Drive_Roller_PRINT':
                b6 = tb.copy(comp.bRepBodies.item(0))
                cy = lambda y0, y1, r: tb.createCylinderOrCone(P3(0, y0, 0), r * S, P3(0, y1, 0), r * S)
                tb.booleanOperation(b6, cy(-7, 16, 3.3), UN)
                tb.booleanOperation(b6, cy(-8, 17, 3.1), DF)
                tb.booleanOperation(b6, tb.createCylinderOrCone(P3(0, 12, 2.0), 1.7 * S, P3(0, 12, 10), 1.7 * S), DF)
                sz = export_body(orient(b6, mode), 'Drive_Roller_6.00mm_shaft.stl')
                out.append('stl %-28s %.1f x %.1f x %.1f mm  %.1f cm3' % ('Drive_Roller_6.00mm_shaft', sz[0], sz[1], sz[2], sz[3] / 1000))
        tmp_occ.deleteMe()
        # hide everything except the feeder
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            o.isLightBulbOn = o.component.name in FEEDER_SHOW
        root.isJointsFolderLightBulbOn = False
        cad = os.path.join(BASE, 'cad')
        if DO_CAD:
            em.execute(em.createSTEPExportOptions(os.path.join(cad, 'Strip_Cutter_v5.step'), root))
            em.execute(em.createFusionArchiveExportOptions(os.path.join(cad, 'Strip_Cutter_v5.f3d'), root))
        app.activeViewport.fit()
        out.append('hidden non-feeder parts; step + f3d written')
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
