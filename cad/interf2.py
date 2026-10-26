import adsk.core, adsk.fusion, math, traceback

def run(_context: str):
    out = []
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        J = {root.asBuiltJoints.item(i).name: root.asBuiltJoints.item(i) for i in range(root.asBuiltJoints.count)}
        ml2 = root.motionLinks.itemByName('ML2_Roller_to_Strip')
        jc = J['J5_Wiper_Crank'].jointMotion
        TARGET = globals().get('CRANK', 0.0)
        cur = math.degrees(jc.rotationValue)
        n = max(1, int(abs(TARGET - cur) / 12) + 1)
        for i in range(1, n + 1):
            jc.rotationValue = math.radians(cur + (TARGET - cur) * i / n)
            adsk.doEvents()
        arm = globals().get('ARM', None)
        if arm is not None:
            J['J2_Pinch_Arm_Pivot'].jointMotion.rotationValue = math.radians(arm)
            adsk.doEvents()
        ents = adsk.core.ObjectCollection.create()
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            if o.isLightBulbOn and not o.component.name.startswith(('Net_Strip_Supply', 'Cut_Piece', 'Collection_Bin')):
                ents.add(o)
        inp = design.createInterferenceInput(ents)
        inp.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(inp)
        rows = []
        for r in res:
            try:
                v = r.interferenceBody.volume * 1000.0
            except Exception:
                v = -1
            a = r.entityOne; b = r.entityTwo
            def nm(e):
                try:
                    return e.assemblyContext.fullPathName + '/' + e.name if e.assemblyContext else e.name
                except Exception:
                    return str(e)
            rows.append((v, nm(a), nm(b)))
        rows.sort(reverse=True)
        out.append('crank %.1f deg: %d interferences' % (TARGET, len(rows)))
        for v, a, b in rows[:40]:
            out.append('  %8.3f mm3  %s  <->  %s' % (v, a, b))
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
