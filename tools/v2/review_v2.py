import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
from shapely.geometry import Point
V1R = pickle.load(open('../review/cards.pkl', 'rb'))
V2R = pickle.load(open('v2_cards.pkl', 'rb'))
CORN = unary_union([Point(x, y).buffer(4.6) for x in (-20, 20) for y in (-32, 32)])
cards = {}
for n in ['Brick', 'Wood', 'Sheep', 'Wheat']:
    d = V1R[n]; cards[n] = ({k: v for k, v in d['face'].items() if k != 1}, d['back'].get(2))
for n in ['Ore', 'Knight', 'Victory Point', 'Road Building', 'Year of Plenty', 'Monopoly', 'Building Costs', 'Longest Road', 'Largest Army']:
    cards[n] = V2R[n]
order = [['Brick', 'Wood', 'Sheep', 'Wheat', 'Ore'], ['Knight', 'Victory Point', 'Road Building', 'Year of Plenty', 'Monopoly'], ['Building Costs', 'Longest Road', 'Largest Army']]
W = 5 * (CW + 20) + 20; H = 4 * (CH + 60) + 60
out = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(out); y = 10
for row in order:
    x = 10
    for n in row:
        dr.text((x, y), n, fill='black', font=F); out.paste(card_img(cards[n][0]), (x, y + 30)); x += CW + 20
    y += CH + 50
dr.text((10, y), 'Backs: resource, development, Building Costs, Longest Road / Largest Army', fill='black', font=F); y += 30; x = 10
def back_img(b):
    img = Image.new('RGB', (CW, CH), (235, 235, 235)); draw(img, V1.CARD, COLS[1]); draw(img, b, COLS[2]); return img
for n in ['Brick', 'Knight', 'Building Costs', 'Longest Road']:
    out.paste(back_img(cards[n][1]), (x, y)); x += CW + 20
out.save('review_v2.png'); print(out.size)
print(f"{'card':16s} {'icon w x h':>13s} {'ink':>5s} {'bbox ctr':>13s} {'ink ctr':>13s} {'over back logo':>15s}")
for n, (face, back) in cards.items():
    ink = unary_union(list(face.values())).buffer(0)
    icon = ink.difference(CORN) if n != 'Building Costs' else ink
    b = icon.bounds; c = icon.centroid
    phys = {k: affinity.scale(v, -1, 1, origin=(0, 0)) for k, v in face.items()}
    gh = sum(v.intersection(back).area for k, v in phys.items() if k != 2) if back is not None else 0
    print(f"{n:16s} {b[2]-b[0]:5.1f} x {b[3]-b[1]:4.1f} {icon.area:5.0f} ({(b[0]+b[2])/2:+5.1f},{(b[1]+b[3])/2:+5.1f}) ({c.x:+5.1f},{c.y:+5.1f}) {gh:10.0f} mm2")
