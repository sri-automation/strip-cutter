# Strip Cutter v11: exit guide extension ("nozzle"), one printed part, PETG-CF.
# The printed exit guide on the machine ends about 10 mm behind the front face of the fixed blade, so the net
# crossed an open pocket (the main-plate window + the gap in front of the plate). This part closes it:
#   - a tube that goes back through the main-plate window to the end of the exit guide,
#   - a flange in the gap (3.3 mm, same two M4 countersunk holes as the gap filler),
#   - a tip whose underside follows the bevel of the fixed blade and whose front is flush with the flange.
# Coordinates as the CAD (mm): x feed direction (main plate front face x = 0), y across (+y motor side), z up.
import numpy as np, trimesh, math, sys
import manifold3d as mf
M = mf.Manifold
SEG = 96
T = 3.3                         # flange thickness = proven filler thickness (upper blade passes in front of it)
GF = 3.6                        # assumed front face of the fixed blade (user: further out than 3.3, less than 3.9)
K = 3.686 / 2.88                # fixed blade bevel: rise per mm (38 deg bevel on a 2.88 blade)
ZU0 = 59.9                      # the underside line passes through (GF, ZU0): the blade edge sits here when its bevel touches the tip
XR = -5.5                       # rear end of the tube (exit guide front end measured at about GF - 10 = -6.4)
TUBE_Y, TUBE_Z = (-8.5, 8.9), (56.2, 67.8)       # fits the window (y -10..10.4, z 53..69) with 1.2 mm or more all round; bottom level with the tip so it prints without a ledge
IN_W, IN_F, IN_R = 7.6, 58.9, 66.9               # inlet: half width, floor, roof (guide channel is +-6.6, 59.8..66.0)
OUT_W, OUT_F, OUT_R = 7.0, 60.4, 65.2            # outlet at the front face: half width, floor (0.5 above the blade edge), roof
BODY_Y, BODY_Z1 = (-17.5, 22.0), 86.0
BAR_Y, BAR_Z = (-44.0, 34.0), (84.0, 100.0)
HOLES = ((-36.0, 92.0), (26.0, 92.0))
M4_R, CSK_R = 2.45, 4.7

def box(x0, x1, y0, y1, z0, z1): return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
def cylx(x0, x1, y, z, r, r2=None): return M.cylinder(x1 - x0, r, r if r2 is None else r2, SEG).rotate([0, 90, 0]).translate([x0, y, z])
def hull(pts): return M.hull_points(np.array(pts, dtype=float))
def zu(x): return max(ZU0 - K * 2.88, ZU0 - K * (GF - x))       # underside of everything in front of the plate

def nozzle():
    r = 4.0
    bar = M.batch_hull([cylx(0, T, y, z, r) for y in (BAR_Y[0] + r, BAR_Y[1] - r) for z in (BAR_Z[0] + r, BAR_Z[1] - r)])
    xk = GF - 2.88
    prof = [(0, BODY_Z1), (0, zu(0)), (xk, zu(xk)), (T, zu(T)), (T, BODY_Z1)]
    body = hull([(x, y, z) for (x, z) in prof for y in BODY_Y])
    tube = box(XR, 0.01, TUBE_Y[0], TUBE_Y[1], TUBE_Z[0], TUBE_Z[1])
    part = bar + body + tube
    # channel: straight taper from the inlet to the outlet, extended a little past both ends
    def sect(x):
        t = (x - XR) / (T - XR)
        return (IN_W + (OUT_W - IN_W) * t, IN_F + (OUT_F - IN_F) * t, IN_R + (OUT_R - IN_R) * t)
    pts = []
    for x in (XR - 0.2, T + 0.2):
        w, f, rr = sect(x)
        pts += [(x, -w, f), (x, w, f), (x, -w, rr), (x, w, rr)]
    part = part - hull(pts)
    for (y, z) in HOLES:
        part = part - cylx(-1, T + 1, y, z, M4_R) - cylx(T - (CSK_R - M4_R), T + 0.02, y, z, M4_R, CSK_R + 0.02)
    return part

def tm(m):
    mm = m.to_mesh(); return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts)

if __name__ == '__main__':
    out = sys.argv[1]
    a = tm(nozzle())
    print('assembly: watertight', a.is_watertight, 'bodies', len(a.split()), 'vol cm3', round(a.volume / 1000, 2), 'bounds', a.bounds.round(2).tolist())
    a.export(out + '/c11_Exit_Nozzle_assembly_position.stl')
    p = a.copy()
    R = trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0])     # front face down on the bed, tube pointing up
    p.apply_transform(R)
    b = p.bounds
    p.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    print('print: bounds', p.bounds.round(2).tolist(), 'size', (p.bounds[1] - p.bounds[0]).round(2).tolist())
    p.export(out + '/c11_Exit_Nozzle_3.3mm.stl')
