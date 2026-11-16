"""Building Costs with the set's own player pieces (silhouettes from the printed pieces) instead of the original Catan shapes."""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
import design_v1 as V1
import numpy as np
G.GAP = G.LINE
O = pickle.load(open('../pieces/silhouettes.pkl', 'rb'))
def clean(g, k):
    """scale to card size, then drop anything thinner than the line weight and round the tips like every icon"""
    b = g.bounds; g = affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
    g = affinity.scale(g, k, k, origin=(0, 0)).simplify(0.12)
    g = g.buffer(-0.45, join_style=1).buffer(0.45, join_style=1)       # removes spikes and slivers under 0.9 mm
    g = g.buffer(0.35, join_style=1).buffer(-0.35, join_style=1)       # closes notches under 0.7 mm
    return G.soften(max(G.pieces(g), key=lambda p: p.area), 0.3)
SET_H, CITY_H = 8.2, 10.0
K = 9.6 / 27.1                                                          # one true scale for all three: city 9.6 mm tall
own = {'road': clean(O['road']['top'], K), 'settlement': clean(O['settlement']['front'], K), 'city': clean(O['city']['front'], K),
       'city_side': clean(O['city']['side'], K)}
def building_costs_with(pieces, right_align=True, gap_to_hex=1.6):
    rows = [('road', ['brick', 'wood']), ('settlement', ['brick', 'wood', 'wheat', 'sheep']),
            ('city', ['ore', 'ore', 'ore', 'wheat', 'wheat']), ('dev', ['ore', 'wheat', 'sheep'])]
    slot = {'brick': C.BRICK, 'wood': C.WOOD, 'wheat': C.WHEAT, 'sheep': C.WHITE, 'ore': C.ORE}
    out = {}
    for i, (p, res) in enumerate(rows):
        y = 21.0 - i * 14.0
        g = pieces[p]; b = g.bounds
        hx0 = -13.0
        if right_align: g = G.place(g, hx0 - gap_to_hex - b[2], y - (b[1] + b[3]) / 2)
        else: g = G.place(g, -18.6 - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2)
        out = C.merge(out, {C.WHITE: g})
        x = hx0
        for r in res:
            out = C.merge(out, {slot[r]: G.place(V1.hexagon(0, 0, 6.5).buffer(0.25, join_style=1).buffer(-0.25, join_style=1), x + 3.25, y)}); x += 7.5
    return out
cur = C.building_costs()[0]
old_pieces = {'road': affinity.rotate(G.road_piece(), 30, origin=(0, 0)), 'settlement': affinity.scale(V1.p_settlement(), 1.25, 1.25, origin=(0, 0)),
              'city': affinity.scale(V1.p_city(), 1.25, 1.25, origin=(0, 0)), 'dev': G.card_solid(6.0, 8.4)}
opts = [cur,
        building_costs_with(old_pieces),                                                            # current pieces, right-aligned (review item 4)
        building_costs_with({**own, 'dev': G.card_solid(6.0, 8.4)}),                               # your pieces, front view
        building_costs_with({'road': own['road'], 'settlement': G.own_settlement2(SET_H), 'city': G.own_city2(CITY_H), 'dev': G.card_solid(6.0, 8.4)})]   # your pieces, drawn flat
pickle.dump(dict(own=own, opts=opts), open('round_bc.pkl', 'wb'))
gap = 24; W = 4 * (CW + gap) + gap; H = CH + 2 * gap
out = Image.new('RGB', (W, H), 'white')
for i, f in enumerate(opts): out.paste(card_img(f), (gap + i * (CW + gap), gap))
# 3x close-up of the piece column of the two new options
zs = [card_img(f).crop((0, 60, CW // 2, CH - 60)).resize((CW, (CH - 120) * 2)) for f in opts[1:]]
big = Image.new('RGB', (W, H + zs[0].height + gap), 'white'); big.paste(out, (0, 0))
for i, z in enumerate(zs): big.paste(z, (gap + i * (CW + gap), H))
big.save('round_bc.png'); print(big.size)
for n, g in own.items():
    b = g.bounds; print(f'{n:10s} {b[2]-b[0]:4.1f} x {b[3]-b[1]:4.1f} mm  area {g.area:5.1f}')
for f in opts:
    g = unary_union(list(f.values())); print('closest %.2f' % G.closest(g), 'smallest %.1f' % min(p.area for p in G.pieces(g)))
