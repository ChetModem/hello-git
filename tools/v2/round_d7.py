import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
G.GAP = G.LINE
def tc(f): return {**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}
picked = G.longest_road6(4, 10.6, 20, seed=3)
evened = [G.longest_road7(seed=sd) for sd in (3, 4, 8, 12)]
pickle.dump(dict(picked=picked, evened=evened), open('round_d7.pkl', 'wb'))
rows = [[card_img(tc(C.table_layout(C.WHITE, g)[0])) for g in [picked] + evened]]
gap = 24; W = 5 * (CW + gap) + gap; H = CH + 2 * gap + gap
out = Image.new('RGB', (W, H), 'white')
for i, im in enumerate(rows[0]): out.paste(im, (gap + i * (CW + gap), gap))
out.save('round_d7.png')
z = out.crop((0, int(CH * 0.28), W, int(CH * 0.52))); z.save('round_d7_zoom.png')
for g in [picked] + evened:
    P = G.pieces(g); a = sorted(p.area for p in P)
    print(f'ink {g.area:4.0f} stones {len(P)} smallest {a[0]:5.1f} largest {a[-1]:5.1f} spread {a[-1]/a[0]:4.1f}x closest {G.closest(g):.2f}')
