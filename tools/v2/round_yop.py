import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
G.GAP = G.LINE
ms = C.monopoly_scale(); wb = C.year_of_plenty()[0][C.WHITE]
import numpy as np
sw = next(s_ for s_ in np.arange(1.6, 0.4, -0.01) if C.ZONE.contains(C.year_of_plenty_at(s_)) and C.year_of_plenty_at(s_).area <= C.YOP_WEIGHT)
mid = (ms + sw) / 2
opts = [('Monopoly', C.monopoly()[0][C.WHITE], ms), ('YoP by weight', C.year_of_plenty_at(sw), sw), ('YoP in between', C.year_of_plenty_at(mid), mid), ('YoP matching Monopoly', C.year_of_plenty_at(ms), ms)]
def dc(g): return {C.WHITE: g, C.GREEN: C.corners(C.GREEN)}
gap = 24; W = 4 * (CW + gap) + gap; H = CH + 2 * gap
out = Image.new('RGB', (W, H), 'white')
for i, (n, g, s_) in enumerate(opts):
    out.paste(card_img(dc(g)), (gap + i * (CW + gap), gap))
    print(f'{n:22s} card {C.CARD_W * s_:4.1f} x {C.CARD_H * s_:4.1f} mm  ink {g.area:4.0f}  hexagons {sum(len(p.interiors) for p in G.pieces(g))}  closest {G.closest(g):.2f}')
out.save('round_yop.png')
