import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
G.GAP = G.LINE
Z = G.safe_zone()
def tc(f): return {**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}
def dc(g, corner=7): return {C.WHITE: g, corner: C.corners(corner)}
lr = [G.road_with_wheel(s) for s in ('on', 'end', 'straight')]
def fit(fn):
    for k in np.arange(1.3, 0.5, -0.01):
        g = fn(k)
        if Z.contains(g) and g.area <= 300: return g
rb2 = fit(G.road_two_tools)
rows = [[card_img(C.build('Longest Road')[0])] + [card_img(tc(C.table_layout(C.WHITE, g)[0])) for g in lr],
        [card_img(C.build('Road Building')[0]), card_img(dc(rb2))]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('round_d5.png'); print(out.size)
pickle.dump(dict(lr=lr, rb2=rb2), open('round_d5.pkl', 'wb'))
for g in lr + [rb2]:
    b = g.bounds; print(f'{b[2]-b[0]:5.1f}x{b[3]-b[1]:5.1f} ink {g.area:4.0f} closest {G.closest(g):.2f} smallest {min(p.area for p in G.pieces(g)):5.1f}')
