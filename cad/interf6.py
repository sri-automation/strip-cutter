# interference of the VISIBLE model over the cutter-lever swing (J9) - v6 plywood cutter
import adsk.core, adsk.fusion, math, traceback
EXPECTED = [('wood screw', 'main plate'), ('M4x12', 'moving knife'), ('M8x55', 'M8 nut'), ('M8x55', 'M8 nylock'),
            ('M4x40', 'M4 nut'), ('M4x25', 'M4 lock nut'), ('M3x8', 'M3 nut'), ('drive roller', 'M3x8'),
            ('Exit guide', 'M4x20'), ('Exit guide', 'M4x16'), ('Feed frame', 'M4x12'), ('Entry guide', 'M4x12'),
            ('pinch arm', 'M4x25'), ('M5x45', 'M5 nut'), ('M5x20', 'nut'), ('Feed frame', 'M5x20'), ('Feed frame', 'M4x25'),
            ('rubber washers x3', 'pinch arm'), ('M8x40', 'nylock'), ('pinch arm', 'M8x40'), ('Feed frame', 'M5x25'),
            ('pivot bracket', 'M5'), ('pivot sleeve', 'M5'), ('Feed frame', 'M5x45'),
            ('M6x20', 'gearbox boss'), ('M8x45', 'nylock'), ('M4x8 button', 'output shaft'), ('grub screw', 'output shaft')]
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
        j9 = J['J9_Cutter_Lever'].jointMotion
        drv = J['J10_Crank'].jointMotion if globals().get('DRIVE') else j9
        ents = adsk.core.ObjectCollection.create()
        skip = globals().get('SKIP', ('Net_Strip_Supply', 'Cut_Piece', 'Collection_Bin', 'C6_Base_Board', 'C6_L_Brackets'))
        for i in range(root.occurrences.count):
            o = root.occurrences.item(i)
            if o.isLightBulbOn and not o.component.name.startswith(skip):
                ents.add(o)
        for tgt in globals().get('ANG', [0.0]):
            cur = math.degrees(drv.rotationValue)
            if cur > 180: cur -= 360
            n = max(1, int(abs(tgt - cur) / (15 if globals().get('DRIVE') else 3)) + 1)
            for i in range(1, n + 1):
                drv.rotationValue = math.radians(cur + (tgt - cur) * i / n); adsk.doEvents()
            inp = design.createInterferenceInput(ents)
            inp.areCoincidentFacesIncluded = False
            res = design.analyzeInterference(inp)
            rows = []
            for r in res:
                try: v = r.interferenceBody.volume * 1000.0
                except Exception: v = -1
                rows.append((v, r.entityOne.name, r.entityTwo.name))
            rows.sort(reverse=True)
            un = [r for r in rows if not is_expected(r[1], r[2])]
            out.append('J10 %.0f  J9 %.1f deg: %d interferences, %d unexpected' % (tgt, (math.degrees(j9.rotationValue) + 180) % 360 - 180, len(rows), len(un)))
            for v, a, b in un:
                out.append('   !! %8.3f mm3  %s <-> %s' % (v, a, b))
    except Exception:
        out.append(traceback.format_exc())
    print('\n'.join(out))
