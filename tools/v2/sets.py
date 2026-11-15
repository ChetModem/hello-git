import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
V1R = pickle.load(open('../review/cards.pkl', 'rb'))
SL = {'Brick': 3, 'Wood': 4, 'Sheep': 2, 'Wheat': 5, 'Ore': 6}
def face(slot, icon): return {slot: unary_union([icon, C.corners(slot)])}
v1 = {n: {k: v for k, v in V1R[n]['face'].items() if k != 1} for n in SL}
ear = G.wheat_ear_final()
sets = [
 ('Set 1 - current (v1): mixed styles', v1),
 ('Set 2 - flat, straight-on view', {'Brick': v1['Brick'], 'Wood': face(4, G.at_final(G.log_ends)[0]), 'Sheep': v1['Sheep'],
                                     'Wheat': face(5, ear), 'Ore': face(6, G.fit_zone(G.ore_rocks())[0])}),
 ('Set 3 - 3D, three-quarter view (built like the wood)', {'Brick': face(3, G.at_final(G.bricks3d)[0]), 'Wood': v1['Wood'],
                                     'Sheep': face(2, G.at_final(G.wool_ball2)[0]), 'Wheat': face(5, ear), 'Ore': face(6, G.at_final(G.ingots3d)[0])}),
]
CORN = unary_union([G.Point(x, y).buffer(4.6) for x in (-20, 20) for y in (-32, 32)])
W = 5 * (CW + 20) + 20; H = len(sets) * (CH + 90) + 20
out = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(out); y = 10
for title, s in sets:
    dr.text((10, y), title, fill='black', font=F); y += 34; x = 10; inks = []
    for n in SL:
        f = s[n]; out.paste(card_img(f), (x, y + 26)); dr.text((x, y), n, fill=(90, 90, 90), font=F)
        ink = unary_union(list(f.values())).difference(CORN); inks.append(f'{n} {ink.area:.0f}')
        # printability of this icon
        g = ink; w = 0.6; r = g.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
        ps = G.pieces(g); cl = min([a.distance(b) for i, a in enumerate(ps) for b in ps[i + 1:]] or [9])
        if g.difference(r).area > 0.12 or cl < 0.6: print('  check', title[:5], n, 'thin', round(g.difference(r).area, 2), 'closest', round(cl, 2))
        x += CW + 20
    print(title, '| ink (mm2):', ', '.join(inks))
    y += CH + 56
out.save('resource_sets.png'); print(out.size)
