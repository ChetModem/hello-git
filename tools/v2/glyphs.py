"""v2 shared glyphs. Final millimetres, face view (as you look at the printed face).
Rules: coloured lines >= 0.7 mm, black gaps >= 0.7 mm (0.6 absolute floor)."""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import design_v1 as V1
import icons2 as I
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity

GAP = 0.7
text, rr, stadium, hexagon, place, printable, dev_icon = V1.text, V1.rr, V1.stadium, V1.hexagon, V1.place, V1.printable, V1.dev_icon

def pieces(g): return [p for p in (g.geoms if hasattr(g, 'geoms') else [g]) if not p.is_empty]
def centre(g):
    b = g.bounds; return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)

# ---------------------------------------------------------------- road: one look everywhere
def road(length, width):
    """A road segment: rounded bar with a dashed black centre line (the same drawing on every card;
    only the number, size and layout of segments changes)."""
    body = rr(-length / 2, -width / 2, length / 2, width / 2, min(0.6, width * 0.25))
    dw = max(GAP, round(width * 0.24, 2))                      # dash width
    dl = max(1.2, width * 0.55); dg = max(1.0, width * 0.45)    # dash length / gap
    usable = length - 2 * max(1.0, width * 0.45)
    n = max(1, int((usable + dg) // (dl + dg)))
    tot = n * dl + (n - 1) * dg; x0 = -tot / 2
    dashes = unary_union([box(x0 + k * (dl + dg), -dw / 2, x0 + k * (dl + dg) + dl, dw / 2) for k in range(n)])
    return body.difference(dashes)

def road_chain(n, seg, width, angle=30):
    """n road segments zig-zagging along hex edges (60 degree bends), exactly >= 0.7 mm apart at each bend."""
    def build(L):
        x = y = 0; parts = []
        for k in range(n):
            a = angle if k % 2 == 0 else -angle
            c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a))
            parts.append(affinity.translate(affinity.rotate(road(L, width), a, origin=(0, 0)), x + seg * c / 2, y + seg * s_ / 2))
            x, y = x + seg * c, y + seg * s_
        return parts
    lo, hi = seg * 0.3, seg
    for _ in range(30):
        L = (lo + hi) / 2; ps = build(L)
        d = min(ps[i].distance(ps[i + 1]) for i in range(n - 1))
        (lo, hi) = (L, hi) if d >= GAP + 0.02 else (lo, L)
    return centre(unary_union(build(lo)))

# ---------------------------------------------------------------- card: one look everywhere
def card(w, h, hex_fill=True):
    """A card: white rounded rectangle with a hexagon in the middle.
    hex_fill=True -> returns (card_white, hex_shape) where the hexagon is to be printed in a resource colour
    (with a black ring between it and the white). hex_fill=False -> development card: black hexagon outline."""
    body = rr(-w / 2, -h / 2, w / 2, h / 2, min(0.9, w * 0.12))
    hw = w * 0.52
    hx = hexagon(0, 0, hw)
    if hex_fill:
        return body.difference(hx.buffer(GAP, join_style=2)), hx
    ring = hx.difference(hx.buffer(-GAP, join_style=2))
    return body.difference(ring), None

# ---------------------------------------------------------------- knight helmet with a joined crest
def helmet(height):
    """Knight helmet with a plain rounded dome: no crest (it broke into dots at small sizes).
    The notch where the old crest sat is filled and the top re-rounded; the visor is untouched."""
    g = dev_icon('knight', height)
    main = max(pieces(g), key=lambda p: p.area)
    main = Polygon(main.exterior, [h for h in main.interiors if Polygon(h).area > 8.0])
    b = main.bounds; top_band = box(b[0] - 1, b[3] - 0.32 * (b[3] - b[1]), b[2] + 1, b[3] + 1)
    r = max(0.8, height * 0.05)
    closed = main.buffer(r, join_style=1).buffer(-r, join_style=1)              # fills the old crest notch
    hull_top = Polygon(main.exterior).convex_hull.intersection(top_band)          # smooth dome outline at the top
    dome = unary_union([main, closed.intersection(top_band), hull_top])                 # convex hull: no dip where the crest was
    return centre(dome.buffer(0))

# ---------------------------------------------------------------- crown (monopoly)
def crown(w):
    h = w * 0.62
    band = rr(-w / 2, -h / 2, w / 2, -h / 2 + h * 0.3, min(0.5, w * 0.05))
    pts = [(-w / 2, -h / 2 + h * 0.25), (-w / 2, h * 0.18), (-w * 0.27, -h * 0.02), (0, h * 0.32), (w * 0.27, -h * 0.02), (w / 2, h * 0.18), (w / 2, -h / 2 + h * 0.25)]
    body = unary_union([band, Polygon(pts)]).buffer(0.3, join_style=1).buffer(-0.3, join_style=1)
    balls = unary_union([Point(x, y).buffer(w * 0.075, quad_segs=16) for x, y in [(-w / 2 + w * 0.03, h * 0.18 + w * 0.03), (0, h * 0.32 + w * 0.035), (w / 2 - w * 0.03, h * 0.18 + w * 0.03)]])
    bpos = [(-w / 2 + w * 0.03, h * 0.18 + w * 0.03), (0, h * 0.32 + w * 0.035), (w / 2 - w * 0.03, h * 0.18 + w * 0.03)]
    necks = unary_union([stadium((x, y), (x * 0.92, y - w * 0.14), max(1.0, w * 0.075)) for x, y in bpos])   # solid joint under each ball
    balls = unary_union([balls, necks])
    gem_r = max(GAP / 2 + 0.1, w * 0.05)
    gems = unary_union([Point(x, -h / 2 + h * 0.15).buffer(gem_r, quad_segs=12) for x in (-w * 0.28, 0, w * 0.28)])
    sep = box(-w / 2 - 1, -h / 2 + h * 0.3, w / 2 + 1, -h / 2 + h * 0.3 + GAP)     # black line between band and points
    return centre(unary_union([body, balls]).difference(gems).difference(sep))

# ---------------------------------------------------------------- wheat (resource card): bolder grains
def wheat_v2(k=0.74, rows=5):
    """Three ears like v1 but fewer, fatter grains (gaps stay 0.65 mm at final size)."""
    parts = []
    pc = 3.28 * 6 / rows
    c, wc = I.ear(0.0, (17.6 * k, 12.9 * k), 2.3 * k, rows, 12.5 * k, 8.0 * k, 0.8, 4.9 * k, pc * k)
    parts += c + [stadium((0.0, 8.0 * k - (rows - 1) * pc * k - 1.3), (0.0, -17.2 * k), 1.3 * k)]
    ps = 2.74 * 6 / rows
    for cx in (-10.6 * k, 10.6 * k):
        e, ws = I.ear(cx, (9.9 * k, 7.0 * k), 2.0 * k, rows, 6.1 * k, 2.8 * k, 0.75, 4.2 * k, ps * k)
        parts += e + [stadium((cx, 2.8 * k - (rows - 1) * ps * k - 1.3), (cx, -17.2 * k), 1.2 * k)]
    wheat_v2.widths = (wc, ws)
    return unary_union(parts)

# ---------------------------------------------------------------- ore (resource card): facets + balanced
def ore_v2(f=0.80):
    """Two peaks, the small one taller than v1 and tucked closer; a black ridge line on each face gives
    them a lit side and a shadow side. Centred on its own weight."""
    big = affinity.scale(Polygon([(-6.0, -10.0), (16.0, -10.0), (5.0, 13.5)]), f, f, origin=(0, 0))
    small = affinity.scale(Polygon([(-16.0, -10.0), (-1.5, -10.0), (-8.75, 4.0)]), f, f, origin=(0, 0)).difference(big.buffer(GAP * 1.2))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    big, small = soft(big, 0.5), soft(small, 0.4)
    ridge_b = LineString([(5.0 * f, 13.0 * f), (7.2 * f, -10.5 * f)]).buffer(0.42, cap_style=2)
    ridge_s = LineString([(-8.75 * f, 3.6 * f), (-7.6 * f, -10.5 * f)]).buffer(0.38, cap_style=2)
    g = unary_union([big.difference(ridge_b), small.difference(ridge_s)])
    c = g.centroid
    return affinity.translate(g, -c.x, -(g.bounds[1] + g.bounds[3]) / 2)


# ---------------------------------------------------------------- fit inside the back ring (no show-through)
import pickle
def safe_zone():
    logo = pickle.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logo.pkl'), 'rb'))
    gz = max(logo.geoms, key=lambda x: x.area) if hasattr(logo, 'geoms') else logo
    return Polygon(gz.interiors[0]).buffer(-0.3)

def fit_zone(g, zone=None, centre_on=(0, 0)):
    """Largest uniform scale (<= 1) at which g fits inside the zone."""
    zone = zone or safe_zone(); g = centre(g); lo, hi = 0.3, 1.0
    if zone.contains(g): return g, 1.0
    for _ in range(30):
        m = (lo + hi) / 2; (lo, hi) = (m, hi) if zone.contains(affinity.scale(g, m, m, origin=(0, 0))) else (lo, m)
    return affinity.scale(g, lo, lo, origin=(0, 0)), lo


def closest(g):
    ps = pieces(g); return min([a.distance(b) for i, a in enumerate(ps) for b in ps[i + 1:]] or [9])

def wheat_final():
    """Largest 4-row wheat that fits the safe zone with every gap >= 0.7 mm (drawn at final size)."""
    z = safe_zone(); best = None
    for k in np.arange(0.80, 0.55, -0.01):
        g = centre(wheat_v2(k, 4))
        if z.contains(g) and closest(g) >= GAP - 0.01: best = (g, k); break
    return best

def ore_final():
    z = safe_zone()
    for f in np.arange(0.85, 0.6, -0.01):
        g = ore_v2(f)
        if z.contains(g) and closest(g) >= GAP - 0.01: return g, f

# ---------------------------------------------------------------- wheat, solid style
def ear_solid(cx, y_top, y_bot, hw, n_cuts, ang=38, stalk_to=None, stalk_w=1.1):
    """A solid ear (pointed top, rounded bottom) with black V-shaped grain lines across it and a stalk."""
    h = y_top - y_bot
    pts = [(cx, y_top)]
    for t in np.linspace(0.12, 1.0, 14):           # right edge from tip to bottom
        y = y_top - t * h
        w = hw * np.sin(np.pi * min(1.0, t * 1.15) ** 0.75) if t < 0.87 else hw * np.sqrt(max(0, 1 - ((t - 0.87) / 0.13) ** 2)) * np.sin(np.pi * 0.87 ** 0.75 * 1.0)
        pts.append((cx + max(w, 0.0), y))
    right = pts[1:]
    poly = Polygon([pts[0]] + right + [(2 * cx - x, y) for x, y in reversed(right)]).buffer(0.25, join_style=1).buffer(0)
    cuts = []
    pitch = (h * 0.78) / n_cuts
    for i in range(n_cuts):
        ya = y_top - h * 0.16 - i * pitch
        dx = hw * 1.4; dy = dx * np.tan(np.radians(ang))
        cuts.append(LineString([(cx - dx, ya + dy), (cx, ya), (cx + dx, ya + dy)]).buffer(GAP / 2, join_style=2))
    ear = poly.difference(unary_union(cuts))
    parts = [ear]
    if stalk_to is not None:
        parts.append(stadium((cx, y_bot - GAP - 0.35 - stalk_w / 2), (cx, stalk_to), stalk_w))
    return unary_union(parts)

def wheat_solid(s=1.0):
    """Three ears, solid style. s scales the layout (line and gap widths stay absolute)."""
    g = unary_union([ear_solid(0, 11.5 * s, -3.0 * s, 2.7 * s, 5, stalk_to=-12.5 * s, stalk_w=1.2),
                     ear_solid(-7.2 * s, 6.5 * s, -5.6 * s, 2.3 * s, 4, stalk_to=-12.5 * s, stalk_w=1.1),
                     ear_solid(7.2 * s, 6.5 * s, -5.6 * s, 2.3 * s, 4, stalk_to=-12.5 * s, stalk_w=1.1)])
    return centre(g)

def wheat_solid_final():
    z = safe_zone()
    for s_ in np.arange(1.2, 0.6, -0.01):
        g = wheat_solid(s_)
        if z.contains(g) and closest(g) >= GAP - 0.01: return g, s_


def fill_zone(g, zone=None):
    """Scale g up or down to the largest size that fits the zone (gaps only grow when scaling up)."""
    zone = zone or safe_zone(); g = centre(g); lo, hi = 0.3, 4.0
    for _ in range(40):
        m = (lo + hi) / 2; (lo, hi) = (m, hi) if zone.contains(affinity.scale(g, m, m, origin=(0, 0))) else (lo, m)
    return affinity.scale(g, lo, lo, origin=(0, 0)), lo
