import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
G.GAP = G.LINE
def tc(f): return {**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}
DIP = {2: dict(up=-0.0, lo=0.5, lo_pre=0.55, up_pre=0.0)}
roads = [G.longest_road10(DIP)] + [G.longest_road11(DIP, nudge={(2, 1, 0): d}) for d in (0.15, 0.2, 0.25)]
pickle.dump(roads, open('round_d11.pkl', 'wb'))
n = len(roads); gap = 24; W = n * (CW + gap) + gap; H = CH + 2 * gap
cards = [card_img(tc(C.table_layout(C.WHITE, g)[0])) for g in roads]
zs = [c.crop((40, 250, CW - 40, 400)).resize(((CW - 80) * 2, 300)) for c in cards]
out = Image.new('RGB', (max(W, n * (zs[0].width + gap) + gap), H + 300 + 2 * gap), 'white')
for i, c in enumerate(cards): out.paste(c, (gap + i * (CW + gap), gap))
for i, z in enumerate(zs): out.paste(z, (gap + i * (z.width + gap), H + gap))
out.save('round_d11.png'); print(out.size)
for g in roads:
    P = G.pieces(g); a = sorted(p.area for p in P)
    print(f'ink {g.area:4.0f} stones {len(P)} smallest {a[0]:5.1f} largest {a[-1]:5.1f} closest {G.closest(g):.2f}')
