import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
from shapely.geometry import box, Polygon
G.GAP = G.LINE
Z = G.safe_zone(); place = G.place
def fit(build, lo=0.4, hi=1.6, weight=290.0):
    for s_ in np.arange(hi, lo, -0.01):
        g = build(s_)
        if g is not None and Z.contains(g) and g.area <= weight: return g
def centred(g): b = g.bounds; return place(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
def holes(g): return sum(len(p.interiors) for p in G.pieces(g))
CROWN_W = 1.7
def mono_crown_above(s_, dx=7.4, spread=14.0):
    """crown just above a fan of three cards, every card showing its centre hexagon (like Building Costs' card)"""
    w, h = 11.0 * s_, 15.4 * s_
    cards = C.fanned_cards([None] * 3, w=w, h=h, spread=spread, dx=dx * s_ + 1.2)[C.WHITE]; cb = cards.bounds   # +1.2: gaps do not shrink with the drawing
    cr = G.crown4(w * CROWN_W, 0.9); crb = cr.bounds
    cr = place(cr, (cb[0] + cb[2]) / 2 - (crb[0] + crb[2]) / 2, cb[3] + 1.4 - crb[1])
    return centred(unary_union([cards, cr]))
def mono_fist(s_, crown=False):
    """a fist holding a fan of three cards (the cards you take from everyone), centre hexagons above the grip"""
    w, h = 11.0 * s_, 15.4 * s_
    f = G.fist(w * 1.6); fb = f.bounds
    plain = C.fanned_cards([None] * 3, w=w, h=h, spread=18.0, dx=6.0 * s_ + 1.2)[C.WHITE]; cb = plain.bounds
    f = place(f, (cb[0] + cb[2]) / 2 - (fb[0] + fb[2]) / 2, cb[1] - fb[1] - 0.6 * (fb[3] - fb[1]) + h * 0.12)
    cards = C.fanned_cards([None] * 3, w=w, h=h, spread=18.0, dx=6.0 * s_ + 1.2, hy=h * 0.17, hr=0.40, blocker=f.convex_hull)[C.WHITE]
    cards = unary_union([p for p in G.pieces(cards) if p.area > 2.0])
    return centred(unary_union([cards, f]))
mono = [fit(lambda s_: mono_crown_above(s_)), fit(lambda s_: mono_crown_above(s_, 6.6, 18.0)), fit(lambda s_: mono_fist(s_))]
R = {n: C.build(n)[0] for n in ('Longest Road', 'Largest Army', 'Knight', 'Road Building')}
lr_alt = [C.table_layout(C.WHITE, G.longest_road6(4, 10.6, 20, seed=sd))[0] for sd in (3, 11)]
rb_shovel = None
for k in np.arange(1.2, 0.6, -0.01):
    g = G.road_tool6(k, 'shovel')
    if Z.contains(g): rb_shovel = g; break
def dc(g, corner=7): return {C.WHITE: g, corner: C.corners(corner)}
def tc(f): return {**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}
rows = [[card_img(dc(g)) for g in mono],
        [card_img(R['Longest Road'] if False else C.build('Longest Road')[0])] + [card_img(tc(f)) for f in lr_alt] + [card_img(C.build('Largest Army')[0]), card_img(C.build('Knight')[0])],
        [card_img(C.build('Road Building')[0]), card_img(dc(rb_shovel))]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('round_d3.png'); print(out.size)
pickle.dump(dict(mono=mono, rb_shovel=rb_shovel), open('round_d3.pkl', 'wb'))
for g in mono + [rb_shovel]:
    if g is None: print('NONE'); continue
    b = g.bounds; print(f'{b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} ink {g.area:4.0f} closest {G.closest(g):.2f} smallest {min(p.area for p in G.pieces(g)):5.1f} hexagons {holes(g)}')
for n in ('Longest Road', 'Largest Army'):
    f = C.build(n)[0]; print(n, 'trophy row bottom %.1f' % f[C.ORANGE].difference(C.corners(0).buffer(0.01)).bounds[1], 'picture bottom %.1f' % unary_union([v for k, v in f.items() if k != C.ORANGE]).bounds[1])
