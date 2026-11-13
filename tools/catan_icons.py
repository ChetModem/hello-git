"""Icons measured from the perspective-corrected reference photo.

Coordinates are card-face millimetres with (0,0) at the card centre,
x to the right and y up, as seen when looking at the face.
"""
import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

GAP = 0.8


def px(x, y):  # helper used while measuring: grid image pixel -> mm
    return (x / 20 - 18, 20 - y / 20)


def ellipse(cx, cy, rx, ry, rot=0):
    e = affinity.scale(Point(0, 0).buffer(1, quad_segs=48), rx, ry)
    return affinity.translate(affinity.rotate(e, rot), cx, cy)


def ring(shape, w):
    return shape.buffer(w, quad_segs=24).difference(shape)


def rbox(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=12)


def stadium(a, b, w):
    return LineString([a, b]).buffer(w / 2, quad_segs=16)


def ear(cx, top_kernel, tk_w, rows, yt, yb, x_in, x_out, pitch, gap=0.65):
    """Ear measured by kernel edges: first pair's outer-top edge yt, inner-bottom edge yb,
    inner edge x_in and outer edge x_out (distances from the ear centre)."""
    w = 1.6
    for _ in range(20):  # kernel width that leaves `gap` between rows
        ang = np.arctan2(yt - yb - w, x_out - x_in - w)
        w = pitch * np.cos(ang) - gap
    parts = [stadium((cx, top_kernel[0]), (cx, top_kernel[1]), tk_w)]
    for i in range(rows):
        dy = -i * pitch
        for s in (-1, 1):
            a = (cx + s * (x_in + w / 2), yb + w / 2 + dy)
            b = (cx + s * (x_out - w / 2), yt - w / 2 + dy)
            parts.append(stadium(a, b, w))
    return parts, w


# Measured warp error of the two cards near the photo edges (card should be 54 x 80 mm):
# sheep came out 57.0 x 77.8, ore 53.2 x 81.5. Coordinates below are already corrected.
SHEEP_FIX = (54 / 57.0, 80 / 77.8)
ORE_FIX = (54 / 53.2, 80 / 81.5)


WHEAT_K = 0.686   # overall size; gaps between kernels stay at their printable width


def wheat(k=None):
    k = WHEAT_K if k is None else k
    parts = []
    c, wc = ear(0.0, (16.2 * k, 11.4 * k), 2.0 * k, 6, 12.5 * k, 8.0 * k, 0.45, 4.75 * k, 3.28 * k)
    parts += c + [stadium((0.0, -11.6 * k), (0.0, -17.2 * k), 1.2 * k)]
    for cx in (-10.4 * k, 10.4 * k):                      # side ears identical and evenly placed
        e, ws = ear(cx, (8.6 * k, 5.4 * k), 1.7 * k, 6, 6.1 * k, 2.8 * k, 0.4, 4.1 * k, 2.74 * k)
        parts += e + [stadium((cx, -13.6 * k), (cx, -17.2 * k), 1.1 * k)]
    wheat.kernel_widths = (wc, ws)
    return unary_union(parts)


def sheep():
    fx, fy = SHEEP_FIX
    # wool: 8 lobes, mirrored left/right
    raw = [px(*p) for p in [(360, 175), (205, 215), (515, 228), (142, 360), (580, 375), (200, 520), (520, 520), (360, 575)]]
    pairs = [(raw[1], raw[2]), (raw[3], raw[4]), (raw[5], raw[6])]
    lobes = [(0, raw[0][1]), (0, raw[7][1])]
    for l, r in pairs:
        x = (abs(l[0]) + abs(r[0])) / 2; y = (l[1] + r[1]) / 2
        lobes += [(-x, y), (x, y)]
    lobes = [Point(x * fx, y * fy).buffer(4.0 * fx, quad_segs=32) for x, y in lobes]
    body = unary_union(lobes + [ellipse(0, 0.8 * fy, 10.5 * fx, 9.5 * fy)])
    # round off the sharp V where neighbouring lobes meet (a nozzle can't reach into the point,
    # which left a black speck at each notch); 0.5 mm fillet radius
    body = body.buffer(0.5, quad_segs=24).buffer(-0.5, quad_segs=24)
    head = ellipse(0, -1.0 * fy, 5.25 * fx, 7.0 * fy)
    ears = [ellipse(s * 7.6 * fx, 2.9 * fy, 2.2 * fx, 1.22 * fy, -s * 14) for s in (-1, 1)]
    shape = body
    for part in [head] + ears:
        shape = shape.difference(ring(part, 1.0))
    # legs: identical, same length, bottoms level, placed symmetrically
    legs = unary_union([rbox(s * 4.3 * fx - 1.85 * fx, -16.0 * fy, s * 4.3 * fx + 1.85 * fx, -10.0 * fy, 1.4) for s in (-1, 1)])
    legs = legs.difference(body.buffer(GAP))
    return unary_union([shape, legs])


def wood():
    r = 3.4
    c1, c2, c3 = (-5.85, 0.0), (-9.85, -6.8), (-1.85, -6.8)   # three equal ends, bottom two level
    ends = [Point(*c).buffer(r, quad_segs=48) for c in (c1, c2, c3)]
    cut = unary_union([e.buffer(GAP) for e in ends])
    d = np.array([np.cos(np.radians(29.5)), np.sin(np.radians(29.5))]) * 14.6   # both logs parallel, same length
    a = stadium(c1, tuple(np.array(c1) + d), 2 * r).difference(cut)
    b = stadium(c3, tuple(np.array(c3) + d), 2 * r).difference(cut)
    a = a.difference(b.buffer(GAP))
    return unary_union(ends + [a, b])


def brick():
    rr = 0.9
    return unary_union([                           # symmetric about the card centre
        rbox(-8.0, 4.25, 8.0, 10.25, rr),
        rbox(-16.75, -3.0, -0.65, 3.0, rr),
        rbox(0.65, -3.0, 16.75, 3.0, rr),
        rbox(-8.0, -10.25, 8.0, -4.25, rr),
    ])


def ore():
    fx, fy = ORE_FIX
    base = -10.5 * fy                              # one shared, level baseline
    bl, br, top = -5.3 * fx, 15.4 * fx, 14.0 * fy
    big = Polygon([(bl, base), (br, base), ((bl + br) / 2, top)])            # apex centred over base
    sl, sr, stop = -17.0 * fx, -4.6 * fx, 1.4 * fy
    small = Polygon([(sl, base), (sr, base), ((sl + sr) / 2, stop)])
    small = small.difference(big.buffer(GAP))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    return unary_union([soft(big, 0.5), soft(small, 0.4)])


ICONS = {'wheat': wheat, 'sheep': sheep, 'wood': wood, 'brick': brick, 'ore': ore}
