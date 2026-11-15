import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
V1R = pickle.load(open('../review/cards.pkl', 'rb'))
CORN = unary_union([G.Point(x, y).buffer(4.6) for x in (-20, 20) for y in (-32, 32)])
def icon_of(n): return unary_union([v for k, v in V1R[n]['face'].items() if k != 1]).difference(CORN)
def face(slot, icon): return {slot: unary_union([G.centre(icon), C.corners(slot)])}
brick = face(3, icon_of('Brick')); sheep = face(2, icon_of('Sheep'))
ear = face(5, G.wheat_ear_final()); rocks = face(6, G.fit_zone(G.ore_rocks())[0])
woods = [G.to_weight(G.pine_tree), G.to_weight(G.leafy_tree), G.to_weight(G.two_pines), G.to_weight(G.log_side), G.to_weight(G.stacked_logs_side)]
gap = 24; W = 5 * (CW + gap) + gap; H = len(woods) * (CH + gap * 2) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for wd in woods:
    row = [brick, face(4, wd), sheep, ear, rocks]; x = gap
    for f in row: out.paste(card_img(f), (x, y)); x += CW + gap
    g = wd; w = 0.6; r = g.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
    blk = G.box(*g.bounds).buffer(1).difference(g); r2 = blk.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
    print(f'wood: ink {g.area:4.0f}  size {g.bounds[2]-g.bounds[0]:.1f} x {g.bounds[3]-g.bounds[1]:.1f}  closest {G.closest(g):.2f}  thin colour {g.difference(r).area:.2f}  thin black {[round(p.area,2) for p in G.pieces(blk.difference(r2)) if p.area>0.12][:4]}')
    y += CH + gap * 2
for n, f in (('brick', brick), ('sheep', sheep), ('wheat', ear), ('ore', rocks)):
    g = unary_union(list(f.values())).difference(CORN); print(f'{n}: ink {g.area:.0f}, centre ({(g.bounds[0]+g.bounds[2])/2:+.1f},{(g.bounds[1]+g.bounds[3])/2:+.1f})')
out.save('wood_five.png'); print(out.size)
