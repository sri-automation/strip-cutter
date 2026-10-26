# 1:1 templates for the plywood cutter + wiper-motor drive (print at 100 %, check the 100 mm scale bar)
import math, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, Polygon
import numpy as np
from shapely.geometry import Point, box as sbox
from shapely.ops import unary_union

YP, ZP = -45.0, 54.7; ZB = 59.7; BW, BL = 28.75, 82.0; YA = -36.0; E_OFF = 5.0; U0 = 10.0
DU, DV = 98.0, 18.0
CY, CZ = 125.0, 42.0; R_CR, L_LK = 13.3, 103.4
BOSS_R = 44.5 / math.sqrt(3.0); BOSS_ANG = (0.0, 120.0, 240.0); SW_R = 24.5
a_ = math.radians(27.0) + math.atan2(DV, DU); DO = (YP + math.hypot(DU, DV) * math.cos(a_), ZP + math.hypot(DU, DV) * math.sin(a_))
PHI_O = math.atan2(DO[1] - CZ, DO[0] - CY)
uo = (math.cos(PHI_O), math.sin(PHI_O)); to = (-uo[1], uo[0])
def at(rad, tan): return (CY + rad * uo[0] + tan * to[0], CZ + rad * uo[1] + tan * to[1])
SW_HOLES = [at(SW_R + 7.5, t) for t in (12.0 - 4.75, 12.0 + 4.75)]

def page(pdf, title, W, H, x0, x1, y0, y1, ox, oy, scale=1.0):
    fig = plt.figure(figsize=(W / 25.4, H / 25.4))
    ax = fig.add_axes([ox / W, oy / H, (x1 - x0) * scale / W, (y1 - y0) * scale / H])
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
    fig.text(0.5, 1 - 8 / H, title, ha='center', va='top', fontsize=10.5, weight='bold')
    sb = fig.add_axes([12 / W, 7 / H, 100 / W, 5 / H]); sb.set_xlim(0, 100); sb.set_ylim(0, 5); sb.axis('off')
    sb.add_patch(Rectangle((0, 1.5), 100, 2, fill=False, lw=0.6))
    for k in range(0, 101, 10): sb.plot([k, k], [1.5, 3.5 + (1 if k % 50 == 0 else 0)], 'k-', lw=0.5)
    fig.text(116 / W, 8.5 / H, ('<- must measure exactly 100 mm (print at 100 %, "actual size")' if scale == 1.0
                                else '<- 100 mm bar is for printer check only; this page is NOT full size'), fontsize=6.5)
    return fig, ax

def hole(ax, x, y, d, lab=None, dx=2, dy=2, cross=True, fs=5.5, **kw):
    ax.add_patch(Circle((x, y), d / 2, fill=False, lw=0.7, **kw))
    if cross:
        ax.plot([x - d / 2 - 1.5, x + d / 2 + 1.5], [y, y], 'k-', lw=0.3); ax.plot([x, x], [y - d / 2 - 1.5, y + d / 2 + 1.5], 'k-', lw=0.3)
    if lab: ax.text(x + dx, y + dy, lab, fontsize=fs)

def dim(ax, p, q, txt, off=(0, 0), fs=5.5):
    ax.annotate('', xy=q, xytext=p, arrowprops=dict(arrowstyle='<->', lw=0.4))
    ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], txt, fontsize=fs, ha='center')

def notes(fig, x, y, lines, fs=6.5):
    fig.text(x, y, '\n'.join(lines), fontsize=fs, va='top')

with PdfPages('Cutter_v6_templates_1to1_A4.pdf') as pdf:
    # ---------------- page 1: main plate FRONT face, landscape ----------------
    fig, ax = page(pdf, 'MAIN PLATE  (8 mm plywood, 240 x 120)  -  FRONT face (knife side).  Stepper / motor side on the RIGHT.',
                   297, 210, -72, 180, -14, 128, ox=22, oy=48)
    ax.add_patch(Rectangle((-65, 0), 240, 120, fill=False, lw=1.2))
    ax.add_patch(Rectangle((-10, 53), 20.4, 16, fill=True, fc='0.85', ec='k', lw=0.9))
    ax.text(0.2, 61, 'CUT OUT\n20.4 x 16', fontsize=5, ha='center', va='center')
    hole(ax, YP, ZP, 8.2, 'lever pivot: drill 8.2', 5, 3)
    for (y, z) in [(-23, 70), (21, 44)]:
        hole(ax, y, z, 4.5, 'M4 csk -> feed frame', 3, 2, fs=5); ax.add_patch(Circle((y, z), 4.4, fill=False, lw=0.4, ls=':'))
    ax.add_patch(Rectangle((YA, ZB - BW), BL, BW, fill=False, lw=0.6, ls='--'))
    ax.text(YA + 1, ZB - 3.2, 'bed knife (sharp edge UP)', fontsize=5)
    ax.add_patch(Rectangle((YA + 3, ZB - BW - 8), BL - 6, 8, fill=False, lw=0.6, ls='-.'))
    ax.text(YA + 5, ZB - BW - 6.5, 'printed ledge', fontsize=5)
    for y in (YA + 11, YA + 41, YA + 71): hole(ax, y, ZB - BW - 4, 2.5)
    for y in (YA + 15, YA + 67): hole(ax, y, 40, 2.5)
    ax.text(YA + 20, 36, 'knife screws: mark through the blade U-slots', fontsize=4.5)
    for y0 in (-62, 48, 152):
        ax.add_patch(Rectangle((y0, 0), 20, 25, fill=False, lw=0.5, ls=':')); ax.text(y0 + 1, 11, 'L-bracket', fontsize=4.5)
    ax.plot([0, 0], [0, 120], 'k:', lw=0.3); ax.text(0.5, 116, 'net centre line', fontsize=4.5)
    # motor
    hole(ax, CY, CZ, 15, None)
    ax.text(CY + 1.5, CZ - 5, 'motor shaft\nhole 15 mm', fontsize=5)
    ax.add_patch(Circle((CY, CZ), BOSS_R, fill=False, lw=0.4, ls=':'))
    for a in BOSS_ANG:
        y, z = CY + BOSS_R * math.cos(math.radians(a)), CZ + BOSS_R * math.sin(math.radians(a))
        hole(ax, y, z, 6.5); ax.add_patch(Circle((y, z), 6.3, fill=False, lw=0.4, ls=':'))
    ax.text(CY + BOSS_R + 7, CZ + 2, 'M6 csk x3\n(44.5 apart -\ncheck with\nthe motor!)', fontsize=4.8)
    ax.add_patch(Circle((CY, CZ), R_CR + 11, fill=False, lw=0.4, ls=(0, (4, 2)), ec='b'))
    ax.text(CY - 8, CZ + R_CR + 12.5, 'crank sweep', fontsize=4.5, color='b')
    # park switch outline
    c = at(SW_R + 7.5, 12.0)
    corners = [(c[0] + sx * 10 * to[0] + sy * 5 * uo[0], c[1] + sx * 10 * to[1] + sy * 5 * uo[1]) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ax.add_patch(Polygon(corners, closed=True, fill=False, lw=0.6, ls='--'))
    for (y, z) in SW_HOLES: hole(ax, y, z, 2.0)
    r0 = at(SW_R, 0.0); ax.add_patch(Circle(r0, 2.5, fill=False, lw=0.5))
    ax.text(c[0] - 38, c[1] + 6, 'park microswitch\n(roller here)', fontsize=4.8)
    dim(ax, (-65, -5), (YP, -5), '20'); dim(ax, (-65, -10), (CY, -10), '190 to motor centre')
    dim(ax, (-68, 0), (-68, ZP), '54.7', (-3, 0)); dim(ax, (178, 0), (178, CZ), '42', (3, 0)); dim(ax, (178, 0), (178, 120), '120', (5, 30))
    dim(ax, (-65, 124), (-10, 124), '55'); dim(ax, (-10, 124), (10.4, 124), '20.4', (0, 1.5)); dim(ax, (10.4, 124), (175, 124), '240 overall', (40, 1.5))
    notes(fig, 12 / 297, 44 / 210, [
        'Tape on the plywood, cut the outline and the window, drill.  Pivot 8.2 mm (M8).  Motor shaft 15 mm (spade bit).  M4 frame screws: 4.5 mm + countersink this face.',
        'MOTOR HOLES: drill the 15 mm shaft hole first. Put the motor behind the plate, shaft through the hole, body pointing UP and to the right (away from the stepper).',
        '   Dab paint/marker on the 3 boss tops, press the motor on, the dots show the true hole centres. Drill 6.5 mm, countersink this face for M6 x 20 flat heads.',
        'Knife / ledge / switch holes: drill 2.5 mm pilots when you fit those parts (mark through the real parts).'], fs=6.2)
    pdf.savefig(fig); plt.close(fig)

    # ---------------- page 2: lever (unchanged geometry) ----------------
    fig, ax = page(pdf, 'LEVER  (8 mm plywood)  -  FRONT face (hub side). Pivot on the LEFT.', 210, 297, -30, 125, -30, 45, ox=25, oy=150)
    shp = unary_union([Point(0, 0).buffer(20, 128), sbox(0, 2, 96, 34), Point(96, 18).buffer(16, 128)])
    xs, ys = shp.exterior.xy; ax.plot(xs, ys, 'k-', lw=1.1)
    hole(ax, 0, 0, 16.5, 'pivot hole 16-17 mm\n(spade bit / drill + file)', 10, 6)
    for a in (120, 200, 280): hole(ax, 16 * math.cos(math.radians(a)), 16 * math.sin(math.radians(a)), 2.5)
    ax.text(-28, -26, 'pilots 2.5 for the hub screws (3.5 x 12)', fontsize=5.5)
    for a in (60, 180, 300): hole(ax, DU + 11 * math.cos(math.radians(a)), DV + 11 * math.sin(math.radians(a)), 2.5)
    ax.add_patch(Circle((DU, DV), 14, fill=False, lw=0.5, ls='--')); ax.text(DU - 14, DV + 16, 'drive boss (3 x 3.5x12)', fontsize=5.5)
    ax.add_patch(Rectangle((U0, -E_OFF), BL, BW, fill=False, lw=0.6, ls='--'))
    ax.text(U0 + 2, -E_OFF + 1, 'moving knife on the BACK face, sharp edge DOWN: edge 7 mm below the lever edge, end 10 mm from pivot centre', fontsize=5)
    for hu in (41 - 12.7, 41 + 12.7): hole(ax, U0 + hu, BW - E_OFF - 5.8, 4.5, 'M4', 3, 2)
    ax.text(U0 + 25, 11.5, '(mark the two M4 holes THROUGH the blade, then drill 4.5)', fontsize=5)
    dim(ax, (0, 38), (96, 38), '96 to the end-arc centre', (0, 1.5)); dim(ax, (-24, 0), (-24, 34), '34', (-3, 0)); dim(ax, (-27, -5), (-27, 2), '7', (-2.5, 0))
    notes(fig, 0.07, 0.43, [
        'Cut the outline (jigsaw / coping saw), bore the 16-17 mm pivot hole, drill the 2.5 mm pilots.',
        'Drive-boss pilots: max 6 mm deep - the moving knife sits behind one of them.',
        'The knife goes on the BACK face (the face toward the main plate), bevel against the plywood, flat face outward.',
        'Clamp the blade 7.0 mm below and parallel to the lever\'s straight bottom edge, its end 10 mm right of the pivot centre,',
        'mark the 2 threaded holes through the blade, drill 4.5, fix with M4x12 + 2 washers from the front (tip must NOT stick out',
        'of the blade\'s flat face - add a washer if it does).',
        'Drive pin: M8 x 45 hex bolt, head in the printed drive boss (hex pocket against the lever), thread pointing out.'], fs=7)
    pdf.savefig(fig); plt.close(fig)

    # ---------------- page 3: link 1:1 + crank stack ----------------
    fig, ax = page(pdf, 'LINK  (8 mm plywood)  -  1:1', 210, 297, -15, 120, -15, 15, ox=38, oy=215)
    shp = unary_union([Point(0, 0).buffer(11, 128), Point(L_LK, 0).buffer(11, 128), sbox(0, -11, L_LK, 11)])
    xs, ys = shp.exterior.xy; ax.plot(xs, ys, 'k-', lw=1.1)
    hole(ax, 0, 0, 8.0, 'drill 8', 5, 4); hole(ax, L_LK, 0, 8.0, 'drill 8', -14, 4)
    dim(ax, (0, -13.5), (L_LK, -13.5), '%.1f  hole centre to hole centre' % L_LK, (0, -3.5))
    ax.text(0, 12.5, 'crank end', fontsize=6); ax.text(L_LK - 14, 12.5, 'lever end', fontsize=6)
    notes(fig, 0.07, 0.70, [
        'Drill the two 8 mm holes square to the face (drill press or a guide block). Check the centre distance: 103-104 mm is fine.',
        'Round the ends, sand the edges. A smear of grease in both holes.',
        '',
        'STACK ON EACH M8 PIN (lever pin and crank pin are the same):',
        '   printed boss  |  M8 washer  |  LINK  |  M8 washer  |  M8 nylock  (snug, then back 1/6 turn so the link turns freely)',
        '',
        'The link must clear the M4 screw + washer on the end of the motor shaft by 1-2 mm.',
        'If it rubs: add one more M8 washer under the link on BOTH pins (keeps the link square).',
        'If there is a big gap (> 4 mm) that\'s fine - nothing to change.',
        '',
        'CRANK ON THE MOTOR SHAFT:',
        '   1. Push the M8 x 45 crank-pin bolt through the crank from the flat (back) side; its head sits in the hex pocket.',
        '   2. Slide the M4 nut sideways into the slot next to the small radial hole; screw in the M4 x 10 grub screw a few turns.',
        '   3. Slide the crank on the shaft, flat side toward the plate, until its hub face is flush with the shaft end.',
        '   4. Turn the crank until the grub screw drops into the slot on the shaft; tighten it. Check there is ~1.5 mm gap to the plate.',
        '   5. M4 x 6 screw + 12 mm washer into the shaft end (keeps the crank from walking off). Only snug; the thread is 5 mm deep.'], fs=7)
    pdf.savefig(fig); plt.close(fig)

    # ---------------- page 4: base board layout (1:2) ----------------
    fig, ax = page(pdf, 'BASE BOARD LAYOUT  (8 mm plywood 285 x 275)  -  seen from ABOVE, scale 1:2  (NOT full size)',
                   210, 297, -140, 160, -100, 190, ox=30, oy=95, scale=0.5)
    ax.add_patch(Rectangle((-135, -95), 285, 275, fill=False, lw=1.0))
    ax.add_patch(Rectangle((-8, -65), 8, 240, fill=True, fc='0.8', ec='k', lw=0.8)); ax.text(-6, 150, 'main plate', rotation=90, fontsize=6)
    ax.add_patch(Rectangle((-86, -27), 78, 103, fill=False, lw=0.8, ec='b')); ax.text(-84, 70, 'feed frame', fontsize=6, color='b')
    ax.add_patch(Rectangle((-118, -19), 64, 35.5, fill=False, lw=0.5, ec='b', ls='--')); ax.text(-116, -26, 'entry guide', fontsize=5.5, color='b')
    ax.add_patch(Rectangle((-73.2, 22.9), 62.2, 57.6, fill=False, lw=0.5, ec='b', ls=':')); ax.text(-70, 38, 'NEMA23', fontsize=5.5, color='b')
    ax.add_patch(Rectangle((-44, 91), 36, 68, fill=False, lw=0.6, ec='r', ls='--')); ax.text(-82, 125, 'wiper gearbox\n(body goes UP)', fontsize=5.5, color='r')
    for (x, y) in [(-20, 3), (-40, 12), (-40, -12), (-80, 13.5)]:
        ax.add_patch(Circle((x, y), 2.5, fill=True, fc='b'))
    ax.text(-128, -5, 'feed frame\nscrews (4)', fontsize=5.5, color='b')
    for y0 in (-62, 48, 152):
        ax.add_patch(Rectangle((0, y0), 25, 20, fill=False, lw=0.6)); ax.text(3, y0 + 7, 'L', fontsize=6)
    ax.plot([-135, 150], [0, 0], 'k:', lw=0.4); ax.text(60, 2, 'net centre line  ->  feed direction', fontsize=6)
    ax.add_patch(Rectangle((8, -40), 60, 40, fill=False, lw=0.5, ls=':')); ax.text(10, -36, 'cut pieces drop here\n(box / bin)', fontsize=5.5)
    dim(ax, (-135, -100 + 2), (-8, -100 + 2), '127', (0, -9)); dim(ax, (-8, -100 + 2), (150, -100 + 2), '158', (0, -9))
    dim(ax, (-20, -95), (-20, -65), '30', (-6, -2)); dim(ax, (155, -95), (155, 0), '95 to net line', (0, 50)); dim(ax, (-140, -95), (-140, 180), '275', (-7, 0))
    notes(fig, 0.07, 0.30, [
        'Coordinates: the main plate\'s BACK face is 127 mm from the entry-side edge of the board; its left end is 30 mm from the board edge.',
        '1. Stand the main plate on the board, back face on the line. 3 L-brackets on the FRONT (knife) side: wood screws into plate and board.',
        '2. Push the feed frame against the plate\'s back face, net channel lined up with the window. 2 x M4 x 20 flat heads from the front',
        '    of the plate into the frame (holes on the template), then 4 wood screws (4 x 10-12 mm) through the frame\'s counterbored holes.',
        '3. The motor bolts only to the plate - keep the gearbox >= 5 mm away from the stepper.',
        '4. Cut pieces fall in front of the knife: put a small box there.'], fs=7)
    pdf.savefig(fig); plt.close(fig)
print('ok')
