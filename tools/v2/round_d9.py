import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
G.GAP = G.LINE
def tc(f): return {**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}
# middle bend (the dip) = bend 2: (upper row, lower row) joint positions, in stones along the next run
variants = [None, {2: (0.15, 0.55)}, {2: (0.1, 0.7)}, {2: (0.2, 0.45)}]
roads = [G.longest_road8(seed=4)] + [G.longest_road9(v) for v in variants[1:]]
pickle.dump(roads, open('round_d9.pkl', 'wb'))
gap = 24; n = len(roads); W = n * (CW + gap) + gap; H = CH + 2 * gap
out = Image.new('RGB', (W, H), 'white')
for i, g in enumerate(roads): out.paste(card_img(tc(C.table_layout(C.WHITE, g)[0])), (gap + i * (CW + gap), gap))
z = out.crop((0, 260, W, 400))
big = Image.new('RGB', (W, H + 2 * z.height + gap), 'white'); big.paste(out, (0, 0)); big.paste(z.resize((W, z.height)).resize((W * 2 // 2, z.height)), (0, H))
# proper 2x zoom of each road, side by side, same aspect
zs = [card_img(tc(C.table_layout(C.WHITE, g)[0])).crop((40, 250, CW - 40, 400)) for g in roads]
zw = zs[0].width; zh = zs[0].height
zoom = Image.new('RGB', (n * (zw * 2 // 1 // 2) + (n + 1) * gap, zh + 2 * gap), 'white')
for i, zi in enumerate(zs): zoom.paste(zi, (gap + i * (zw + gap), gap))
out2 = Image.new('RGB', (max(W, zoom.width), H + zoom.height), 'white'); out2.paste(out, (0, 0)); out2.paste(zoom, (0, H)); out2.save('round_d9.png')
for g in roads:
    P = G.pieces(g); a = sorted(p.area for p in P)
    print(f'ink {g.area:4.0f} stones {len(P)} smallest {a[0]:5.1f} largest {a[-1]:5.1f} closest {G.closest(g):.2f}')
