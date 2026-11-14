"""Turn the outline development-card icons into the solid style used on the resource cards.
Coordinates are the card's own frame (as printed), so no mirroring is needed."""
import pickle
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity
D = pickle.load(open(__file__.rsplit('/', 1)[0] + '/dev_shapes.pkl', 'rb'))

W = 0.82   # outline stroke width in the original art

def _clean(g, min_area):
    gs = list(g.geoms) if hasattr(g, 'geoms') else [g]
    return unary_union([x for x in gs if x.area >= min_area])

GAP_F = 0.7    # black gap between separate shapes, in final mm
LINE_F = 0.75  # black detail line width, in final mm
COL_F = 0.7    # thinnest coloured line, in final mm

def _cells(name, k=1.0):
    """Each enclosed area of the outline art becomes its own filled shape, grown back out to the
    outline's outer edge. Where two areas meet, the smaller one gives way to the larger with a clean gap.
    Outline loops that sit inside another area (star, road dashes, hexagons) become black detail lines."""
    strokes = D[name]['icon']
    pieces = list(strokes.geoms) if hasattr(strokes, 'geoms') else [strokes]
    holes = [Polygon(h) for p in pieces for h in p.interiors]
    # a piece lying inside another piece's area is a detail drawn on top of it
    detail = [p for p in pieces if any(h.contains(p) for h in holes)]
    detail_holes = [Polygon(h) for p in detail for h in p.interiors]
    areas = [h for p in pieces if p not in detail for h in (Polygon(i) for i in p.interiors)]
    # which shape stays whole where two meet: normally the larger; for Monopoly the round heads stay whole
    cells = sorted((h.buffer(W / 2, join_style=2, mitre_limit=3) for h in areas), key=lambda c: c.area, reverse=(name == 'mono'))
    out = []
    for i, c in enumerate(cells):
        bigger = unary_union(cells[i + 1:]) if i + 1 < len(cells) else None
        out.append(c.difference(bigger.buffer(GAP_F / k)) if bigger is not None else c)
    shape = unary_union(out)
    # outline pieces that enclose nothing (e.g. arrow is its own piece with a hole, handled above);
    # detail lines: subtract their strokes, keep whatever they enclose filled
    for p in detail:   # detail lines drawn at LINE_F mm wide once scaled
        shape = shape.difference(p.buffer(max(0, (LINE_F / k - W) / 2), join_style=2, mitre_limit=3))
    return shape

def solid(name, k=1.0):
    strokes = D[name]['icon']
    pieces = list(strokes.geoms) if hasattr(strokes, 'geoms') else [strokes]
    if name == 'vp':
        fills = [Polygon(p.exterior, [h for h in p.interiors if abs(Polygon(h).centroid.x) > 8]) for p in pieces]
        sil = unary_union(fills)
        band = sil.difference(sil.buffer(-(W + 0.1), join_style=2))
        inner = _clean(strokes.difference(band), 0.4)
        inner = _clean(inner.intersection(Polygon([(-6, -2), (6, -2), (6, 12), (-6, 12)])), 0.4)   # star only
        sil = sil.union(strokes.buffer(max(0, (COL_F / k - W) / 2)))     # keep the thin handles printable
        out = sil.difference(inner.buffer(max(0, (LINE_F / k - W) / 2), join_style=2, mitre_limit=3))
    else:
        out = _cells(name, k)
    out = out.buffer(0.25, join_style=1).buffer(-0.25, join_style=1)   # round sharp inward corners (no black specks)
    out = _clean(out, 0.5)
    gs = list(out.geoms) if hasattr(out, 'geoms') else [out]
    gs = [Polygon(g.exterior, [h for h in g.interiors if Polygon(h).area > 0.3]) for g in gs]
    return unary_union(gs).buffer(0)

def safe_zone():
    logo = pickle.load(open(__file__.rsplit('/', 1)[0] + '/logo.pkl', 'rb'))
    g = max(logo.geoms, key=lambda x: x.area) if hasattr(logo, 'geoms') else logo
    return Polygon(g.interiors[0]).buffer(-0.3)    # same frame as the resource icons

def fitted(name):
    z = safe_zone(); k = 1.0
    for _ in range(3):              # gaps and lines depend on the final scale, so refit a few times
        p = solid(name, k)
        lo, hi = 0.3, 1.0
        for _ in range(30):
            m = (lo + hi) / 2
            (lo, hi) = (m, hi) if z.contains(affinity.scale(p, m, m, origin=(0, 0))) else (lo, m)
        k = round(lo - 0.003, 3)
    p = solid(name, k)
    while not z.contains(affinity.scale(p, k, k, origin=(0, 0))): k -= 0.002
    return affinity.scale(p, k, k, origin=(0, 0)), k


NAMES = {'knight': 'Knight', 'vp': 'Victory Point', 'rb': 'Road Building', 'yop': 'Year of Plenty', 'mono': 'Monopoly'}
