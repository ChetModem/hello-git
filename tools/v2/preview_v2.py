import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cards_v2 as C, glyphs as G, design_v1 as V1
from shapely.ops import unary_union
from shapely import affinity
from shapely.strtree import STRtree
from PIL import Image, ImageDraw, ImageFont
COLS = {1: (25, 25, 25), 2: (240, 240, 240), 3: (200, 60, 50), 4: (110, 120, 60), 5: (240, 190, 140), 6: (170, 170, 175), 7: (0, 128, 0), 8: (128, 128, 255), 9: (255, 128, 0)}
S = 9; CW, CH = 54 * S, 80 * S
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
def draw(img, g, col, ox=0, oy=0):
    mask = Image.new('L', img.size, 0)
    for p in G.pieces(g):
        if p.geom_type != 'Polygon': continue
        t = Image.new('L', img.size, 0); d = ImageDraw.Draw(t)
        d.polygon([(ox + CW / 2 + x * S, oy + CH / 2 - y * S) for x, y in p.exterior.coords], fill=255)
        for h in p.interiors: d.polygon([(ox + CW / 2 + x * S, oy + CH / 2 - y * S) for x, y in h.coords], fill=0)
        mask.paste(255, (0, 0), t)
    img.paste(col, (0, 0), mask)
def card_img(shapes):
    img = Image.new('RGB', (CW, CH), (235, 235, 235)); draw(img, V1.CARD, COLS[1])
    for k, g in shapes.items(): draw(img, g, COLS[k])
    return img
def thin(g, w):
    r = g.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
    lost = g.difference(r).buffer(-0.01).buffer(0.01)
    return [round(p.area, 2) for p in G.pieces(lost) if p.area > 0.12]
res = {}
for name in C.CARDS:
    face, back, corner = C.build(name)
    phys = {k: affinity.scale(v, -1, 1, origin=(0, 0)) for k, v in face.items()}
    ghost = sum(v.intersection(back).area for k, v in phys.items() if k != 2)
    ps = [(k, p) for k, v in face.items() for p in G.pieces(v)]
    tree = STRtree([p for _, p in ps]); close = []
    for i, (k, p) in enumerate(ps):
        for j in tree.query(p.buffer(0.6)):
            if j > i and p.distance(ps[j][1]) < 0.6: close.append(round(p.distance(ps[j][1]), 2))
    allc = unary_union(list(face.values()))
    ov = sum(face[a].intersection(face[b]).area for a in face for b in face if a < b)
    blk = V1.CARD.difference(allc)
    out = allc.difference(V1.CARD.buffer(-1.5)).area
    tc = {k: thin(v, 0.58) for k, v in face.items() if thin(v, 0.58)}
    tb = thin(blk, 0.58); bt = thin(back, 0.58)
    ink = unary_union([v for k, v in face.items()]).difference(C.corners(0) if corner else G.Polygon()).area if True else 0
    print(f'{name:15s} show-through {ghost:5.1f} mm2 | thin colour {tc or "-"} | thin black {tb or "-"} | pieces <0.6 apart {len(close)} | overlap {ov:.2f} | near edge {out:.2f} | back thin {bt or "-"} | colours {sorted(face)}')
    res[name] = (face, back)
pickle.dump(res, open('v2_cards.pkl', 'wb'))
