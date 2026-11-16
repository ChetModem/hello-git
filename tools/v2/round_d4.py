import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
from shapely.geometry import box, Polygon, Point, LineString
G.GAP = G.LINE
Z = G.safe_zone(); place = G.place
def fit(build, lo=0.4, hi=1.6, weight=290.0):
    for s_ in np.arange(hi, lo, -0.01):
        g = build(s_)
        if g is not None and Z.contains(g) and g.area <= weight: return g
def centred(g): b = g.bounds; return place(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
def holes(g): return sum(len(p.interiors) for p in G.pieces(g))

SH_RAISE = 0.45
def figure_over_fan(s_, hand_y=1.6, spread_k=1.0, crown=False, arm_t=2.4):
    """A figure behind a fan of three cards (centre hexagons): head and shoulders above the fan, the cards in front
    of its body, arms spread out with the hands just above the outer cards."""
    w, h = 10.0 * s_, 14.0 * s_
    cards = C.fanned_cards([None] * 3, w=w, h=h, spread=16.0, dx=6.2 * s_ + 1.2)[C.WHITE]
    cb = cards.bounds; cx = (cb[0] + cb[2]) / 2; top = cb[3]
    rx, ry = w * 0.62, w * 0.52
    sh_y = top + ry * SH_RAISE
    shoulders = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=48), rx, ry), cx, sh_y)
    head = Point(cx, sh_y + ry + G.GAP + w * 0.30).buffer(w * 0.34, quad_segs=48)
    span = (cb[2] - cb[0]) * 0.5 * spread_k
    arms = []
    for sd in (-1, 1):
        a0 = (cx + sd * rx * 0.70, sh_y + ry * 0.55)
        elbow = (cx + sd * (rx + (span - rx) * 0.55), sh_y + ry * 0.75)
        hand = (cx + sd * (span - arm_t * 0.4), top + hand_y * s_ + arm_t * 0.5)
        arms.append(LineString([a0, elbow, hand]).buffer(arm_t / 2, cap_style=1, join_style=1))
        arms.append(Point(hand).buffer(arm_t * 0.68, quad_segs=24))
    fig = unary_union([shoulders] + arms)
    fig = fig.difference(cards.buffer(G.GAP, join_style=1)).difference(head.buffer(G.GAP))
    parts = [cards, fig, head]
    if crown:
        cr = G.crown4(w * 0.7, 0.9); crb = cr.bounds; hb = head.bounds
        parts.append(place(cr, cx - (crb[0] + crb[2]) / 2, hb[3] - (crb[3] - crb[1]) * 0.15 - crb[1]).difference(head.buffer(G.GAP)) if False else place(cr, cx - (crb[0] + crb[2]) / 2, hb[3] + G.GAP - crb[1]))
    g = unary_union([p for p in G.pieces(unary_union(parts)) if p.area > 2.0])
    return centred(G.soften(g, 0.3))
opts = [fit(lambda s_: figure_over_fan(s_)),                          # hands just above the outer cards
        fit(lambda s_: figure_over_fan(s_, hand_y=0.4, spread_k=0.9)),  # hands lower and closer, over the cards
        fit(lambda s_: figure_over_fan(s_, hand_y=4.0, spread_k=1.12)), # arms wider, hands lifted: presiding
        ]
r3 = pickle.load(open('round_d3.pkl', 'rb'))['mono'][0]
pickle.dump(opts, open('round_d4.pkl', 'wb'))
def dc(g, corner=7): return {C.WHITE: g, corner: C.corners(corner)}
rows = [[card_img(dc(r3))] + [card_img(dc(g)) for g in opts]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('round_d4.png'); print(out.size)
for g in opts:
    if g is None: print('NONE'); continue
    b = g.bounds; print(f'{b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} ink {g.area:4.0f} closest {G.closest(g):.2f} smallest {min(p.area for p in G.pieces(g)):5.1f} hexagons {holes(g)}')
