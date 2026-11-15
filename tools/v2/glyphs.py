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

# ---------------------------------------------------------------- v2b additions
def trophy(height):
    """One trophy everywhere: solid cup with filled handles and a solid black star (as on Longest Road / Largest Army)."""
    t = dev_icon('vp', height)
    ps = sorted(pieces(t), key=lambda p: -p.area)
    main = ps[0]
    b = main.bounds; cx = (b[0] + b[2]) / 2
    holes = [Polygon(h) for h in main.interiors]
    star = [h for h in holes if abs(h.centroid.x - cx) < (b[2] - b[0]) * 0.2]          # the star sits in the middle of the cup
    sil = Polygon(main.exterior)                                                       # handles and everything filled
    g = sil.difference(unary_union(star)) if star else sil
    g = g.buffer(0.3, join_style=2, mitre_limit=10).buffer(-0.3, join_style=2, mitre_limit=10)   # no black slivers
    return centre(printable(g, w=0.6, speck=1.0))

def crown2(w):
    """Simple crown: three points (middle tallest) with round tips, a solid band, one black line between them."""
    h = w * 0.7
    band_h = h * 0.26
    band = rr(-w / 2, -h / 2, w / 2, -h / 2 + band_h, min(0.6, w * 0.05))
    y0 = -h / 2 + band_h + GAP
    tips = [(-w / 2 + w * 0.06, h * 0.22), (0, h * 0.40), (w / 2 - w * 0.06, h * 0.22)]
    valleys = [(-w * 0.22, y0 + h * 0.18), (w * 0.22, y0 + h * 0.18)]
    pts = [(-w / 2, y0), tips[0], valleys[0], tips[1], valleys[1], tips[2], (w / 2, y0)]
    body = Polygon(pts).buffer(0.35, join_style=1).buffer(-0.35, join_style=1)
    balls = unary_union([Point(x, y + w * 0.035).buffer(w * 0.07, quad_segs=16) for x, y in tips])
    return centre(unary_union([band, body, balls]))

def hammer(length, width):
    """Hammer pointing up along y: handle plus a head with a flat face on one side and a claw on the other."""
    hw = width * 0.55
    handle = rr(-hw / 2, -length / 2, hw / 2, length / 2 - width * 0.6, hw * 0.45)
    head_w = width * 2.9; head_h = width * 1.15; yt = length / 2
    face = rr(-head_w / 2, yt - head_h, -head_w * 0.05, yt, 0.4)                                   # striking side
    claw = Polygon([(-head_w * 0.1, yt - head_h), (head_w / 2, yt - head_h * 0.15), (head_w / 2 - 0.2, yt), (-head_w * 0.1, yt)])
    head = unary_union([face, claw]).buffer(0.3, join_style=1).buffer(-0.3, join_style=1)
    return unary_union([handle, head])

def road_and_hammer():
    """Road and hammer crossed (road behind, hammer in front with a black gap where they cross)."""
    r = affinity.rotate(road(26.0, 5.0), 45, origin=(0, 0))
    hm = affinity.rotate(hammer(25.0, 3.2), 45, origin=(0, 0))
    r = r.difference(hm.buffer(GAP, join_style=1))
    return centre(printable(unary_union([r, hm]), w=0.6, speck=1.0))

def ore_v3(f=0.80):
    """Two peaks with a Matterhorn-style shoulder (a zag on the right flank) and ridge lines."""
    P = lambda pts: affinity.scale(Polygon(pts), f, f, origin=(0, 0))
    big = P([(-6.0, -10.0), (16.0, -10.0), (11.2, -0.5), (13.2, 1.6), (6.5, 13.5), (4.2, 11.0)])
    small = P([(-16.0, -10.0), (-1.5, -10.0), (-5.2, -3.4), (-3.9, -1.8), (-8.9, 4.4)]).difference(big.buffer(GAP * 1.2))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    big, small = soft(big, 0.45), soft(small, 0.35)
    ridge_b = LineString([(6.6 * f, 11.2 * f), (8.2 * f, 3.0 * f), (7.4 * f, -10.5 * f)]).buffer(0.42, cap_style=2, join_style=2)
    ridge_s = LineString([(-8.8 * f, 2.6 * f), (-7.7 * f, -10.5 * f)]).buffer(0.38, cap_style=2)
    g = printable(unary_union([big.difference(ridge_b), small.difference(ridge_s)]), w=0.6, speck=1.0)
    c = g.centroid
    return affinity.translate(g, -c.x, -(g.bounds[1] + g.bounds[3]) / 2)

def ore3_final():
    z = safe_zone()
    for f in np.arange(0.85, 0.6, -0.01):
        g = ore_v3(f)
        if z.contains(g) and closest(g) >= GAP - 0.01: return g, f

def ore_v4(f=0.80):
    """Matterhorn-style: big peak with a summit leaning right and one shoulder on the right flank; plain small peak.
    Flat silhouettes, no ridge lines."""
    P = lambda pts: affinity.scale(Polygon(pts), f, f, origin=(0, 0))
    big = P([(-7.0, -10.0), (17.0, -10.0), (11.6, -0.8), (13.4, 1.0), (6.2, 13.8), (5.0, 13.6), (2.0, 7.0)])
    small = P([(-16.0, -10.0), (-2.5, -10.0), (-8.6, 3.2)]).difference(big.buffer(GAP * 1.1))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    g = printable(unary_union([soft(big, 0.45), soft(small, 0.4)]), w=0.6, speck=1.0)
    c = g.centroid
    return affinity.translate(g, -c.x, -(g.bounds[1] + g.bounds[3]) / 2)

def ore4_final():
    z = safe_zone()
    for f in np.arange(0.9, 0.6, -0.01):
        g = ore_v4(f)
        if z.contains(g) and closest(g) >= GAP - 0.01: return g, f

def hammer2(length, width):
    """Hammer pointing up: handle, square head at right angles to it (flat face one side, short claw the other)."""
    hw = width * 0.6
    handle = rr(-hw / 2, -length / 2, hw / 2, length / 2 - width * 0.4, hw * 0.45)
    hh = width * 1.25; hl = width * 3.0; yt = length / 2
    face = rr(-hl * 0.5, yt - hh, hl * 0.12, yt, 0.35)
    claw = Polygon([(hl * 0.1, yt - hh * 0.75), (hl * 0.5, yt - hh * 0.25), (hl * 0.46, yt - hh * 0.05), (hl * 0.1, yt)])
    return unary_union([handle, face, claw]).buffer(0.25, join_style=1).buffer(-0.25, join_style=1)

def road_and_hammer2():
    L, W = 24.0, 5.2
    body = rr(-L / 2, -W / 2, L / 2, W / 2, min(0.6, W * 0.25)); dw = max(GAP, round(W * 0.24, 2))
    dashes = unary_union([box(sx * L * 0.30 - 1.9, -dw / 2, sx * L * 0.30 + 1.9, dw / 2) for sx in (-1, 1)])   # one dash per half, clear of the crossing
    r = affinity.rotate(body.difference(dashes), 45, origin=(0, 0))          # road along /
    hm = affinity.rotate(hammer2(24.0, 3.2), 45, origin=(0, 0))      # hammer handle along \ (head top-left)
    r = r.difference(hm.buffer(GAP, join_style=1))
    return centre(printable(unary_union([r, hm]), w=0.6, speck=1.0))

# ---------------------------------------------------------------- v2c
def money_bag(height):
    """Coin purse silhouette: round bag, cinched neck, a three-lobe ruffle on top."""
    h = height; w = h * 0.78
    body = affinity.scale(Point(0, 0).buffer(1, quad_segs=48), w / 2, h * 0.36)
    body = affinity.translate(body, 0, -h * 0.5 + h * 0.36)
    neck = Polygon([(-w * 0.20, h * 0.08), (w * 0.20, h * 0.08), (w * 0.13, h * 0.22), (-w * 0.13, h * 0.22)])
    ruff = unary_union([Point(x, h * 0.30).buffer(w * 0.12, quad_segs=24) for x in (-w * 0.17, 0, w * 0.17)] +
                       [Point(0, h * 0.36).buffer(w * 0.12, quad_segs=24)])
    g = unary_union([body, neck, ruff]).buffer(0.6, join_style=1).buffer(-0.6, join_style=1)
    return centre(g)

def bag_outline(height, lw):
    """Outline of the purse at line width lw, plus the tie across the neck."""
    sil = money_bag(height)
    hollow = sil.buffer(-lw, join_style=1)
    body_hollow = max(pieces(hollow), key=lambda p: p.area)
    b = sil.bounds; h = b[3] - b[1]
    tie_y = b[1] + h * 0.70
    tie = box(b[0], tie_y - lw / 2, b[2], tie_y + lw / 2).intersection(sil)
    return unary_union([sil.difference(body_hollow), tie]).buffer(0)

def ore_v5(f=0.80):
    """Two clean peaks (v2 shapes) with a ridge line for depth; the ridge has a slight zag half-way down."""
    big = affinity.scale(Polygon([(-6.0, -10.0), (16.0, -10.0), (5.0, 13.5)]), f, f, origin=(0, 0))
    small = affinity.scale(Polygon([(-16.0, -10.0), (-1.5, -10.0), (-8.75, 4.0)]), f, f, origin=(0, 0)).difference(big.buffer(GAP * 1.2))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    big, small = soft(big, 0.5), soft(small, 0.4)
    ridge_b = LineString([(5.0 * f, 12.4 * f), (5.7 * f, 3.2 * f), (7.3 * f, 1.0 * f), (7.9 * f, -10.6 * f)]).buffer(0.42, cap_style=2, join_style=2)
    ridge_s = LineString([(-8.75 * f, 3.2 * f), (-8.3 * f, -2.6 * f), (-7.4 * f, -3.8 * f), (-7.1 * f, -10.6 * f)]).buffer(0.38, cap_style=2, join_style=2)
    g = printable(unary_union([big.difference(ridge_b), small.difference(ridge_s)]), w=0.6, speck=1.0)
    c = g.centroid
    return affinity.translate(g, -c.x, -(g.bounds[1] + g.bounds[3]) / 2)

def ore5_final():
    z = safe_zone()
    for f in np.arange(0.9, 0.6, -0.01):
        g = ore_v5(f)
        if z.contains(g) and closest(g) >= GAP - 0.01: return g, f

def road_edges(length, width):
    """Road seen from above: white edge lines, black tarmac, white dashed centre line."""
    e = max(0.9, width * 0.14); dw = max(0.8, width * 0.12)
    outer = rr(-length / 2, -width / 2, length / 2, width / 2, 0.3)
    tarmac = box(-length / 2 - 1, -width / 2 + e, length / 2 + 1, width / 2 - e)
    dl, dg = width * 0.55, width * 0.45; n = max(1, int((length - 1.2 * dg + dg) // (dl + dg))); tot = n * dl + (n - 1) * dg; x0 = -tot / 2   # dashes stay clear of the ends
    dashes = unary_union([box(x0 + k * (dl + dg), -dw / 2, x0 + k * (dl + dg) + dl, dw / 2) for k in range(n)])
    return unary_union([outer.difference(tarmac), dashes.intersection(outer)])

def road_perspective(length, w_near, w_far):
    """Road running into the distance: a white trapezoid with black centre dashes that shrink with distance."""
    body = Polygon([(-w_near / 2, -length / 2), (w_near / 2, -length / 2), (w_far / 2, length / 2), (-w_far / 2, length / 2)])
    body = body.buffer(0.3, join_style=1).buffer(-0.3, join_style=1)
    dashes = []; y = -length / 2 + length * 0.08
    for k in range(4):
        t = (y + length / 2) / length; wd = max(GAP, (w_near + (w_far - w_near) * t) * 0.14)
        dl = max(1.2, (w_near + (w_far - w_near) * t) * 0.55)
        dashes.append(box(-wd / 2, y, wd / 2, y + dl)); y += dl * 1.9
    return body.difference(unary_union(dashes).intersection(body.buffer(-0.9)))

def road_hammer_with(road_shape, angle_road=45):
    r = affinity.rotate(road_shape, angle_road, origin=(0, 0))
    hm = affinity.rotate(hammer2(24.0, 3.2), 45, origin=(0, 0))
    r = r.difference(hm.buffer(GAP, join_style=1))
    return centre(printable(unary_union([r, hm]), w=0.6, speck=1.0))

def money_bag2(height):
    """Coin purse: pear-shaped bag (wide bottom), pinched neck, a fuller ruffle on top."""
    h = height; w = h * 0.86
    base = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=48), w / 2, h * 0.30), 0, -h / 2 + h * 0.30)
    shoulder = Polygon([(-w * 0.46, -h * 0.22), (w * 0.46, -h * 0.22), (w * 0.16, h * 0.14), (-w * 0.16, h * 0.14)])
    neck = box(-w * 0.13, h * 0.10, w * 0.13, h * 0.22)
    ruff = Polygon([(-w * 0.13, h * 0.20), (-w * 0.36, h * 0.40), (-w * 0.18, h * 0.36), (-w * 0.10, h * 0.48),
                    (0, h * 0.38), (w * 0.10, h * 0.48), (w * 0.18, h * 0.36), (w * 0.36, h * 0.40), (w * 0.13, h * 0.20)])
    g = unary_union([base, shoulder, neck, ruff]).buffer(0.9, join_style=1).buffer(-0.9, join_style=1)
    return centre(g)

def bag_outline2(height, lw):
    sil = money_bag2(height); b = sil.bounds; h = b[3] - b[1]
    hollow = sil.buffer(-lw, join_style=1)
    body_hollow = max(pieces(hollow), key=lambda p: p.area)
    out = sil.difference(body_hollow)
    tie_y = b[1] + h * 0.655
    tie = box(b[0] - 1, tie_y - lw / 2, b[2] + 1, tie_y + lw / 2).intersection(sil.buffer(0.01))
    return printable(unary_union([out, tie]).buffer(0), w=0.6, speck=1.0)

def road_chain_edges(n, seg, width, angle=30):
    def build(L):
        x = y = 0; parts = []
        for k in range(n):
            a = angle if k % 2 == 0 else -angle
            c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a))
            parts.append(affinity.translate(affinity.rotate(road_edges(L, width), a, origin=(0, 0)), x + seg * c / 2, y + seg * s_ / 2))
            x, y = x + seg * c, y + seg * s_
        return parts
    lo, hi = seg * 0.3, seg
    for _ in range(30):
        L = (lo + hi) / 2; ps = build(L)
        d = min(unary_union(ps[i]).distance(unary_union(ps[i + 1])) for i in range(n - 1))
        (lo, hi) = (L, hi) if d >= GAP + 0.02 else (lo, L)
    return centre(unary_union(build(lo)))

def road_tile(length, width):
    """Small-size road: the same edge-line road but closed at both ends (an outlined segment with a centre dash)."""
    e = max(0.9, width * 0.15)
    outer = rr(-length / 2, -width / 2, length / 2, width / 2, min(0.8, width * 0.2))
    inner = outer.buffer(-e, join_style=2)
    dw = max(0.8, width * 0.14)
    dash = box(-length * 0.22, -dw / 2, length * 0.22, dw / 2)
    return unary_union([outer.difference(inner), dash.intersection(inner.buffer(-GAP))])

def road_chain_tiles(n, seg, width, angle=30):
    def build(L):
        x = y = 0; parts = []
        for k in range(n):
            a = angle if k % 2 == 0 else -angle
            c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a))
            parts.append(affinity.translate(affinity.rotate(road_tile(L, width), a, origin=(0, 0)), x + seg * c / 2, y + seg * s_ / 2))
            x, y = x + seg * c, y + seg * s_
        return parts
    lo, hi = seg * 0.3, seg
    for _ in range(30):
        L = (lo + hi) / 2; ps = build(L)
        d = min(ps[i].distance(ps[i + 1]) for i in range(n - 1))
        (lo, hi) = (L, hi) if d >= GAP + 0.02 else (lo, L)
    return centre(unary_union(build(lo)))

def winding_road(n, seg, width, angle=30):
    """One continuous road along n hex edges (zig-zag), drawn like road_edges: white edges, dashed centre line."""
    pts = [(0.0, 0.0)]
    for k in range(n):
        a = angle if k % 2 == 0 else -angle
        x, y = pts[-1]; pts.append((x + seg * np.cos(np.radians(a)), y + seg * np.sin(np.radians(a))))
    line = LineString(pts)
    e = max(0.9, width * 0.15); dw = max(0.8, width * 0.13)
    body = line.buffer(width / 2, cap_style=2, join_style=2, mitre_limit=3)
    tarmac = line.buffer(width / 2 - e, cap_style=2, join_style=2, mitre_limit=3).buffer(0)
    tarmac = unary_union([tarmac, LineString([pts[0], pts[1]]).buffer(width / 2 - e, cap_style=2), LineString([pts[-2], pts[-1]]).buffer(width / 2 - e, cap_style=2)])
    dashes = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2; ux, uy = (x1 - x0) / seg, (y1 - y0) / seg; dl = seg * 0.32
        dashes.append(LineString([(mx - ux * dl / 2, my - uy * dl / 2), (mx + ux * dl / 2, my + uy * dl / 2)]).buffer(dw / 2, cap_style=2))
    g = unary_union([body.difference(tarmac), unary_union(dashes)])
    return centre(printable(g, w=0.6, speck=0.5))

def road_piece():
    """Silhouette of the physical road piece (Building Costs shows the pieces you build as silhouettes)."""
    return rr(-4.6, -1.35, 4.6, 1.35, 0.5)

# ---------------------------------------------------------------- v2d
def ore_v6(f=0.80):
    """Two clean peaks with ridge lines; each ridge has its own, different kink."""
    big = affinity.scale(Polygon([(-6.0, -10.0), (16.0, -10.0), (5.0, 13.5)]), f, f, origin=(0, 0))
    small = affinity.scale(Polygon([(-16.0, -10.0), (-1.5, -10.0), (-8.75, 4.0)]), f, f, origin=(0, 0)).difference(big.buffer(GAP * 1.2))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    big, small = soft(big, 0.5), soft(small, 0.4)
    ridge_b = LineString([(5.0 * f, 12.4 * f), (5.7 * f, 3.2 * f), (7.3 * f, 1.0 * f), (7.9 * f, -10.6 * f)]).buffer(0.42, cap_style=2, join_style=2)
    ridge_s = LineString([(-8.75 * f, 3.0 * f), (-9.4 * f, -5.6 * f), (-8.5 * f, -6.6 * f), (-8.6 * f, -10.6 * f)]).buffer(0.38, cap_style=2, join_style=2)
    g = printable(unary_union([big.difference(ridge_b), small.difference(ridge_s)]), w=0.6, speck=1.0)
    c = g.centroid
    return affinity.translate(g, -c.x, -(g.bounds[1] + g.bounds[3]) / 2)

def ore6_final():
    z = safe_zone()
    for f in np.arange(0.9, 0.6, -0.01):
        g = ore_v6(f)
        if z.contains(g) and closest(g) >= GAP - 0.01: return g, f

def cobbles_along(pts, width, rows=2, stone_len=None):
    """Cobblestone road along a polyline: rounded stones laid in staggered rows, every stone >= 0.7 mm from the next."""
    line = LineString(pts); L = line.length
    sw = (width - GAP * (rows - 1)) / rows                     # stone width across the road
    sl = stone_len or sw * 1.45                                 # stone length along the road
    placed = []
    for r in range(rows):
        off = -width / 2 + sw / 2 + r * (sw + GAP)
        s = sl / 2 + (0 if r % 2 == 0 else (sl + GAP) / 2)
        while s <= L - sl / 2 + 1e-6:
            p = line.interpolate(s); q = line.interpolate(min(L, s + 0.01)); p0 = line.interpolate(max(0, s - 0.01))
            dx, dy = q.x - p0.x, q.y - p0.y; n = np.hypot(dx, dy); ux, uy = dx / n, dy / n
            c = (p.x - uy * off, p.y + ux * off)
            st = affinity.rotate(rr(-sl / 2, -sw / 2, sl / 2, sw / 2, min(sw, sl) * 0.32), np.degrees(np.arctan2(uy, ux)), origin=(0, 0))
            st = affinity.translate(st, *c)
            if all(st.distance(o) >= GAP for o in placed): placed.append(st)
            s += sl + GAP
        # the staggered row also gets a half stone at its start so the road edge is filled
        if r % 2 == 1:
            p = line.interpolate(sl * 0.3); q = line.interpolate(sl * 0.3 + 0.01); p0 = line.interpolate(max(0, sl * 0.3 - 0.01))
            dx, dy = q.x - p0.x, q.y - p0.y; n = np.hypot(dx, dy); ux, uy = dx / n, dy / n
            st = affinity.translate(affinity.rotate(rr(-sl * 0.3, -sw / 2, sl * 0.3, sw / 2, min(sw, sl) * 0.32), np.degrees(np.arctan2(uy, ux)), origin=(0, 0)), p.x - uy * off, p.y + ux * off)
            if all(st.distance(o) >= GAP for o in placed): placed.append(st)
    return unary_union(placed)

def cobble_road(length, width, rows=2):
    return cobbles_along([(-length / 2, 0), (length / 2, 0)], width, rows)

def cobble_winding(n, seg, width, angle=30, rows=2):
    pts = [(0.0, 0.0)]
    for k in range(n):
        a = angle if k % 2 == 0 else -angle
        x, y = pts[-1]; pts.append((x + seg * np.cos(np.radians(a)), y + seg * np.sin(np.radians(a))))
    return centre(cobbles_along(pts, width, rows))

def road_hammer_cobbles():
    r = affinity.rotate(cobble_road(27.0, 6.4, rows=3), 45, origin=(0, 0))
    hm = affinity.rotate(hammer2(24.0, 3.2), 45, origin=(0, 0))
    r = unary_union([p for p in pieces(r.difference(hm.buffer(GAP, join_style=1))) if p.area > 0.8])
    return centre(printable(unary_union([r, hm]), w=0.6, speck=1.0))

def coin_stack_outline(lw):
    """Coins in line style for the Building Costs back: a tall stack, a short stack beside it and one coin leaning on it.
    Each coin seen edge-on is a bar one line wide; the top coins show their faces as ovals."""
    cw, ch, gp = 10.0, lw, 0.85
    parts = []
    def stack(cx, n, w):
        y = -8.0
        for k in range(n):
            parts.append(rr(cx - w / 2, y, cx + w / 2, y + ch, ch * 0.45)); y += ch + gp
        top = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=32), w / 2, w * 0.2), cx, y + w * 0.2 - 0.2)
        parts.append(top.difference(top.buffer(-lw * 0.85)))
    stack(-2.2, 5, cw)
    stack(6.0, 2, cw * 0.78)
    lean = affinity.scale(Point(0, 0).buffer(1, quad_segs=32), 4.0, 1.7)
    lean = affinity.translate(affinity.rotate(lean.difference(lean.buffer(-lw * 0.85)), 62, origin=(0, 0)), -10.6, -4.2)
    parts.append(lean)
    g = unary_union(parts)
    return centre(printable(g, w=0.6, speck=0.5))

def cobbled_path(pts, width, stone=None):
    """Cobbled road: one solid path (keeps its shape) with black joint lines marking two staggered rows of stones."""
    line = LineString(pts); L = line.length
    body = line.buffer(width / 2, cap_style=2, join_style=2, mitre_limit=4)
    body = body.buffer(0.4, join_style=1).buffer(-0.4, join_style=1)
    sl = stone or width * 0.62
    joints = [line.buffer(GAP / 2, cap_style=2)]                     # centre joint between the two rows
    bends = [line.project(Point(p)) for p in pts[1:-1]]
    for side, start in ((1, sl * 0.5), (-1, sl)):
        s = start
        while s < L - sl * 0.45:
            if all(abs(s - b) > width * 0.45 for b in bends):
                p = line.interpolate(s); q = line.interpolate(min(L, s + 0.01)); p0 = line.interpolate(max(0, s - 0.01))
                dx, dy = q.x - p0.x, q.y - p0.y; n = np.hypot(dx, dy); nx, ny = -dy / n, dx / n
                joints.append(LineString([(p.x, p.y), (p.x + side * nx * width, p.y + side * ny * width)]).buffer(GAP / 2, cap_style=2))
            s += sl
    g = body.difference(unary_union(joints))
    return printable(g, w=0.6, speck=0.8)

def cobbled_winding(n, seg, width, angle=30):
    pts = [(0.0, 0.0)]
    for k in range(n):
        a = angle if k % 2 == 0 else -angle
        x, y = pts[-1]; pts.append((x + seg * np.cos(np.radians(a)), y + seg * np.sin(np.radians(a))))
    return centre(cobbled_path(pts, width))

def road_hammer_cobbled():
    r = affinity.rotate(cobbled_path([(-13.5, 0), (13.5, 0)], 6.6), 45, origin=(0, 0))
    hm = affinity.rotate(hammer2(24.0, 3.2), 45, origin=(0, 0))
    r = r.difference(hm.buffer(GAP, join_style=1))
    return centre(printable(unary_union([r, hm]), w=0.6, speck=1.0))

def coin_stacks_outline(lw):
    """Line-style coins for the Building Costs back: a tall stack and a shorter one beside it, each coin edge-on as a bar,
    the top of each stack showing the round coin face."""
    ch, gp = lw, 0.85
    parts = []
    def stack(cx, base, n, w):
        y = base
        for k in range(n):
            parts.append(rr(cx - w / 2, y, cx + w / 2, y + ch, ch * 0.48)); y += ch + gp
        ry = w * 0.26
        face = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=40), w / 2, ry), cx, y + ry - 0.15)
        parts.append(face.difference(face.buffer(-lw * 0.85)))
        return y + 2 * ry
    stack(-3.8, -8.0, 5, 9.6)
    stack(6.4, -8.0, 3, 7.8)
    g = unary_union(parts)
    return centre(printable(g, w=0.6, speck=0.5))

# ---------------------------------------------------------------- v2e
def cobbled_path2(pts, width, stone):
    """Cobbled road with joints everywhere, including through each bend (a joint along the bend's bisector)."""
    line = LineString(pts); L = line.length
    body = line.buffer(width / 2, cap_style=2, join_style=2, mitre_limit=4)
    joints = [line.buffer(GAP / 2, cap_style=2)]
    cum = [0.0]
    for a, b in zip(pts[:-1], pts[1:]): cum.append(cum[-1] + np.hypot(b[0] - a[0], b[1] - a[1]))
    for i in range(1, len(pts) - 1):                          # joint through each bend, along the bisector
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        u = np.array([x1 - x0, y1 - y0]); u /= np.linalg.norm(u); v = np.array([x2 - x1, y2 - y1]); v /= np.linalg.norm(v)
        bis = u + v; nrm = np.array([-bis[1], bis[0]]); nrm /= np.linalg.norm(nrm)
        joints.append(LineString([(x1 - nrm[0] * width, y1 - nrm[1] * width), (x1 + nrm[0] * width, y1 + nrm[1] * width)]).buffer(GAP / 2, cap_style=2))
    for i in range(len(pts) - 1):                             # stones along each straight run, staggered rows
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        seg = np.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / seg, (y1 - y0) / seg; nx, ny = -uy, ux
        for side, start in ((1, stone * 0.5), (-1, stone)):
            s = start
            while s < seg - stone * 0.35:
                if s > stone * 0.35:
                    px, py = x0 + ux * s, y0 + uy * s
                    joints.append(LineString([(px, py), (px + side * nx * width, py + side * ny * width)]).buffer(GAP / 2, cap_style=2))
                s += stone
    g = body.difference(unary_union(joints))
    return printable(g.buffer(0), w=0.6, speck=0.8)

def cobbled_winding2(n, seg, width, stone, angle=30):
    pts = [(0.0, 0.0)]
    for k in range(n):
        a = angle if k % 2 == 0 else -angle
        x, y = pts[-1]; pts.append((x + seg * np.cos(np.radians(a)), y + seg * np.sin(np.radians(a))))
    return centre(cobbled_path2(pts, width, stone))

def coin_stack(cx, base, n, w, lw, t):
    """One stack in line style: n coins, each a front edge (lower half-ellipse) t apart, with side lines,
    and the top coin's full face as an oval."""
    ry = w * 0.24
    parts = []
    top_y = base + (n - 1) * t
    face = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=48), w / 2, ry), cx, top_y + ry)
    parts.append(face.difference(face.buffer(-lw, join_style=1)))
    for k in range(n):
        y = base + k * t
        e = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=48), w / 2, ry), cx, y + ry)
        lower = e.difference(e.buffer(-lw)).intersection(box(cx - w, y - 1, cx + w, y + ry))
        parts.append(lower)
    parts.append(box(cx - w / 2, base + ry, cx - w / 2 + lw, top_y + ry))     # sides
    parts.append(box(cx + w / 2 - lw, base + ry, cx + w / 2, top_y + ry))
    return unary_union(parts)

def coin_stacks3(lw=1.2):
    """Three stacks: tallest in the middle, one side lower, the other lowest."""
    w = 6.4; t = lw + GAP + 0.15; gap_x = 1.2
    xs = (-(w + gap_x), 0.0, w + gap_x); ns = (4, 6, 3)
    g = unary_union([coin_stack(x, -6.0, n, w, lw, t) for x, n in zip(xs, ns)])
    return centre(printable(g.buffer(0), w=0.6, speck=0.5))

def trophy_open(height):
    """Large trophy: open handle loops (as v1) but the solid black star of the small trophies."""
    t = dev_icon('vp', height)
    ps = sorted(pieces(t), key=lambda p: -p.area)
    main = ps[0]                                      # dropping the small islands makes the star hole solid black
    g = Polygon(main.exterior, main.interiors).buffer(0)
    return centre(printable(g, w=0.6, speck=1.0))

def wheat_one_ear(k=1.25, rows=5):
    """A single large ear of wheat (centre ear of the v1 drawing, scaled up with gaps kept at 0.65 mm)."""
    pc = 3.28 * 6 / rows
    c, wc = I.ear(0.0, (16.2 * k, 11.4 * k), 2.0 * k, rows, 12.5 * k, 8.0 * k, 0.85, 4.75 * k, pc * k)
    stalk = stadium((0.0, 8.0 * k - (rows - 1) * pc * k - 1.6), (0.0, -17.2 * k + 3.5 * k), 1.3 * k)
    wheat_one_ear.w = wc
    return centre(unary_union(c + [stalk]))

def ore_mountains_plain(f=0.80):
    big = affinity.scale(Polygon([(-6.0, -10.0), (16.0, -10.0), (5.0, 13.5)]), f, f, origin=(0, 0))
    small = affinity.scale(Polygon([(-16.0, -10.0), (-1.5, -10.0), (-8.75, 4.0)]), f, f, origin=(0, 0)).difference(big.buffer(GAP * 1.2))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    big, small = soft(big, 0.5), soft(small, 0.4)
    ridge_b = LineString([(5.0 * f, 12.4 * f), (5.7 * f, 3.2 * f), (7.3 * f, 1.0 * f), (7.9 * f, -10.6 * f)]).buffer(0.42, cap_style=2, join_style=2)
    g = printable(unary_union([big.difference(ridge_b), small]), w=0.6, speck=1.0)
    c = g.centroid; return affinity.translate(g, -c.x, -(g.bounds[1] + g.bounds[3]) / 2)

def ore_rocks():
    """Hunks of ore: a big faceted rock and a smaller one beside it, black facet lines for the cut faces."""
    big = Polygon([(-5.5, -8.0), (8.5, -8.0), (11.0, -1.5), (6.5, 7.5), (-1.5, 9.0), (-7.5, 1.5)])
    small = Polygon([(-15.0, -8.0), (-7.0, -8.0), (-6.4, -3.0), (-9.5, 1.5), (-14.0, -1.0)]).difference(big.buffer(GAP * 1.2))
    facets_b = unary_union([LineString(p).buffer(0.4, cap_style=2, join_style=2) for p in
                            [[(-1.5, 9.0), (1.0, 1.0), (6.5, 7.5)], [(1.0, 1.0), (2.5, -8.2)], [(1.0, 1.0), (-7.5, 1.5)], [(1.0, 1.0), (11.0, -1.5)]]])
    facets_s = unary_union([LineString(p).buffer(0.38, cap_style=2, join_style=2) for p in [[(-9.5, 1.5), (-10.4, -3.0), (-6.4, -3.0)], [(-10.4, -3.0), (-11.2, -8.2)]]])
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    g = printable(unary_union([soft(big, 0.35).difference(facets_b), soft(small, 0.3).difference(facets_s)]), w=0.6, speck=1.0)
    c = g.centroid; return affinity.translate(g, -c.x, -(g.bounds[1] + g.bounds[3]) / 2)

def ingot(w, h, top):
    """One ingot seen from the front and slightly above: trapezoid front face + top face, black line between."""
    front = Polygon([(-w / 2, 0), (w / 2, 0), (w / 2 - h * 0.45, h), (-w / 2 + h * 0.45, h)])
    topf = Polygon([(-w / 2 + h * 0.45, h + GAP), (w / 2 - h * 0.45, h + GAP), (w / 2 - h * 0.45 - top * 0.6, h + GAP + top), (-w / 2 + h * 0.45 + top * 0.6, h + GAP + top)])
    return unary_union([front, topf]).buffer(0.25, join_style=1).buffer(-0.25, join_style=1)

def ore_ingots():
    w, h, top = 11.5, 4.2, 2.6
    a = place(ingot(w, h, top), -(w / 2 + 0.6), -8.0); b = place(ingot(w, h, top), w / 2 + 0.6, -8.0)
    c = place(ingot(w, h, top), 0, -8.0 + h + GAP + top + GAP)
    g = unary_union([a, b, c.difference(unary_union([a, b]).buffer(GAP))])
    return centre(printable(g, w=0.6, speck=1.0))


def wheat_ear_final():
    """Largest single ear that fits the safe zone as drawn (no shrinking), every gap >= 0.65 mm."""
    z = safe_zone()
    for k in np.arange(1.4, 0.8, -0.01):
        g = wheat_one_ear(k)
        if z.contains(g) and closest(g) >= 0.64: wheat_ear_final.k = k; return g

# ---------------------------------------------------------------- 3/4-view materials in the style of the wood card
def prism_stack(section, centres, length, ang=29.5, gap=GAP):
    """Same construction as the wood icon: an end face at each centre, and long bodies running back at `ang`
    from the top end and the bottom-right end (the bottom-left one stays an end only, like the wood).
    `section` is the end shape centred on (0,0)."""
    d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))]) * length
    ends = [place(section, *c) for c in centres]
    cut = unary_union([e.buffer(gap, join_style=2) for e in ends])
    def body(c):
        e = place(section, *c)
        return unary_union([e, place(e, *d)]).convex_hull.difference(cut)
    top, br = centres[0], centres[2]
    a = body(top); b = body(br)
    a = a.difference(b.buffer(gap, join_style=2))
    return centre(unary_union(ends + [a, b]))

def bricks3d(s=1.0):
    """Bricks laid flat, ends towards you: end = flat rectangle."""
    w, h = 6.2 * s, 3.6 * s
    sec = rr(-w / 2, -h / 2, w / 2, h / 2, 0.45)
    cs = [(-(w / 2 + GAP / 2) + (w + GAP) / 2 - (w + GAP) / 2 + 0.0, h + GAP), (-(w + GAP) / 2, 0.0), ((w + GAP) / 2, 0.0)]
    cs = [(0.0, h + GAP), (-(w + GAP) / 2, 0.0), ((w + GAP) / 2, 0.0)]           # top brick centred on the two below
    return prism_stack(sec, cs, 14.0 * s)

def ingots3d(s=1.0):
    """Ingots, ends towards you: end = trapezoid (narrow on top)."""
    wb, wt, h = 7.0 * s, 4.4 * s, 4.0 * s
    sec = Polygon([(-wb / 2, -h / 2), (wb / 2, -h / 2), (wt / 2, h / 2), (-wt / 2, h / 2)]).buffer(0.3, join_style=1).buffer(-0.3, join_style=1)
    cs = [(0.0, h + GAP), (-(wb + GAP) / 2, 0.0), ((wb + GAP) / 2, 0.0)]
    return prism_stack(sec, cs, 14.0 * s)

def wood3d_check(s=1.0):
    """The wood icon rebuilt with prism_stack (circles), to confirm the construction matches the real wood card."""
    r = 3.4 * s; sec = Point(0, 0).buffer(r, quad_segs=48)
    return prism_stack(sec, [(-5.85 * s + 5.85 * s - 4.0 * s + 4.0 * s, 6.8 * s), (-4.0 * s, 0.0), (4.0 * s, 0.0)], 14.6 * s)

def at_final(fn):
    """Largest version of fn(s) that fits the safe zone as drawn (gaps stay 0.7 mm)."""
    z = safe_zone()
    for s_ in np.arange(1.6, 0.5, -0.01):
        g = fn(s_)
        if z.contains(g) and closest(g) >= GAP - 0.01: return g, s_

# ---------------------------------------------------------------- resource set studies
def log_ends(s=1.0):
    """Flat front view of a log pile: 3-2-1 log ends, each with a black growth ring."""
    r = 3.0 * s; d = 2 * r + GAP; parts = []
    for row, n in enumerate((3, 2, 1)):
        for i in range(n):
            x = (i - (n - 1) / 2) * d; y = row * d * np.sqrt(3) / 2
            c = Point(x, y).buffer(r, quad_segs=48)
            ring = Point(x + r * 0.08, y + r * 0.05).buffer(r * 0.52, quad_segs=32)
            parts.append(c.difference(ring.difference(ring.buffer(-GAP))))
    return centre(unary_union(parts))

def wool_ball(s=1.0):
    """Ball of wool (3D): a sphere wrapped with yarn, black lines for the strands, a loose end trailing off."""
    R = 10.0 * s
    ball = Point(0, 0).buffer(R, quad_segs=64)
    strands = []
    for a, off, rx in ((25, -3.6, 1.0), (25, 0.6, 1.0), (25, 4.8, 0.9), (-55, -2.0, 0.95), (-55, 2.8, 0.9)):
        e = affinity.scale(Point(0, 0).buffer(1, quad_segs=64), R * rx, R * 0.42)
        arc = e.exterior.buffer(GAP / 2)
        strands.append(affinity.rotate(affinity.translate(arc, 0, off * s), a, origin=(0, 0)))
    yarn = unary_union(strands).intersection(ball.buffer(-1.2))
    tail = LineString([(R * 0.62, -R * 0.75), (R * 1.0, -R * 1.05), (R * 1.35, -R * 0.95)]).buffer(0.55 * s + 0.15, cap_style=1, join_style=1)
    tail = tail.difference(ball.buffer(GAP))
    return centre(printable(unary_union([ball.difference(yarn), tail]), w=0.6, speck=0.8))

def sheaf(s=1.0):
    """Wheat sheaf: three ears fanned out, their stalks tied with a band and spreading below it."""
    ears = []
    for ang, dx in ((-22, -1.2), (0, 0.0), (22, 1.2)):
        parts, w = I.ear(0.0, (13.0, 10.2), 1.5, 3, 9.6, 6.3, 0.7, 3.7, 2.9, gap=GAP)
        ear = unary_union(parts)
        ear = affinity.rotate(ear, ang, origin=(0, -2.0))
        ears.append(affinity.translate(ear, dx, 0))
    ears = unary_union(ears)
    band_y = -4.6
    stalks = unary_union([LineString([(0, -0.6), (x, -14.0)]).buffer(0.55, cap_style=2) for x in (-4.2, -2.1, 0, 2.1, 4.2)])
    stalks = stalks.difference(box(-6, band_y - 1.4, 6, band_y + 1.4).buffer(GAP))
    band = rr(-3.4, band_y - 1.2, 3.4, band_y + 1.2, 0.5)
    stalks = stalks.difference(ears.buffer(GAP))
    g = unary_union([ears, band, stalks]).buffer(0)
    return centre(affinity.scale(printable(g, w=0.6, speck=0.5), s, s, origin=(0, 0)))

def wool_ball2(s=1.0):
    """Ball of wool: curved parallel wraps from two directions (arcs of large circles centred off the ball)."""
    R = 10.0 * s; ball = Point(0, 0).buffer(R, quad_segs=64)
    lines = []
    for (cx, cy), radii in (((-17.0 * s, 9.0 * s), [13.5, 16.3, 19.1, 21.9]), ((15.0 * s, 12.0 * s), [12.0, 14.8, 17.6])):
        for r in radii:
            lines.append(Point(cx, cy).buffer(r * s, quad_segs=96).exterior.buffer(GAP / 2))
    g1 = unary_union(lines[:4]).intersection(ball.buffer(-1.0)).intersection(Point(-2.5 * s, -1.0 * s).buffer(R * 1.1))
    g2 = unary_union(lines[4:]).intersection(ball.buffer(-1.0)).difference(Point(-17.0 * s, 9.0 * s).buffer(18.0 * s))
    yarn = unary_union([g1, g2])
    tail = LineString([(R * 0.55, -R * 0.84), (R * 0.95, -R * 1.12), (R * 1.35, -R * 1.0)]).buffer(0.6 * s + 0.1, cap_style=1, join_style=1).difference(ball.buffer(GAP))
    return centre(printable(unary_union([ball.difference(yarn), tail]), w=0.6, speck=0.8))

def teardrop_ear(h, w, cuts):
    """A solid ear of wheat (pointed teardrop) with a few V-cuts marking the grains, kept to the upper part."""
    pts = []
    for t in np.linspace(0, np.pi, 40):
        y = h / 2 * np.cos(t); x = w / 2 * np.sin(t) * (0.55 + 0.45 * (1 - (y / (h / 2) + 1) / 2)) if False else w / 2 * np.sin(t) ** 1.25
        pts.append((x, y))
    right = pts; ear = Polygon(right + [(-x, y) for x, y in reversed(right)]).buffer(0)
    vs = []
    for i in range(cuts):
        ya = h / 2 - h * 0.30 - i * (h * 0.55 / max(1, cuts - 1) if cuts > 1 else 0)
        dx = w; dy = dx * 0.75
        vs.append(LineString([(-dx, ya + dy), (0, ya), (dx, ya + dy)]).buffer(GAP / 2, join_style=2))
    return ear.difference(unary_union(vs))

def sheaf2(s=1.0):
    ears = []
    for ang, dx, hh in ((-20, -1.4, 11.5), (0, 0.0, 13.0), (20, 1.4, 11.5)):
        e = teardrop_ear(hh, 5.2, 3)
        e = affinity.translate(e, 0, 4.0 + hh / 2)
        ears.append(affinity.translate(affinity.rotate(e, ang, origin=(0, 0)), dx, 0))
    ears_u = unary_union(ears)
    band_y = -1.6
    band = rr(-3.6, band_y - 1.2, 3.6, band_y + 1.2, 0.5)
    top_y = band_y - 1.2 - GAP; bot_y = -13.0
    fan = Polygon([(-3.2, top_y), (3.2, top_y), (5.6, bot_y), (-5.6, bot_y)]).buffer(0.3, join_style=1).buffer(-0.3, join_style=1)
    splits = unary_union([LineString([(x * 0.55, top_y + 1), (x, bot_y - 1)]).buffer(GAP / 2, cap_style=2) for x in (-3.4, -1.15, 1.15, 3.4)])
    stalks = fan.difference(splits)
    neck = Polygon([(-1.6, band_y + 1.2 + GAP), (1.6, band_y + 1.2 + GAP), (0.9, 3.4), (-0.9, 3.4)]).difference(ears_u.buffer(GAP))
    stalks = unary_union([stalks, neck])
    # ears touching each other: keep them apart
    e0, e1, e2 = ears
    e0 = e0.difference(e1.buffer(GAP)); e2 = e2.difference(e1.buffer(GAP))
    g = unary_union([e0, e1, e2, band, stalks]).buffer(0)
    return centre(affinity.scale(printable(g, w=0.6, speck=0.5), s, s, origin=(0, 0)))

def sheaf3(s=1.0):
    """Sheaf drawn at final size: shapes scale with s, gaps stay 0.7 mm."""
    ears = []
    for ang, dx, hh in ((-20, -1.4, 11.5), (0, 0.0, 13.0), (20, 1.4, 11.5)):
        e = teardrop_ear(hh * s, 5.2 * s, 3)
        e = affinity.translate(e, 0, 4.0 * s + hh * s / 2)
        ears.append(affinity.translate(affinity.rotate(e, ang, origin=(0, 0)), dx * s, 0))
    e0, e1, e2 = ears
    e0 = e0.difference(e1.buffer(GAP)); e2 = e2.difference(e1.buffer(GAP))
    ears_u = unary_union([e0, e1, e2])
    band_y = -1.6 * s
    band = rr(-3.6 * s, band_y - 1.2 * s, 3.6 * s, band_y + 1.2 * s, 0.5)
    top_y = band_y - 1.2 * s - GAP; bot_y = -13.0 * s
    fan = Polygon([(-3.2 * s, top_y), (3.2 * s, top_y), (5.6 * s, bot_y), (-5.6 * s, bot_y)]).buffer(0.3, join_style=1).buffer(-0.3, join_style=1)
    splits = unary_union([LineString([(x * 0.55 * s, top_y + 1), (x * s, bot_y - 1)]).buffer(GAP / 2, cap_style=2) for x in (-3.4, -1.15, 1.15, 3.4)])
    neck = Polygon([(-1.6 * s, band_y + 1.2 * s + GAP), (1.6 * s, band_y + 1.2 * s + GAP), (0.9 * s, 3.4 * s), (-0.9 * s, 3.4 * s)]).difference(ears_u.buffer(GAP))
    g = unary_union([ears_u, band, fan.difference(splits), neck]).buffer(0)
    return centre(printable(g, w=0.6, speck=0.5))

# ---------------------------------------------------------------- flat wood options
def log_ends3(s=1.0):
    """Three big log ends (2 below, 1 on top), each with a black bark ring and one growth ring."""
    r = 6.0 * s; d = 2 * r + GAP; parts = []
    for x, y in ((-d / 2, 0.0), (d / 2, 0.0), (0.0, d * np.sqrt(3) / 2)):
        c = Point(x, y).buffer(r, quad_segs=64)
        bark = c.difference(c.buffer(-max(0.9, r * 0.16))).difference(c.buffer(-max(0.9, r * 0.16) - GAP))
        bark_line = c.buffer(-max(0.9, r * 0.16)).difference(c.buffer(-max(0.9, r * 0.16) - GAP))
        ring = Point(x + r * 0.06, y + r * 0.04).buffer(r * 0.42, quad_segs=48)
        parts.append(c.difference(bark_line).difference(ring.difference(ring.buffer(-GAP))))
    return centre(unary_union(parts))

def pine_tree(s=1.0):
    """Pine tree: three stacked tiers with a black gap between them, and a trunk."""
    tiers = []
    for i, (w, y0, h) in enumerate(((22.0, -6.0, 9.5), (17.0, 0.2, 8.5), (11.5, 5.6, 8.0))):
        t = Polygon([(-w / 2 * s, y0 * s), (w / 2 * s, y0 * s), (0, (y0 + h) * s)]).buffer(0.5, join_style=1).buffer(-0.5, join_style=1)
        tiers.append(t)
    out = []
    for i, t in enumerate(tiers):
        above = unary_union(tiers[i + 1:]) if i + 1 < len(tiers) else Polygon()
        out.append(t.difference(above.buffer(GAP, join_style=1)) if not above.is_empty else t)
    trunk = rr(-1.8 * s, -12.0 * s, 1.8 * s, -6.0 * s - GAP, 0.3)
    return centre(unary_union(out + [trunk]))

def log_side(s=1.0):
    """One log seen side-on: long body, cut end on the left showing rings, a short branch stub on top."""
    L, R = 24.0 * s, 5.0 * s
    body = rr(-L / 2, -R, L / 2, R, R * 0.9)
    end = affinity.scale(Point(0, 0).buffer(1, quad_segs=48), R * 0.55, R)
    end = affinity.translate(end, -L / 2 + R * 0.55, 0)
    body = body.difference(end.buffer(GAP))
    ring = affinity.scale(Point(0, 0).buffer(1, quad_segs=48), R * 0.25, R * 0.48)
    ring = affinity.translate(ring, -L / 2 + R * 0.6, 0)
    end = end.difference(ring.difference(ring.buffer(-GAP)))
    stub = Polygon([(L * 0.12, R - 0.4), (L * 0.12 + 2.6 * s, R - 0.4), (L * 0.12 + 4.6 * s, R + 3.4 * s), (L * 0.12 + 2.4 * s, R + 3.4 * s)])
    grain = unary_union([LineString([(-L * 0.18, y), (L * 0.40, y)]).buffer(GAP / 2, cap_style=1) for y in (-R * 0.35, R * 0.25)])
    body = unary_union([body, stub]).difference(grain)
    return centre(printable(unary_union([body, end]), w=0.6, speck=0.5))

# ---------------------------------------------------------------- more flat wood options
def leafy_tree(s=1.0):
    """Broadleaf tree: round canopy made of overlapping circles, trunk below with a black gap."""
    c = unary_union([Point(x * s, y * s).buffer(r * s, quad_segs=48) for x, y, r in
                     ((0, 6.5, 7.2), (-6.0, 2.6, 5.4), (6.0, 2.6, 5.4), (-2.8, 0.4, 5.0), (2.8, 0.4, 5.0))])
    c = c.buffer(0.4, join_style=1).buffer(-0.4, join_style=1)
    trunk = Polygon([(-1.9 * s, -12.0 * s), (1.9 * s, -12.0 * s), (1.3 * s, -3.0 * s), (-1.3 * s, -3.0 * s)]).difference(c.buffer(GAP))
    return centre(unary_union([c, trunk]))

def stacked_logs_side(s=1.0):
    """Three logs seen side-on, two below and one on top: each with its cut end (growth ring) on the left."""
    def one(L, R):
        body = rr(-L / 2, -R, L / 2, R, R * 0.9)
        end = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=48), R * 0.55, R), -L / 2 + R * 0.55, 0)
        ring = affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=48), R * 0.25, R * 0.48), -L / 2 + R * 0.6, 0)
        return unary_union([body.difference(end.buffer(GAP)), end.difference(ring.difference(ring.buffer(-GAP)))])
    L, R = 22.0 * s, 3.4 * s
    a = place(one(L, R), 0, R + GAP / 2); b = place(one(L, R), 0, -(R + GAP / 2))
    c = place(one(L * 0.8, R), L * 0.05, 3 * R + GAP * 1.5)
    return centre(unary_union([a, b, c]))

def two_pines(s=1.0):
    """A small stand of forest: a tall pine with a shorter one behind it to the right."""
    big = place(pine_tree(1.0 * s), -3.2 * s, 0)
    small = place(pine_tree(0.72 * s), 6.8 * s, -4.2 * s)                  # built at its own size: gaps stay 0.7 mm
    return centre(unary_union([big, small.difference(big.buffer(GAP, join_style=1))]))

def to_weight(fn, target=270.0):
    """fn(s) scaled (shapes only, gaps stay 0.7 mm) to about `target` mm2 of colour, or the largest that fits the zone."""
    z = safe_zone(); best = None
    for s_ in np.arange(1.6, 0.5, -0.01):
        g = fn(s_)
        if not z.contains(g) or closest(g) < GAP - 0.01: continue
        best = g
        if g.area <= target: return g
    return best
