import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
Z = G.safe_zone()
r5 = pickle.load(open('set_r5.pkl', 'rb'))['set']
def card(slot, icon): return {slot: unary_union([icon, C.corners(slot)])}
def at_bottom(g, B): b = g.bounds; return affinity.translate(g, -(b[0] + b[2]) / 2, B - b[1])
def ok(g): return Z.contains(g) and G.closest(g) >= 0.75
brick = G.centre(G.brick2()); BW = brick.bounds[1]                 # wide icons share the brick's bottom edge
pine, sheep, B = r5['pine'], r5['sheep'], r5['pine'].bounds[1]
wheat = next(g for g in (at_bottom(G.wheat_angular3(k, w=1.85), B) for k in np.arange(1.6, 0.5, -0.01)) if ok(g) and G.closest(g) >= 0.8)
def ore_fit(fn):
    for k in np.arange(1.6, 0.5, -0.01):
        g = at_bottom(fn(k), BW)
        if ok(g) and g.area <= 272: return g
ore_new, ore_old = ore_fit(G.ore_rocks5), ore_fit(G.ore_rocks6)
rows = [[card(3, brick), card(4, pine), card(2, sheep), card(5, wheat), card(6, ore_new)],
        [card(3, r5['brick']), card(3, brick), card(5, r5['wheat']), card(5, wheat)],
        [card(6, ore_old), card(6, ore_new)]]
gap = 24; W = 5 * (CW + gap) + gap; H = 3 * (CH + gap * 2) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for f in r: out.paste(card_img(f), (x, y)); x += CW + gap
    y += CH + gap * 2
out.save('round6.png')
pickle.dump({'set': {'brick': brick, 'pine': pine, 'sheep': sheep, 'wheat': wheat, 'ore': ore_new}, 'ore_old': ore_old}, open('set_r6.pkl', 'wb'))
for n, g in (('brick', brick), ('wheat', wheat), ('ore new', ore_new), ('ore old', ore_old)):
    b = g.bounds; p = G.pieces(g)
    w = 0.6; r = g.buffer(-w/2, join_style=2, mitre_limit=10).buffer(w/2, join_style=2, mitre_limit=10)
    print(f'{n:8s} {b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} top {b[3]:+5.1f} bottom {b[1]:+5.1f} ink {g.area:4.0f} closest {G.closest(g):.2f} zone {Z.contains(g)} smallest {min(q.area for q in p):.1f} thin {g.difference(r).area:.2f}')
wb = wheat.bounds; ear_low = min(q.bounds[1] for q in G.pieces(wheat) if q.bounds[3] - q.bounds[1] < 8 and q.bounds[1] > wb[1] + 1)
print('stalk visible length r5 %.1f -> now %.1f' % (min(q.bounds[1] for q in G.pieces(r5['wheat']) if q.bounds[1] > r5['wheat'].bounds[1] + 1) - r5['wheat'].bounds[1], ear_low - wb[1]))
