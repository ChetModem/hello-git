import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
G.GAP = G.LINE
def tc(f): return {**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}
roads = [G.longest_road7(seed=4), G.longest_road8(seed=4), G.longest_road8(seed=4, bend_shift=0.65), G.longest_road8(seed=8), G.longest_road8(seed=12)]
pickle.dump(roads, open('round_d8.pkl', 'wb'))
gap = 24; W = 5 * (CW + gap) + gap; H = CH + 2 * gap
out = Image.new('RGB', (W, H), 'white')
for i, g in enumerate(roads): out.paste(card_img(tc(C.table_layout(C.WHITE, g)[0])), (gap + i * (CW + gap), gap))
out.save('round_d8.png')
z = out.crop((0, 250, W, 410)); z = z.resize((z.width, z.height)); 
big = Image.new('RGB', (W, H + z.height * 2 + gap), 'white'); big.paste(out, (0, 0)); big.paste(z.resize((W, z.height * 2)), (0, H)); big.save('round_d8.png')
for g in roads:
    P = G.pieces(g); a = sorted(p.area for p in P)
    print(f'ink {g.area:4.0f} stones {len(P)} smallest {a[0]:5.1f} largest {a[-1]:5.1f} closest {G.closest(g):.2f}')
