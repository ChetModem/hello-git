import pickle, json, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.ops import unary_union
pics = pickle.load(open(sys.argv[1], 'rb')); names = json.load(open(sys.argv[2])); out = sys.argv[3]
try:
    F1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18); F2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except Exception: F1 = F2 = None
rows = []
for key, p in pics.items():
    L, over, fill, meshes, fm = p['L'], p['over'], p['fill'], p['meshes'], p['fm']
    allg = unary_union([g for g in L if not g.is_empty]); bx = allg.bounds
    w, h = bx[2] - bx[0], bx[3] - bx[1]; sc = min(380 / max(w, 1), 380 / max(h, 1))
    W, Hh = int(w * sc) + 20, int(h * sc) + 20
    P = lambda x, y: ((x - bx[0]) * sc + 10, (bx[3] - y) * sc + 10)
    def draw(img, g, col):
        d = ImageDraw.Draw(img)
        for q in (g.geoms if hasattr(g, 'geoms') else [g]):
            if q.is_empty or q.geom_type != 'Polygon': continue
            d.polygon([P(*c) for c in q.exterior.coords], fill=col)
    def base():
        img = Image.new('RGB', (W, Hh), 'white')
        for k, g in enumerate(L):
            if not g.is_empty: v = int(60 + 160 * k / len(L)); draw(img, g, (v, v, v))
        return img
    a = base(); ov = unary_union([u for u in over if not u.is_empty]); draw(a, ov.buffer(max(0.15, 1.5 / sc)), (230, 40, 40))
    b = base(); fi = unary_union([g for g in fill if not g.is_empty]); draw(b, fi.buffer(max(0.1, 1 / sc)), (255, 150, 0))
    # side cut through the largest overhang
    big = max((ov.geoms if hasattr(ov, 'geoms') else [ov]), key=lambda g: g.area); cy = big.centroid.y
    zt = max(m.bounds[1][2] for m in meshes); sc2 = min(sc, 300 / max(zt, 1)) if zt > 0 else sc
    SW, SH = W, int(zt * sc2) + 30; side = Image.new('RGB', (SW, SH), 'white'); ds = ImageDraw.Draw(side)
    for m, col in [(x, (150, 150, 150)) for x in meshes] + [(fm, (255, 150, 0))]:
        s = m.section([0, 1, 0], [0, cy, 0])
        if s is None: continue
        for e in s.discrete:
            e = np.asarray(e); ds.polygon([((x - bx[0]) * sc + 10, SH - 10 - z * sc2) for x, _, z in e], fill=col)
    title = names.get(key, key)
    row = Image.new('RGB', (W * 3 + 40, max(Hh, SH) + 40), 'white'); dr = ImageDraw.Draw(row)
    dr.text((5, 5), title, fill=(0, 0, 0), font=F1)
    row.paste(a, (0, 35)); row.paste(b, (W + 20, 35)); row.paste(side, (2 * W + 40, 35 + max(0, Hh - SH)))
    rows.append(row)
head = Image.new('RGB', (max(r.width for r in rows), 70), 'white'); dh = ImageDraw.Draw(head)
dh.text((5, 5), 'Left: from above, RED = overhang too steep to print well (>55 deg).   Middle: ORANGE = fill added underneath.', fill=(0, 0, 0), font=F2)
dh.text((5, 28), 'Right: side cut through the biggest overhang. Grey = original model, orange = new fill.', fill=(0, 0, 0), font=F2)
sheet = Image.new('RGB', (head.width, head.height + sum(r.height for r in rows)), 'white'); y = 0
for r in [head] + rows: sheet.paste(r, (0, y)); y += r.height
sheet.save(out); print(sheet.size)
