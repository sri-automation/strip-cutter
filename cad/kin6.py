# four-bar check: wiper crank at C drives the knife lever through a link to the drive pin D
import math, numpy as np, sys
YP, ZP = -45.0, 54.7
DU, DV = 98.0, 18.0
RD = math.hypot(DU, DV); DEL = math.atan2(DV, DU)
TH_O, TH_C = 27.0, 10.0
E_OFF = 5.0; ZF = 59.8                     # moving knife edge offset; channel floor

def D(th):  # th deg
    a = math.radians(th) + DEL
    return np.array([YP + RD * math.cos(a), ZP + RD * math.sin(a)])

def design(C):
    C = np.array(C, float)
    do, dc = np.linalg.norm(C - D(TH_O)), np.linalg.norm(C - D(TH_C))
    r = abs(do - dc) / 2; L = (do + dc) / 2
    return r, L, ('open=extended' if do > dc else 'open=folded')

def solve(C, r, L, phi, th_guess):
    P = np.array(C) + r * np.array([math.cos(phi), math.sin(phi)])
    # circle about O radius RD  intersect circle about P radius L
    O = np.array([YP, ZP]); d = np.linalg.norm(P - O)
    a = (RD**2 - L**2 + d**2) / (2 * d); h2 = RD**2 - a**2
    if h2 < 0: return None, P
    h = math.sqrt(h2); ex = (P - O) / d; ey = np.array([-ex[1], ex[0]])
    sols = [O + a * ex + h * ey, O + a * ex - h * ey]
    ths = [math.degrees(math.atan2(s[1] - ZP, s[0] - YP) - DEL) for s in sols]
    th = min(ths, key=lambda t: abs(t - th_guess))
    return th, P

def edge_z(th, y):  # moving knife edge line height at world y
    t = math.radians(th)
    # edge line: lever-local v = -E_OFF ; world y = YP + u cos - v sin ; z = ZP + u sin + v cos
    u = (y - YP - E_OFF * math.sin(t)) / math.cos(t)
    return ZP + u * math.sin(t) - E_OFF * math.cos(t)

def run(C, verbose=True):
    r, L, mode = design(C)
    phio = math.atan2(*(D(TH_O) - C)[::-1]) if mode == 'open=extended' else math.atan2(*(C - D(TH_O))[::-1])
    rows = []; th = TH_O
    for k in range(361):
        phi = phio - math.radians(k)          # crank turning clockwise (seen from the front)
        th, P = solve(C, r, L, phi, th)
        Dp = D(th)
        link = (np.array(C) + r * np.array([math.cos(phi), math.sin(phi)])) - Dp
        a = math.radians(th) + DEL
        tang = np.array([-math.sin(a), math.cos(a)])
        dev = math.degrees(math.acos(abs(np.dot(link / np.linalg.norm(link), tang))))
        rows.append((k, th, dev, edge_z(th, -6.6)))
    rows = np.array(rows)
    dth = np.gradient(rows[:, 1], math.radians(1.0))    # deg per rad
    if verbose:
        print('C', C, 'r %.2f L %.2f %s  phi_open %.1f deg' % (r, L, mode, math.degrees(phio)))
        print(' theta range %.2f..%.2f' % (rows[:, 1].min(), rows[:, 1].max()))
        # cut happens theta 17 -> 11.5
        cut = rows[(rows[:, 1] < 17.0) & (rows[:, 1] > 11.5)]
        print(' max transmission deviation %.1f deg (during cut %.1f)' % (rows[:, 2].max(), cut[:, 2].max() if len(cut) else -1))
        for zt, lab in ((62.5 + 0.8, 'flat net + 0.8'), (65.3 + 0.5, '5.5 twist')):
            ok = rows[rows[:, 3] > zt][:, 0]
            print(' knife clear of %-15s: %d deg of 360 (%.2f s at 30 rpm)' % (lab, len(ok), len(ok) / 360 * 2.0))
        # torque per 100 N knife force at 47 mm radius : T = F * R * dtheta/dphi
        g = np.abs(dth) * math.pi / 180   # rad/rad
        m = (rows[:, 1] < 17.0) & (rows[:, 1] > 11.0)
        print(' crank torque per 100 N at the knife (R 47): max during cut %.2f N.m' % ((100 * 0.047 * g[m]).max()))
        idx = np.where(np.diff(np.sign(rows[:, 1] - 11.5)))[0]
        print(' cut window crank deg:', rows[(rows[:, 1] < 17.0) & (rows[:, 1] > 11.5)][:, 0][[0, -1]] if m.any() else None)
    return r, L, rows

if __name__ == '__main__':
    for C in [(125, 42), (125, 45), (125, 40), (128, 42), (7.3, 163.6)]:
        run(np.array(C, float)); print()
