# J10 crank (revolute about the motor shaft), J11 link-crank pin, J12 link-lever pin -> closed four-bar
import adsk.core, adsk.fusion, math, traceback
S = 0.1
def run(_context: str):
    out = []
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        G = globals()
        CY, CZ, PO, DO = G['CY'], G['CZ'], G['PO'], G['DO']
        for i in range(root.asBuiltJoints.count - 1, -1, -1):
            if root.asBuiltJoints.item(i).name[:4] in ('J10_', 'J11_', 'J12_'): root.asBuiltJoints.item(i).deleteMe()
        for j in root.joints:
            if j.name == 'J9_Cutter_Lever': j.jointMotion.rotationValue = 0.0
        for j in root.asBuiltJoints:
            if j.name == 'J9_Cutter_Lever': j.jointMotion.rotationValue = 0.0
        sk = root.sketches.itemByName('Joint_Axes_C6_drive')
        if sk: sk.deleteMe()
        sk = root.sketches.add(root.yZConstructionPlane); sk.name = 'Joint_Axes_C6_drive'; sk.isLightBulbOn = False
        def geo(y, z):
            c = sk.modelToSketchSpace(adsk.core.Point3D.create(0, y * S, z * S)); c.z = 0
            circ = sk.sketchCurves.sketchCircles.addByCenterRadius(c, 0.2)
            return adsk.fusion.JointGeometry.createByCurve(circ, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        plate = root.occurrences.itemByName('C6_Main_Plate_PLY:1')
        crank = root.occurrences.itemByName('C6_Crank_Assy:1')
        link = root.occurrences.itemByName('C6_Link_PLY:1')
        lev = root.occurrences.itemByName('C6_Lever_Assy:1')
        for nm in ('C6_Wiper_Motor_PM11G', 'C6_Motor_Bolts_M6', 'C6_Park_Switch', 'C6_Base_Board_PLY', 'C6_L_Brackets'):
            o = root.occurrences.itemByName(nm + ':1')
            if o: o.isGrounded = True
        for i in range(crank.childOccurrences.count):
            crank.childOccurrences.item(i).isGroundToParent = True
        def rev(a, b, g, name):
            ji = root.asBuiltJoints.createInput(a, b, g)
            ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            j = root.asBuiltJoints.add(ji); j.name = name
            return j
        j10 = rev(crank, plate, geo(CY, CZ), 'J10_Crank')
        out.append('J10 ok')
        if G.get('LOOP', True):
            try:
                rev(link, crank, geo(*PO), 'J11_Link_Crank'); out.append('J11 ok')
                rev(link, lev, geo(*DO), 'J12_Link_Lever'); out.append('J12 ok')
            except Exception as e:
                out.append('loop joints failed: ' + str(e))
        # which way is + for J10 ?
        m = j10.jointMotion
        m.rotationValue = math.radians(3); adsk.doEvents()
        p = adsk.core.Point3D.create(0, (CY + 10) * S, CZ * S); p.transformBy(crank.transform2)
        ang = math.degrees(math.atan2(p.z / S - CZ, p.y / S - CY))
        out.append('J10 +3 deg moves a point at 0 deg to %.2f deg (so + = %s seen from the front)' % (ang, 'CCW' if ang > 0 else 'CW'))
        for j in root.asBuiltJoints:
            if j.name == 'J9_Cutter_Lever': out.append('J9 now %.2f deg' % math.degrees(j.jointMotion.rotationValue))
        m.rotationValue = 0; adsk.doEvents()
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
