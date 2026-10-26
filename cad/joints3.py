# Strip Cutter v3 - joints + motion links (run after build2.py)
import adsk.core, adsk.fusion, math, traceback, os

S = 0.1
HERE = os.path.join(os.path.expanduser('~'), 'Documents', 'Strip_Cutter', 'v3', 'cad')


def run(_context: str):
    out = []
    try:
        G = {'__name__': 'geo', 'PART': 'NONE'}
        exec(compile(open(os.path.join(HERE, 'build3.py'), encoding='utf-8').read(), 'build3.py', 'exec'), G)
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        XR, ZD, ZPN, PVX, PVZ = G['XR'], G['ZD'], G['ZPN'], G['PVX'], G['PVZ']
        Py, Pz, Cy, Cz = G['Py'], G['Pz'], G['Cy'], G['Cz']
        K_O, E_O, R_EFF = G['K_O'], G['E_O'], G['R_EFF']
        lever_state = G['lever_state']

        def P3(x, y, z): return adsk.core.Point3D.create(x * S, y * S, z * S)
        def occ(name):
            o = root.occurrences.itemByName(name + ':1')
            if o is None: raise Exception('missing ' + name)
            return o

        while root.motionLinks.count: root.motionLinks.item(0).deleteMe()
        while root.asBuiltJoints.count: root.asBuiltJoints.item(0).deleteMe()
        for nm in ('Joint_Axes_Y', 'Joint_Axes_X'):
            sk = root.sketches.itemByName(nm)
            if sk: sk.deleteMe()
        sky = root.sketches.add(root.xZConstructionPlane); sky.name = 'Joint_Axes_Y'
        skx = root.sketches.add(root.yZConstructionPlane); skx.name = 'Joint_Axes_X'
        for sk in (sky, skx): sk.isLightBulbOn = False

        def circ(sk, p):
            c = sk.modelToSketchSpace(P3(*p)); c.z = 0
            return sk.sketchCurves.sketchCircles.addByCenterRadius(c, 0.3)
        J = {}
        KP = adsk.fusion.JointKeyPointTypes.CenterKeyPoint
        ZD_ = adsk.fusion.JointDirections.ZAxisJointDirection
        def mk(name, o1, o2, sk, p, kind='rev'):
            geo = adsk.fusion.JointGeometry.createByCurve(circ(sk, p), KP)
            ji = root.asBuiltJoints.createInput(o1, o2, geo)
            if kind == 'rev': ji.setAsRevoluteJointMotion(ZD_)
            else: ji.setAsSliderJointMotion(ZD_)
            j = root.asBuiltJoints.add(ji); j.name = name; J[name] = j
            return j
        frame = occ('Feed_Frame_PRINT')
        mk('J1_Stepper_Drive_Roller', occ('Drive_Rotor'), frame, sky, (XR, 0, ZD))
        mk('J2_Pinch_Arm_Pivot', occ('Pinch_Arm_Assy'), frame, sky, (PVX, 0, PVZ))
        mk('J3_Pinch_Roller', occ('Pinch_Rotor'), occ('Pinch_Arm_Assy'), sky, (XR, 0, ZPN))
        mk('J4_Strip_Feed', occ('Strip_Feed_Piece'), occ('Base_Plate_Al8'), skx, (0, 0, 61), 'slide')
        mk('J5_Wiper_Crank', occ('Crank_Rotor'), occ('Wiper_Motor_12V_(yours)'), skx, (0, Cy, Cz))
        mk('J6_Shear_Lever_Pivot', occ('Lever_Assy'), occ('Main_Plate_Al8'), skx, (0, Py, Pz))
        mk('J7_Link_Crank_Pin', occ('Link_Assy'), occ('Crank_Rotor'), skx, (0, K_O[0], K_O[1]))
        mk('J8_Link_Lever_Pin', occ('Link_Assy'), occ('Lever_Assy'), skx, (0, E_O[0], E_O[1]))

        # which sign of J2 lifts the arm?
        arm = occ('Pinch_Arm_Assy'); j2 = J['J2_Pinch_Arm_Pivot'].jointMotion
        j2.rotationValue = math.radians(2); adsk.doEvents()
        p = adsk.core.Point3D.create(XR * S, 0, ZPN * S); p.transformBy(arm.transform2)
        up = p.z / S - ZPN
        j2.rotationValue = 0; adsk.doEvents()
        sgn = 1 if up > 0 else -1
        out.append('J2 +2deg moves axle z by %.3f -> sign %d' % (up, sgn))
        lo, hi = sorted([sgn * math.radians(-3.58), sgn * math.radians(6.0)])   # world: gap 0 .. gap ~5.3 mm
        lim = j2.rotationLimits
        lim.isMinimumValueEnabled = True; lim.minimumValue = lo
        lim.isMaximumValueEnabled = True; lim.maximumValue = hi
        lim = J['J4_Strip_Feed'].jointMotion.slideLimits
        lim.isMinimumValueEnabled = True; lim.minimumValue = 0
        lim.isMaximumValueEnabled = True; lim.maximumValue = 10.5

        def mlink(name, j1, j2_, v1, v2, rev_):
            mi = root.motionLinks.createInput(j1, j2_)
            mi.valueOne = adsk.core.ValueInput.createByString(v1)
            mi.valueTwo = adsk.core.ValueInput.createByString(v2)
            mi.isReversed = rev_
            ml = root.motionLinks.add(mi); ml.name = name
            return ml
        mlink('ML1_Gears_Opposite', J['J1_Stepper_Drive_Roller'], J['J3_Pinch_Roller'], '360 deg', '360 deg', True)
        mlink('ML2_Roller_to_Strip', J['J1_Stepper_Drive_Roller'], J['J4_Strip_Feed'], '360 deg', '%.4f mm' % (2 * math.pi * R_EFF), False)

        def xang(m):
            a = m.asArray(); return math.degrees(math.atan2(a[9], a[5]))
        def tp(m, y, z):
            q = adsk.core.Point3D.create(0, y * S, z * S); q.transformBy(m); return (q.y / S, q.z / S)
        crank = occ('Crank_Rotor'); lever = occ('Lever_Assy'); drive = occ('Drive_Rotor'); strip = occ('Strip_Feed_Piece')
        jc = J['J5_Wiper_Crank'].jointMotion
        for d in (15, 30, 45, 60, 75, 90, 75, 60, 45, 30, 15, 0):
            jc.rotationValue = math.radians(d); adsk.doEvents()
        K = tp(crank.transform2, *K_O)
        out.append('crank back to 0: K=(%.2f, %.2f) expected (%.2f, %.2f), lever %.3f deg' % (K[0], K[1], K_O[0], K_O[1], xang(lever.transform2)))
        jd = J['J1_Stepper_Drive_Roller'].jointMotion
        jd.rotationValue = math.radians(30); adsk.doEvents()
        out.append('drive +30: pinch %.2f deg, strip x %.3f mm (expect %.3f)' % (
            math.degrees(J['J3_Pinch_Roller'].jointMotion.rotationValue), strip.transform2.translation.x / S, 2 * math.pi * R_EFF / 12))
        jd.rotationValue = 0; adsk.doEvents()
        design.snapshots.add() if design.snapshots.hasPendingSnapshot else None
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
