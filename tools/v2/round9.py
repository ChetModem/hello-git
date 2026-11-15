import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
Z = G.safe_zone()
r5 = pickle.load(open('set_r5.pkl', 'rb'))['set']; r6 = pickle.load(open('set_r6.pkl', 'rb'))['set']
def card(slot, icon): return {slot: unary_union([icon, C.corners(slot)])}
def at_bottom(g, B): b = g.bounds; return affinity.translate(g, -(b[0] + b[2]) / 2, B - b[1])
def ok(g, gap=0.75): return Z.contains(g) and G.closest(g) >= gap
B, BW = r6['pine'].bounds[1], r6['brick'].bounds[1]
def wheat_mid(k):     # between r5 and r6: stalk 1.7 mm wide, ~5.8 mm showing
    g = G.wheat_angular3(k, w=1.9, pitch0=3.0, extra=0.9, sw=1.7)
    return g
wheat_m = next(g for g in (at_bottom(wheat_mid(k), B) for k in np.arange(1.6, 0.5, -0.01)) if ok(g, 0.8))
def ore_fit(st):
    for k in np.arange(1.6, 0.5, -0.01):
        g = at_bottom(G.ore_rocks7(k, st), BW)
        if ok(g) and g.area <= 272: return g
ores = {st: ore_fit(st) for st in ('split6', 'offset', 'noleft', 'noright')}
rows = [[card(6, ores['split6']), card(6, ores['offset']), card(6, ores['noleft']), card(6, ores['noright'])]]
gap = 24; W = 5 * (CW + gap) + gap; H = 1 * (CH + gap * 2) + gap
out = Image.new('RGB', (4 * (CW + gap) + gap, H), 'white'); y = gap
for r in rows:
    x = gap
    for f in r: out.paste(card_img(f), (x, y)); x += CW + gap
    y += CH + gap * 2
out.save('round9.png')
pickle.dump({'wheat_mid': wheat_m, 'ores': ores}, open('set_r9.pkl', 'wb'))
def stalk(g):
    b = g.bounds; return min(q.bounds[1] for q in G.pieces(g) if q.bounds[1] > b[1] + 1) - b[1], min(q.bounds[2]-q.bounds[0] for q in G.pieces(g) if q.bounds[1] < b[1] + 0.1)
for n, g in (('wheat r5', r5['wheat']), ('wheat mid', wheat_m), ('wheat r6', r6['wheat'])):
    sl, sw = stalk(g); print(f'{n:9s} ink {g.area:4.0f} stalk showing {sl:.1f} wide {sw:.1f} closest {G.closest(g):.2f} zone {Z.contains(g)}')
for n, g in ores.items():
    w = 0.6; r = g.buffer(-w/2, join_style=2, mitre_limit=10).buffer(w/2, join_style=2, mitre_limit=10)
    print(f'ore {n:6s} ink {g.area:4.0f} closest {G.closest(g):.2f} faces {sorted(round(p.area) for p in G.pieces(g))} thin {g.difference(r).area:.2f}')
