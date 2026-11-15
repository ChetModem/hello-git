import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
opts = [G.log_up_a, G.log_up_b, G.log_up_c, G.log_up_d, G.log_pair, None]
ear = G.wheat_ear_final()
gap = 24; cols = 3; rows = 2
out = Image.new('RGB', (cols * (CW + gap) + gap, rows * (CH + gap) + gap), 'white')
for i, fn in enumerate(opts):
    if fn is None:      # last slot: the wheat card, for comparing alignment
        f = {5: unary_union([ear, C.corners(5)])}
    else:
        g = G.to_weight(fn, 300.0)
        if g is None: print(i + 1, 'did not fit'); continue
        w = 0.6; r = g.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
        blk = G.box(*g.bounds).buffer(1).difference(g); r2 = blk.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
        print(f'{i+1}: ink {g.area:4.0f} size {g.bounds[2]-g.bounds[0]:.1f} x {g.bounds[3]-g.bounds[1]:.1f} closest {G.closest(g):.2f} thin colour {g.difference(r).area:.2f} thin black {[round(p.area,2) for p in G.pieces(blk.difference(r2)) if p.area>0.12][:4]}')
        f = {4: unary_union([G.centre(g), C.corners(4)])}
    out.paste(card_img(f), (gap + (i % cols) * (CW + gap), gap + (i // cols) * (CH + gap)))
print('wheat ear size %.1f x %.1f' % (ear.bounds[2] - ear.bounds[0], ear.bounds[3] - ear.bounds[1]))
out.save('log_grid.png'); print(out.size)
