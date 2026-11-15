import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
from PIL import Image, ImageDraw, ImageFont
from shapely.ops import unary_union
S = 10   # px per mm
def draw(img, g, col, ox, oy, H):
    mask = Image.new('L', img.size, 0)
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        if p.is_empty or p.geom_type != 'Polygon': continue
        m = Image.new('L', img.size, 0); d = ImageDraw.Draw(m)
        d.polygon([(ox + x * S, oy + (H / 2 - y) * S) for x, y in p.exterior.coords], fill=255)
        for h in p.interiors: d.polygon([(ox + x * S, oy + (H / 2 - y) * S) for x, y in h.coords], fill=0)
        mask.paste(255, (0, 0), m)
    img.paste(col, (0, 0), mask)
def card(shapes):
    W, H = 54, 80; img = Image.new('RGB', (W * S + 20, H * S + 20), (235, 235, 235))
    draw(img, D.CARD, D.COLS[1], 10 + W / 2 * S, 10, H)
    for slot, g in shapes.items(): draw(img, g, D.COLS[slot], 10 + W / 2 * S, 10, H)
    return img
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
cards = [(n, card(f())) for n, (f, c) in D.CARDS.items()]
row = Image.new('RGB', (sum(c.width for _, c in cards) + 40, cards[0][1].height + 50), 'white'); x = 0; dr = ImageDraw.Draw(row)
for n, c in cards: row.paste(c, (x, 50)); dr.text((x + 10, 10), {'building-costs': 'Building Costs (x4)', 'longest-road': 'Longest Road', 'largest-army': 'Largest Army'}[n], fill='black', font=F); x += c.width + 20
row.save('cards_preview.png')
L = D.legend(); W, H = D.BOARD_W, D.BOARD_H; print('board', W, 'x', H, 'mm')
img = Image.new('RGB', (int(W * S) + 20, int(H * S) + 20), (235, 235, 235))
draw(img, D.rr(-W / 2, -H / 2, W / 2, H / 2, 4), D.COLS[1], 10 + W / 2 * S, 10, H)
for slot, g in L.items(): draw(img, g, D.COLS[slot], 10 + W / 2 * S, 10, H)
img.save('legend_preview.png'); print(row.size, img.size)
# printability: pieces of colour (or of black gap) narrower than 0.7 mm, ignoring corner tips
def thin(g, w=0.58):
    r = g.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
    lost = g.difference(r).buffer(-0.01).buffer(0.01)
    return [round(p.area, 2) for p in (lost.geoms if hasattr(lost, 'geoms') else [lost]) if p.area > 0.12]
import shapely
for name, shapes in [(n, f()) for n, (f, c) in D.CARDS.items()] + [('legend', L)]:
    allc = unary_union(list(shapes.values()))
    frame = D.CARD if name != 'legend' else D.rr(-D.BOARD_W/2, -D.BOARD_H/2, D.BOARD_W/2, D.BOARD_H/2, 4)
    ov = sum(shapes[a].intersection(shapes[b]).area for a in shapes for b in shapes if a < b)
    if name == 'legend':
        print('legend text strokes under 0.5 mm:', len(thin(shapes[2], 0.5)), 'pieces, largest', max(thin(shapes[2], 0.5) or [0]), 'mm2 | black gaps under 0.5 mm:', thin(frame.difference(allc), 0.5)[:10])
    print(name, 'thin colour bits:', {k: thin(v) for k, v in shapes.items() if thin(v)}, '| thin black gaps:', thin(frame.difference(allc))[:12], '| colour overlap', round(ov, 3), '| outside frame', round(allc.difference(frame.buffer(-1.5)).area, 2))
