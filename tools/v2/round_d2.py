import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
from shapely.geometry import box, Polygon
G.GAP = G.LINE
Z = G.safe_zone(); place = G.place
WEIGHT = 290.0
def fit(build, lo=0.4, hi=1.6, weight=WEIGHT):
    """largest scale s (geometry only, gaps fixed) that fits inside the ring and is no heavier than the set's icons"""
    for s_ in np.arange(hi, lo, -0.01):
        g = build(s_)
        if g is not None and Z.contains(g) and g.area <= weight: return g
def centred(g): b = g.bounds; return place(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
def holes(g): return sum(len(p.interiors) for p in G.pieces(g))

# ---------------- Monopoly
def mono_fan(s_, spread, dx, hr_crown, overlap, corner_hex=True, gap_above=None):
    w, h = 11.0 * s_, 15.4 * s_
    kw = dict(w=w, h=h, spread=spread, dx=dx * s_)
    if corner_hex: kw.update(hx0=-w * 0.22, hy=h * 0.26, hr=0.30)
    plain = C.fanned_cards([None] * 3, **{k: v for k, v in kw.items() if k in ('w', 'h', 'spread', 'dx')})[C.WHITE]; cb = plain.bounds
    cr = G.crown4(w * 1.25, hr_crown); crb = cr.bounds
    if gap_above is None: y = cb[3] - overlap * (crb[3] - crb[1]) - crb[1]
    else: y = cb[3] + gap_above - crb[1]
    cr = place(cr, (cb[0] + cb[2]) / 2 - (crb[0] + crb[2]) / 2, y)
    cards = C.fanned_cards([None] * 3, blocker=cr.convex_hull, **kw)[C.WHITE]
    cards = unary_union([p for p in G.pieces(cards) if p.area > 2.0])
    return centred(unary_union([cards, cr]))
def mono_stack(s_):
    """crown on a squared-up deck: three cards stacked with their edges showing, front card with its hexagon"""
    w, h = 12.0 * s_, 16.0 * s_; out = Polygon(); prev = Polygon()
    cardsh = [place(G.rr(-w / 2, -h / 2, w / 2, h / 2, 0.9), i * 1.9, i * 1.9) for i in range(3)]
    for i, c in enumerate(cardsh):
        front = unary_union(cardsh[:i]) if i else Polygon()
        out = unary_union([out, c.difference(front.buffer(G.GAP, join_style=1)) if i else c.difference(G.hexagon(0, -h * 0.12, w * 0.4))])
    cb = out.bounds; cr = G.crown4(w * 1.05, 0.9); crb = cr.bounds
    cr = place(cr, -(crb[0] + crb[2]) / 2, h / 2 - 0.35 * (crb[3] - crb[1]) - crb[1])
    out = out.difference(cr.convex_hull.buffer(G.GAP, join_style=1))
    return centred(unary_union([p for p in G.pieces(out) if p.area > 2] + [cr]))
def mono_jewel(s_): return centred(G.crown4(26.0 * s_, 0.85, hex_jewel=True))
mono = [C.build('Monopoly')[0][C.WHITE],
        fit(lambda s_: mono_fan(s_, 20.0, 5.2, 0.9, 0.22)),                         # refined: wider fan, taller crown, corner hexagons
        fit(lambda s_: mono_fan(s_, 20.0, 5.2, 0.9, 0, gap_above=1.4)),               # refined: crown above the fan, cards whole
        fit(mono_stack),                                                             # redesign: crown on a squared deck
        fit(mono_jewel)]                                                              # redesign: crown with a hexagon jewel
# ---------------- Year of Plenty
def yop_fan(s_, corner_hex, spread=14.0, dx=7.4):
    w, h = 11.0 * s_, 15.4 * s_
    kw = dict(w=w, h=h, spread=spread, dx=dx * s_)
    if corner_hex: kw.update(hx0=-w * 0.22, hy=h * 0.26, hr=0.30)
    return centred(C.fanned_cards([None] * 2, **kw)[C.WHITE])
def plus(w):
    a, t = w * 0.30, w * 0.13
    return unary_union([box(-a, -t, a, t), box(-t, -a, t, a)])
def yop_plus(s_): return centred(C.fanned_cards([None] * 2, w=11.0 * s_, h=15.4 * s_, spread=14.0, dx=7.4 * s_, mark=plus)[C.WHITE])
def yop_bank(s_):
    """two cards lifting out of a solid hexagon (the bank)"""
    w, h = 9.0 * s_, 12.6 * s_; hx = G.hexagon(0, -6.0 * s_, 9.0 * s_)
    cards = C.fanned_cards([None] * 2, w=w, h=h, spread=18.0, dx=6.4 * s_)[C.WHITE]
    cards = place(cards, 0, 4.0 * s_)
    hx = hx.difference(cards.convex_hull.buffer(G.GAP, join_style=1)) if False else hx
    cards = cards.difference(hx.buffer(G.GAP, join_style=1))
    return centred(unary_union([p for p in G.pieces(cards) if p.area > 2] + [hx]))
yop = [C.build('Year of Plenty')[0][C.WHITE], fit(lambda s_: yop_fan(s_, True)), fit(yop_plus)]
# ---------------- Longest Road (with the Largest Army card for comparison) and Road Building
LRo = [G.longest_road5(4, 10.6, 30), G.longest_road5(3, 13.0, 25), G.longest_road5(4, 10.6, 20), G.longest_road5(6, 7.4, 30)]
lr_cards = [C.table_layout(C.WHITE, g)[0] for g in LRo]
rb = [C.build('Road Building')[0][C.WHITE], fit(lambda k: G.road_hammer5(k), hi=1.2)]
sheep4 = pickle.load(open('sheep_d1.pkl', 'rb'))[3]
pickle.dump(dict(mono=mono, yop=yop, lr=LRo, rb=rb), open('round_d2.pkl', 'wb'))
GR = 7
def dc(g, corner=GR): return {C.WHITE: g, corner: C.corners(corner)}
rows = [[card_img(dc(g)) for g in mono],
        [card_img(dc(g)) for g in yop],
        [card_img({**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}) for f in lr_cards] + [card_img(C.build('Largest Army')[0])],
        [card_img(dc(g)) for g in rb]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('round_d2.png'); print(out.size)
for n, gs in (('mono', mono), ('yop', yop), ('rb', rb)):
    for g in gs:
        if g is None: print(n, 'NONE'); continue
        b = g.bounds; print(f'{n:5s} {b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} ink {g.area:4.0f} closest {G.closest(g):.2f} smallest {min(p.area for p in G.pieces(g)):5.1f} hexagons/holes {holes(g)}')
for g in LRo: b = g.bounds; print(f'lr    {b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} ink {g.area:4.0f} smallest {min(p.area for p in G.pieces(g)):5.1f}')
