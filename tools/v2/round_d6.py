import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
G.GAP = G.LINE
Z = G.safe_zone()
def fit(fn, w=290.0):
    for k in np.arange(1.3, 0.5, -0.01):
        g = fn(k)
        if Z.contains(g) and g.area <= w: return g
opts = [fit(lambda k: G.road_tool7(k, 'hammer')), fit(lambda k: G.road_tool7(k, 'shovel')),
        fit(lambda k: G.tools_crossed(k))]
pickle.dump(opts, open('round_d6.pkl', 'wb'))
def dc(g, corner=7): return {C.WHITE: g, corner: C.corners(corner)}
rows = [[card_img(dc(g)) for g in opts]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('round_d6.png'); print(out.size)
for g in opts:
    if g is None: print('NONE'); continue
    b = g.bounds; print(f'{b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} ink {g.area:4.0f} closest {G.closest(g):.2f} smallest {min(p.area for p in G.pieces(g)):5.1f}')
