import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import numpy as np
Z = G.safe_zone(); BW = pickle.load(open('set_r6.pkl', 'rb'))['set']['brick'].bounds[1]
def card(slot, icon): return {slot: unary_union([icon, C.corners(slot)])}
def at_bottom(g, B): b = g.bounds; return affinity.translate(g, -(b[0] + b[2]) / 2, B - b[1])
def fit(st):
    for k in np.arange(1.6, 0.5, -0.01):
        g = at_bottom(G.ore_rocks8(k, st), BW)
        if Z.contains(g) and G.closest(g) >= 0.78 and g.area <= 272: return g
styles = ('orig', 'blunt', 'veer_a', 'veer_b'); ores = {s: fit(s) for s in styles}
gap = 24; out = Image.new('RGB', (4 * (CW + gap) + gap, CH + 2 * gap + CH // 2 + gap), 'white')
for i, s in enumerate(styles):
    im = card_img(card(6, ores[s])); out.paste(im, (gap + i * (CW + gap), gap))
    z = im.crop((CW // 2 - CW // 4 - 20, CH // 2 - CH // 8, CW // 2 + CW // 4 - 20, CH // 2 + CH // 8)).resize((CW, CH // 2))  # zoom on the rocks
    out.paste(z, (gap + i * (CW + gap), CH + 2 * gap))
out.save('round12.png'); pickle.dump(ores, open('set_r12.pkl', 'wb'))
for s, g in ores.items():
    w = 0.6; r = g.buffer(-w/2, join_style=2, mitre_limit=10).buffer(w/2, join_style=2, mitre_limit=10)
    print(f'{s:6s} ink {g.area:4.0f} closest {G.closest(g):.2f} faces {sorted(round(p.area) for p in G.pieces(g))} thin {g.difference(r).area:.2f}')
