import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
COLS[10] = (150, 165, 85)                               # lighter olive / sage, for the filament comparison only
Z = G.safe_zone()
old = pickle.load(open('set_r3.pkl', 'rb'))
def card(slot, icon, corner=None): return {slot: unary_union([icon, C.corners(slot)])} if corner is None else {slot: icon, corner: C.corners(corner)}
def at_bottom(g, B): b = g.bounds; return affinity.translate(g, -(b[0] + b[2]) / 2, B - b[1])
def largest(fn, lo=0.5, hi=1.6, place=lambda g: g):
    for k in np.arange(hi, lo, -0.01):
        g = place(fn(k))
        if Z.contains(g) and G.closest(g) >= 0.75: return g
brick = old['brick'][1]
pine = G.optical(G.to_weight(G.pine_tree2)); B = pine.bounds[1]
def weighted(fn, target):
    for s in np.arange(1.5, 0.5, -0.01):
        g = at_bottom(fn(s), B)
        if Z.contains(g) and G.closest(g) >= 0.75 and g.area <= target and len(G.pieces(g)) == 4: return g
sheep = {st: weighted(lambda s, st=st: G.sheep3(s, st), 285) for st in 'a'}
wheat = largest(G.wheat_angular2, place=lambda g: at_bottom(g, B))
def ore_place(g):
    g = G.centre(g); o = G.optical(g); return affinity.translate(g, 0, (o.bounds[1] - g.bounds[1]) / 2)
ore = next(g for g in (ore_place(G.ore_rocks5(k)) for k in np.arange(1.6, 0.5, -0.01)) if Z.contains(g) and G.closest(g) >= 0.75 and g.area <= 272)
new = {'brick': brick, 'pine': pine, 'sheep': sheep['a'], 'wheat': wheat, 'ore': ore}
o = lambda n: G.optical(old[n][1])
r4 = pickle.load(open('set_r4.pkl', 'rb'))['set']
rows = [[card(3, brick), card(4, r4['pine']), card(2, r4['sheep']), card(5, r4['wheat']), card(6, r4['ore'])],
        [card(3, brick), card(4, pine), card(2, sheep['a']), card(5, wheat), card(6, ore)],
        [card(2, r4['sheep']), card(2, sheep['a']), card(6, o('ore')), card(6, r4['ore']), card(6, ore)]]
gap = 24; W = 5 * (CW + gap) + gap; H = 3 * (CH + gap * 2) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for f in r: out.paste(card_img(f), (x, y)); x += CW + gap
    y += CH + gap * 2
out.save('round5.png')
pickle.dump({'set': new, 'sheep': sheep}, open('set_r5.pkl', 'wb'))
for n, g in list(new.items()):
    b = g.bounds
    print(f'{n:8s} {b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} top {b[3]:+5.1f} bottom {b[1]:+5.1f} ink {g.area:4.0f} closest {G.closest(g):.2f} in zone {Z.contains(g)} pieces {len(G.pieces(g))} smallest {min(p.area for p in G.pieces(g)):.1f}')
