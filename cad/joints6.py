# J9: cutter lever pivot (revolute about the x-parallel axis through the pivot); angle 0 = park (open)
import adsk.core, adsk.fusion, math, traceback, os
S = 0.1
def run(_context: str):
    out = []
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        YP, ZP, TH_OPEN, TH_CLOSED = globals()['YP'], globals()['ZP'], globals()['TH_OPEN'], globals()['TH_CLOSED']
        for i in range(root.asBuiltJoints.count - 1, -1, -1):
            if root.asBuiltJoints.item(i).name.startswith('J9_'): root.asBuiltJoints.item(i).deleteMe()
        sk = root.sketches.itemByName('Joint_Axes_C6')
        if sk: sk.deleteMe()
        sk = root.sketches.add(root.yZConstructionPlane); sk.name = 'Joint_Axes_C6'; sk.isLightBulbOn = False
        c = sk.modelToSketchSpace(adsk.core.Point3D.create(0, YP * S, ZP * S)); c.z = 0
        circ = sk.sketchCurves.sketchCircles.addByCenterRadius(c, 0.3)
        geo = adsk.fusion.JointGeometry.createByCurve(circ, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        lev = root.occurrences.itemByName('C6_Lever_Assy:1'); plate = root.occurrences.itemByName('C6_Main_Plate_PLY:1')
        plate.isGrounded = True
        for nm in ('C6_Base_Board_PLY', 'C6_L_Brackets', 'C6_Bed_Knife', 'C6_Bed_Ledge_PRINT', 'C6_Bed_Knife_Screws', 'C6_Pivot_Hardware'):
            o = root.occurrences.itemByName(nm + ':1')
            if o: o.isGrounded = True
        for i in range(lev.childOccurrences.count):
            lev.childOccurrences.item(i).isGroundToParent = True
        ji = root.asBuiltJoints.createInput(lev, plate, geo)
        ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        j = root.asBuiltJoints.add(ji); j.name = 'J9_Cutter_Lever'
        m = j.jointMotion
        m.rotationValue = math.radians(3); adsk.doEvents()
        p = adsk.core.Point3D.create(0, (YP + 100) * S, ZP * S)
        q = adsk.core.Point3D.create(0, (YP + 100 * math.cos(math.radians(TH_OPEN))) * S, (ZP + 100 * math.sin(math.radians(TH_OPEN))) * S)
        q.transformBy(lev.transform2)
        ang = math.degrees(math.atan2(q.z / S - ZP, q.y / S - YP))
        m.rotationValue = 0; adsk.doEvents()
        sgn = 1 if ang > TH_OPEN else -1
        lo, hi = sorted([0.0, sgn * math.radians(TH_CLOSED - TH_OPEN)])
        L = m.rotationLimits
        L.isMinimumValueEnabled = True; L.minimumValue = lo
        L.isMaximumValueEnabled = True; L.maximumValue = hi
        out.append('J9 +3deg -> lever angle %.2f (ref %.1f); sign %d; limits %.1f .. %.1f deg' % (ang, TH_OPEN, sgn, math.degrees(lo), math.degrees(hi)))
        globals()['SGN'] = sgn
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
