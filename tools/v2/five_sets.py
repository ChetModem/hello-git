import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
V1R = pickle.load(open('../review/cards.pkl', 'rb'))
def face(slot, icon): return {slot: unary_union([icon, C.corners(slot)])}
v1 = {n: {k: v for k, v in V1R[n]['face'].items() if k != 1} for n in ('Brick', 'Wood', 'Sheep')}
ear = face(5, G.wheat_ear_final())
rocks = face(6, G.fit_zone(G.ore_rocks())[0]); mountains = face(6, G.fit_zone(G.ore_mountains_plain(1.0))[0])
ingots = face(6, G.at_final(G.ingots3d)[0]); bricks3d = face(3, G.at_final(G.bricks3d)[0])
pine = face(4, G.at_final(G.pine_tree)[0]); logside = face(4, G.at_final(G.log_side)[0])
sets = [
    [v1['Brick'], pine,       v1['Sheep'], ear, rocks],        # 1 flat, pine tree
    [v1['Brick'], v1['Wood'], v1['Sheep'], ear, rocks],        # 2 flat, 3D logs
    [v1['Brick'], logside,    v1['Sheep'], ear, rocks],        # 3 flat, log side-on
    [v1['Brick'], pine,       v1['Sheep'], ear, mountains],    # 4 where it comes from: tree, sheep, wheat, mountains
    [bricks3d,    v1['Wood'], v1['Sheep'], ear, ingots],       # 5 3D materials (brick, logs, ingots) + sheep + wheat
]
CORN = unary_union([G.Point(x, y).buffer(4.6) for x in (-20, 20) for y in (-32, 32)])
gap = 24; W = 5 * (CW + gap) + gap; H = len(sets) * (CH + gap * 2) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for row in sets:
    x = gap
    for f in row:
        out.paste(card_img(f), (x, y)); x += CW + gap
        g = unary_union(list(f.values())).difference(CORN); w = 0.6
        r = g.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
        ps = G.pieces(g); cl = min([a.distance(b) for i, a in enumerate(ps) for b in ps[i + 1:]] or [9])
        if g.difference(r).area > 0.12 or cl < 0.6: print('check: thin', round(g.difference(r).area, 2), 'closest', round(cl, 2))
    y += CH + gap * 2
out.save('five_sets.png'); print(out.size)
