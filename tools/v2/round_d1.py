import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
G.GAP = G.LINE
OLD = pickle.load(open('v2_cards_before_D1.pkl', 'rb')); NEW = pickle.load(open('v2_cards.pkl', 'rb'))
Z = G.safe_zone(); B = C.TALL_LINE
def sheep_opt(le, fe):
    for s in np.arange(1.2, 0.5, -0.01):
        g = G.sheep4(s, le, fe); b = g.bounds; g = affinity.translate(g, -(b[0] + b[2]) / 2, B - b[1])
        if Z.contains(g) and G.closest(g) >= 0.78 and g.area <= 285 and len(G.pieces(g)) == 4: return g
sheep = [C.RES_ICONS['sheep'], sheep_opt(1.2, 0), sheep_opt(2.4, 0), sheep_opt(1.0, 1.0)]
pickle.dump(sheep, open('sheep_d1.pkl', 'wb'))
for g in sheep: b = g.bounds; print(f'sheep ink {g.area:4.0f} top {b[3]:+5.1f} bottom {b[1]:+5.1f} middle {(b[1]+b[3])/2:+5.1f} closest {G.closest(g):.2f}')
dev = ('Knight', 'Victory Point', 'Road Building', 'Year of Plenty', 'Monopoly'); tab = ('Building Costs', 'Longest Road', 'Largest Army')
rows = [[card_img(OLD[n][0]) for n in dev], [card_img(NEW[n][0]) for n in dev],
        [card_img(OLD[n][0]) for n in tab[1:]] + [card_img(NEW[n][0]) for n in tab],
        [card_img({2: unary_union([g, C.corners(2)])}) for g in sheep]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('round_d1.png'); print(out.size)
