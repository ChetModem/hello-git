import pickle, numpy as np
from shapely.ops import unary_union
from shapely.geometry import Point, box
from PIL import Image, ImageDraw, ImageFont
D = pickle.load(open('cards.pkl', 'rb'))
S = 9; CW, CH = 54 * S, 80 * S; F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def draw(img, g, col, ox, oy):
    mask = Image.new('L', img.size, 0)
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        if p.is_empty or p.geom_type != 'Polygon': continue
        t = Image.new('L', img.size, 0); d = ImageDraw.Draw(t)
        d.polygon([(ox + CW / 2 + x * S, oy + CH / 2 - y * S) for x, y in p.exterior.coords], fill=255)
        for h in p.interiors: d.polygon([(ox + CW / 2 + x * S, oy + CH / 2 - y * S) for x, y in h.coords], fill=0)
        mask.paste(255, (0, 0), t)
    img.paste(col, (0, 0), mask)
def card_img(d, side):
    img = Image.new('RGB', (CW, CH), (235, 235, 235)); sh = d[side]
    for ex in sorted(sh, key=lambda e: e != 1):            # black body first
        c = rgb(d['cols'][ex - 1]) if ex != 1 else (25, 25, 25)
        draw(img, sh[ex], c, 0, 0)
    return img
labels = list(D)
rows = [labels[:5], labels[5:10], labels[10:]]
W = 5 * (CW + 20) + 20; H = 3 * (CH + 50) + (CH + 50) + 60
out = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(out); y = 10
for r in rows:
    x = 10
    for l in r:
        dr.text((x, y), l, fill='black', font=F); out.paste(card_img(D[l], 'face'), (x, y + 35)); x += CW + 20
    y += CH + 50
dr.text((10, y), 'Backs:', fill='black', font=F); y += 35; x = 10
for l in ['Brick', 'Knight', 'Building Costs', 'Longest Road']:
    out.paste(card_img(D[l], 'back'), (x, y)); dr.text((x + 5, y + 5), {'Brick': 'resource', 'Knight': 'development', 'Building Costs': 'building costs', 'Longest Road': 'longest road / army'}[l], fill='white', font=F); x += CW + 20
out.save('all_cards.png'); print(out.size)
# measurements
CORN = unary_union([Point(x, y).buffer(4.6) for x in (-20, 20) for y in (-32, 32)])
print(f"{'card':16s} {'icon w x h':>12s} {'ink mm2':>8s} {'bbox ctr':>14s} {'ink ctr':>14s}  colours (filament: hex)  corners")
for l, d in D.items():
    ink = unary_union([g for ex, g in d['face'].items() if ex != 1]).buffer(0)
    icon = ink.difference(CORN) if d['corners'] else ink
    b = icon.bounds; c = icon.centroid
    corner = ink.intersection(CORN)
    cols = {ex: d['cols'][ex - 1] for ex in d['face'] if ex != 1 and not d['face'][ex].difference(CORN).is_empty}
    ccols = {ex: d['cols'][ex - 1] for ex in d['face'] if ex != 1 and not d['face'][ex].intersection(CORN).is_empty}
    print(f"{l:16s} {b[2]-b[0]:5.1f} x {b[3]-b[1]:4.1f} {icon.area:8.0f} ({(b[0]+b[2])/2:+5.1f},{(b[1]+b[3])/2:+5.1f}) ({c.x:+5.1f},{c.y:+5.1f})  {cols}  {ccols if d['corners'] else 'none'} {round(corner.area/4,1) if d['corners'] else ''}")
