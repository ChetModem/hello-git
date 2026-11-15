"""Small versions of the real resource-card icons, with gaps re-opened to stay printable."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import icons2 as I
from shapely.ops import unary_union
from shapely import affinity
GAP = 0.7

def pieces(g): return [p for p in (g.geoms if hasattr(g, 'geoms') else [g]) if not p.is_empty]

def regap(g, gap=GAP):
    """Shrink each separate piece just enough that every pair is at least `gap` apart."""
    ps = pieces(g)
    for _ in range(6):
        md = min([a.distance(b) for i, a in enumerate(ps) for b in ps[i + 1:]] or [9])
        if md >= gap - 1e-3: break
        e = (gap - md) / 2 + 0.005
        ps = [p.buffer(-e, join_style=1) for p in ps]; ps = [q for p in ps for q in pieces(p) if q.area > 0.3]
    return unary_union(ps)

def fit(g, size):
    b = g.bounds; k = size / max(b[2] - b[0], b[3] - b[1])
    g = affinity.scale(g, k, k, origin=(0, 0)); b = g.bounds
    return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)

def clean(g, w=0.6):
    g = g.buffer(-w / 2, join_style=1).buffer(w / 2, join_style=1)
    return unary_union([p for p in pieces(g) if p.area > 0.3])

def sheep_mini(size):
    """The card's sheep, rebuilt so the black ring round the head and ears and the gap above the legs
    come out 0.7 mm at the final size (shrinking the finished card icon would close them up)."""
    k = size / 26.0                           # card sheep is about 26 mm tall
    for _ in range(4):
        fx, fy = I.SHEEP_FIX; px = I.px
        raw = [px(*p) for p in [(360, 175), (205, 215), (515, 228), (142, 360), (580, 375), (200, 520), (520, 520), (360, 575)]]
        pairs = [(raw[1], raw[2]), (raw[3], raw[4]), (raw[5], raw[6])]
        lobes = [(0, raw[0][1]), (0, raw[7][1])]
        for l, r in pairs:
            x = (abs(l[0]) + abs(r[0])) / 2; y = (l[1] + r[1]) / 2; lobes += [(-x, y), (x, y)]
        from shapely.geometry import Point
        lobes = [Point(x * fx, y * fy).buffer(4.0 * fx, quad_segs=32) for x, y in lobes]
        body = unary_union(lobes + [I.ellipse(0, 0.8 * fy, 10.5 * fx, 9.5 * fy)])
        body = body.buffer(0.5, quad_segs=24).buffer(-0.5, quad_segs=24)
        head = I.ellipse(0, -1.0 * fy, 5.25 * fx, 7.0 * fy)
        ears = [I.ellipse(s * 7.6 * fx, 2.9 * fy, 2.2 * fx, 1.22 * fy, -s * 14) for s in (-1, 1)]
        shape = body
        for part in [head] + ears: shape = shape.difference(part.buffer(GAP / k))
        legs = unary_union([I.rbox(s * 4.3 * fx - 1.85 * fx, -16.0 * fy, s * 4.3 * fx + 1.85 * fx, -10.0 * fy, 1.4) for s in (-1, 1)])
        legs = legs.difference(body.buffer(GAP / k))
        g = unary_union([shape, head] + ears + [legs])
        b = g.bounds; k2 = size / max(b[2] - b[0], b[3] - b[1])
        if abs(k2 - k) < 1e-3: break
        k = k2
    return clean(fit(g, size))

def mini(name, size):
    if name == 'wheat': return wheat_ear(size)
    if name == 'sheep':
        import design as D
        g = D.m_sheep(); b = g.bounds; k = size / max(b[2] - b[0], b[3] - b[1])
        g = affinity.scale(g, k, k, origin=(0, 0)); b = g.bounds      # k > 1: its 0.7 mm gaps only get wider
        return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
    return clean(regap(fit(I.ICONS[name](), size)))

def wheat_ear(size):
    """One ear in the style of the card's wheat, drawn at final size (no scaling, so gaps stay 0.7 mm):
    top grain, two chevron pairs of grains, and a stalk."""
    parts, w = I.ear(0.0, (4.6, 3.3), 1.35, 2, 2.6, 0.5, 0.3, 2.35, 3.0, gap=GAP)
    wheat_ear.grain_width = w
    parts.append(I.stadium((0.0, -3.4), (0.0, -4.9), 1.3))
    g = regap(unary_union(parts)); b = g.bounds          # stalk / top grain also kept 0.7 mm clear
    k = max(1.0, size * 1.1 / (b[3] - b[1]))               # only ever scaled up, so gaps never shrink
    g = affinity.scale(g, k, k, origin=(0, 0)); b = g.bounds
    return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
