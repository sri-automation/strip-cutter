import adsk.core, adsk.fusion, math, traceback

EXPECTED = [
    ('gearbox', 'M6 mount'), ('crank r16', 'M8x30'), ('lever', 'M8x20'), ('lever', 'M4x16 countersunk'),
    ('Main plate', 'M5x20 SHCS'), ('pinch arm', 'M4x25'), ('Exit guide', 'M4x20'), ('Feed frame', 'M4x12'),
    ('Entry guide', 'M4x12'), ('KW11', ''), ('lever', 'roller'), ('M4x40', 'M4 nut'), ('M4x25', 'M4 lock nut'),
    ('feeding net', ''), ('M3x8', 'M3 nut'), ('blade clamp', 'M4x16'), ('drive roller', 'M3x8'),
]


def is_expected(a, b):
    for p, q in EXPECTED:
        for x, y in ((a, b), (b, a)):
            if p in x and q in y:
                return True
    return False


def run(_context: str):
    out = []
    try:
        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        J = {root.asBuiltJoints.item(i).name: root.asBuiltJoints.item(i) for i in range(root.asBuiltJoints.count)}
        j2 = J['J2_Pinch_Arm_Pivot'].jointMotion
        arm_occ = root.occurrences.itemByName('Pinch_Arm_Assy:1')
        def axle_z():
            p = adsk.core.Point3D.create(-4.5, 0, 7.7); p.transformBy(arm_occ.transform2); return p.z * 10, p.x * 10
        ents = adsk.core.ObjectCollection.create()
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            if not o.component.name.startswith(('Net_Strip_Supply', 'Cut_Piece', 'Collection_Bin')):
                ents.add(o)
        for tgt in globals().get('ARMS', [0.0]):
            cur = math.degrees(j2.rotationValue)
            if cur > 180: cur -= 360
            n = max(1, int(abs(tgt - cur) / 0.5) + 1)
            for i in range(1, n + 1):
                j2.rotationValue = math.radians(cur + (tgt - cur) * i / n)
                adsk.doEvents()
            z, x = axle_z()
            gap = math.hypot(x + 45, z - 45) - 30
            inp = design.createInterferenceInput(ents)
            inp.areCoincidentFacesIncluded = False
            res = design.analyzeInterference(inp)
            rows = []
            for r in res:
                try: v = r.interferenceBody.volume * 1000.0
                except Exception: v = -1
                a = r.entityOne.name; b = r.entityTwo.name
                rows.append((v, a, b))
            rows.sort(reverse=True)
            unexp = [r for r in rows if not is_expected(r[1], r[2])]
            out.append('ARM joint %.2f deg -> axle z %.2f x %.2f, roller gap %.2f mm: %d interferences, %d unexpected' % (
                math.degrees(j2.rotationValue), z, x, gap, len(rows), len(unexp)))
            for v, a, b in unexp:
                out.append('   !! %8.3f mm3  %s <-> %s' % (v, a, b))
            if globals().get('VERBOSE'):
                for v, a, b in rows:
                    out.append('      %8.3f mm3  %s <-> %s' % (v, a, b))
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
