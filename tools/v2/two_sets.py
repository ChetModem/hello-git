import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
V1R = pickle.load(open('../review/cards.pkl', 'rb'))
CORN = unary_union([G.Point(x, y).buffer(4.6) for x in (-20, 20) for y in (-32, 32)])
def icon_of(n): return G.centre(unary_union([v for k, v in V1R[n]['face'].items() if k != 1]).difference(CORN))
icons = {'Brick': icon_of('Brick'), 'Pine': G.to_weight(G.pine_tree), 'Log': G.to_weight(G.log_side), 'Sheep': icon_of('Sheep'),
         'Wheat': G.wheat_ear_final(), 'Ore': G.centre(G.fit_zone(G.ore_rocks())[0])}
slot = {'Brick': 3, 'Pine': 4, 'Log': 4, 'Sheep': 2, 'Wheat': 5, 'Ore': 6}
print(f"{'icon':6s} {'w x h':>12s} {'ink':>5s} {'fill of its box':>15s} {'weight centre (from card centre)':>34s}")
for n, g in icons.items():
    b = g.bounds; c = g.centroid
    print(f"{n:6s} {b[2]-b[0]:5.1f} x {b[3]-b[1]:4.1f} {g.area:5.0f} {100*g.area/((b[2]-b[0])*(b[3]-b[1])):13.0f} %   ({c.x:+5.1f}, {c.y:+5.1f}) mm")
rows = [['Brick', 'Pine', 'Sheep', 'Wheat', 'Ore'], ['Brick', 'Log', 'Sheep', 'Wheat', 'Ore']]
gap = 24; W = 5 * (CW + gap) + gap; H = 2 * (CH + gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for n in r:
        out.paste(card_img({slot[n]: unary_union([icons[n], C.corners(slot[n])])}), (x, y)); x += CW + gap
    y += CH + gap
out.save('two_sets.png')
# close-up of the ore icon
S = 30; g = icons['Ore']; b = g.bounds
img = Image.new('RGB', (int((b[2]-b[0])*S)+40, int((b[3]-b[1])*S)+40), (25, 25, 25)); d = ImageDraw.Draw(img)
for p in G.pieces(g):
    d.polygon([(20+(a-b[0])*S, 20+(b[3]-bb)*S) for a, bb in p.exterior.coords], fill=(170,170,175))
    for h in p.interiors: d.polygon([(20+(a-b[0])*S, 20+(b[3]-bb)*S) for a, bb in h.coords], fill=(25,25,25))
img.save('ore_zoom.png')
