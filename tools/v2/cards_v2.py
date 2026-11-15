"""v2 card faces and backs. Face view coordinates; back coordinates as seen from the back.
Each card: dict(face={slot: shape}, back=white shape, corners=slot or None)."""
import os, sys, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphs as G
import design_v1 as V1
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
SPD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WHITE, BRICK, WOOD, WHEAT, ORE, GREEN, PURPLE, ORANGE = 2, 3, 4, 5, 6, 7, 8, 9
CORNERS = [(-20, 32), (20, 32), (-20, -32), (20, -32)]
place, centre = G.place, G.centre

# ---------------------------------------------------------------- backs
RES_LOGO = pickle.load(open(os.path.join(SPD, 'logo.pkl'), 'rb'))
RING = max(RES_LOGO.geoms, key=lambda g: g.area) if hasattr(RES_LOGO, 'geoms') else RES_LOGO
LW = ((RING.bounds[2] - RING.bounds[0]) - (Polygon(RING.interiors[0]).bounds[2] - Polygon(RING.interiors[0]).bounds[0])) / 2

def ring_around(inner_ring, gap):
    """A second hex ring of the same line width, `gap` mm outside the given ring."""
    outer_edge = Polygon(inner_ring.exterior)
    a = outer_edge.buffer(gap, join_style=2); b = a.buffer(LW, join_style=2)
    return b.difference(a)

def back_resource(): return RES_LOGO
def back_dev():
    """Two rings: the resource ring plus one 2 mm outside it. Every development icon sits inside the inner ring."""
    return unary_union([RING, ring_around(RING, 2.0)])
def small_ring(cx, cy, h, lw=1.3):
    hx = G.hexagon(cx, cy, h * np.sqrt(3) / 2)
    return hx.difference(hx.buffer(-lw, join_style=2))
def badge_backs(inner):
    """Table cards: a small ring at the top and the bottom of the back (where their faces are empty),
    each holding an outline drawing; the bottom one is turned upside down so the back reads either way."""
    top = unary_union([small_ring(0, 30.5, 14.0), place(inner, 0, 30.5)])
    return unary_union([top, affinity.rotate(top, 180, origin=(0, 0))])
def outline_of(g, lw=1.1):
    f = unary_union([Polygon(p.exterior) for p in G.pieces(g)]).buffer(0)
    inside = f.buffer(-lw, join_style=1)
    keep = max(G.pieces(inside), key=lambda p: p.area) if not inside.is_empty else Polygon()
    return f.difference(keep)
def back_trophy():
    t = V1.dev_icon('vp', 7.4); return badge_backs(centre(outline_of(t, 0.9)))
def back_costs():
    return badge_backs(centre(outline_of(G.card(4.6, 6.4, False)[0].buffer(0), 0.9)))

# ---------------------------------------------------------------- helpers
def corners(slot): return unary_union([G.hexagon(x, y, 6.06) for x, y in CORNERS])
def merge(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items(): out[k] = unary_union([out[k], v]) if k in out else v
    return out
ZONE = G.safe_zone()

def fanned_cards(colours, w=8.6, h=12.0, spread=16.0, dx=5.0):
    """Cards fanned left to right (later ones in front). colours: list of hex slots (None = development card)."""
    n = len(colours); out = {}; prev = Polygon()
    shapes = []
    for i, col in enumerate(colours):
        a = spread * (i - (n - 1) / 2)
        body, hx = G.card(w, h, col is not None)
        body = affinity.rotate(affinity.translate(body, (i - (n - 1) / 2) * dx, 0), -a, origin=((i - (n - 1) / 2) * dx, -h * 0.9))
        if hx is not None: hx = affinity.rotate(affinity.translate(hx, (i - (n - 1) / 2) * dx, 0), -a, origin=((i - (n - 1) / 2) * dx, -h * 0.9))
        shapes.append((body, hx, col))
    for i, (body, hx, col) in enumerate(shapes):        # each card cut back where the cards in front of it sit
        front = unary_union([Polygon(s[0].exterior) for s in shapes[i + 1:]]) if i + 1 < n else Polygon()
        cut = front.buffer(G.GAP, join_style=1) if not front.is_empty else Polygon()
        out = merge(out, {WHITE: body.difference(cut)})
        if hx is not None: out = merge(out, {col: hx.difference(cut)})
    return out

# ---------------------------------------------------------------- development cards
def knight():
    g, k = G.fit_zone(G.helmet(31.0)); return {PURPLE: g}, PURPLE
def victory_point():
    t = V1.dev_icon('vp', 25.1); g, k = G.fit_zone(t); return {ORANGE: g}, ORANGE
def road_building():
    r = G.road(15.5, 5.4)
    a = place(affinity.rotate(r, 60, origin=(0, 0)), -2.6, 6.6); b = place(affinity.rotate(r, -60, origin=(0, 0)), -2.6, -6.6)
    g = unary_union([a, b]); g = centre(g)
    z, k = G.fill_zone(g); return {WHITE: z}, GREEN
def year_of_plenty():
    f = fanned_cards([BRICK, WHEAT], w=11.0, h=15.4, spread=14.0, dx=6.4)
    allg = unary_union(list(f.values())); b = allg.bounds
    f = {k: place(v, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2) for k, v in f.items()}
    _, s_ = G.fill_zone(unary_union(list(f.values())))
    return {k: affinity.scale(v, s_, s_, origin=(0, 0)) for k, v in f.items()}, GREEN
def monopoly():
    cr = G.crown(14.0)
    f = fanned_cards([ORE, ORE, ORE], w=8.4, h=11.8, spread=16.0, dx=4.6)
    fb = unary_union(list(f.values())).bounds
    f = {k: place(v, -(fb[0] + fb[2]) / 2, -6.2 - (fb[1] + fb[3]) / 2) for k, v in f.items()}
    cr = place(cr, 0, 8.6)
    out = merge(f, {WHITE: cr})
    allg = unary_union(list(out.values())); b = allg.bounds
    out = {s: place(v, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2) for s, v in out.items()}
    _, k = G.fill_zone(unary_union(list(out.values())))
    out = {s: G.printable(affinity.scale(v, k, k, origin=(0, 0)), w=0.6, speck=0.5) for s, v in out.items()}
    out[WHITE] = out[WHITE].buffer(0.2, join_style=1).buffer(-0.2, join_style=1)     # seal hairline cracks (< 0.4 mm)
    return out, GREEN

# ---------------------------------------------------------------- table cards
TROPHY_Y, TROPHY_H = -14.0, 9.5
def trophies():
    t = V1.dev_icon('vp', TROPHY_H).buffer(0.3, join_style=2, mitre_limit=10).buffer(-0.3, join_style=2, mitre_limit=10)
    w = t.bounds[2] - t.bounds[0]
    return unary_union([place(t, -(w / 2 + 1.6), TROPHY_Y), place(t, w / 2 + 1.6, TROPHY_Y)])
def longest_road():
    chain = G.road_chain(5, 9.0, 3.0)
    return {WHITE: place(chain, 0, 6.0), ORANGE: trophies()}, ORANGE
def largest_army():
    big = G.helmet(22.0); small = G.helmet(15.5); base = -6.0; gap = 1.4
    wb = big.bounds[2] - big.bounds[0]; ws = small.bounds[2] - small.bounds[0]
    h = unary_union([place(big, 0, base - big.bounds[1])] + [place(small, sd * (wb / 2 + gap + ws / 2), base - small.bounds[1]) for sd in (-1, 1)])
    return {PURPLE: h, ORANGE: trophies()}, ORANGE
def building_costs():
    rows = [('road', ['brick', 'wood']), ('settlement', ['brick', 'wood', 'wheat', 'sheep']),
            ('city', ['ore', 'ore', 'ore', 'wheat', 'wheat']), ('dev', ['ore', 'wheat', 'sheep'])]
    slot = {'brick': BRICK, 'wood': WOOD, 'wheat': WHEAT, 'sheep': WHITE, 'ore': ORE}
    piece = {'road': affinity.rotate(G.road(9.0, 2.8), 30, origin=(0, 0)),
             'settlement': affinity.scale(V1.p_settlement(), 1.25, 1.25, origin=(0, 0)),
             'city': affinity.scale(V1.p_city(), 1.25, 1.25, origin=(0, 0)),
             'dev': G.card(6.0, 8.4, False)[0]}
    out = {}
    for i, (p, res) in enumerate(rows):
        y = 21.0 - i * 14.0
        g = piece[p]; b = g.bounds; out = merge(out, {WHITE: place(g, -18.6 - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2)})
        x = -13.0
        for r in res:
            out = merge(out, {slot[r]: place(V1.hexagon(0, 0, 6.5).buffer(0.25, join_style=1).buffer(-0.25, join_style=1), x + 3.25, y)}); x += 7.5
    return out, None

# ---------------------------------------------------------------- resource cards (v2 options for wheat and ore)
import icons2 as I
def wheat_card(option):
    if option == 'v1': g = centre(I.wheat())
    elif option == 'r4': g = centre(G.wheat_v2(0.67, 4))
    else: g = centre(G.wheat_v2(0.67, 3))
    return {WHEAT: g}, WHEAT
def ore_card():
    g, f = G.ore_final(); return {ORE: g}, ORE

CARDS = {
    'Knight': (knight, back_dev), 'Victory Point': (victory_point, back_dev), 'Road Building': (road_building, back_dev),
    'Year of Plenty': (year_of_plenty, back_dev), 'Monopoly': (monopoly, back_dev),
    'Building Costs': (building_costs, back_costs), 'Longest Road': (longest_road, back_trophy), 'Largest Army': (largest_army, back_trophy),
    'Ore': (ore_card, back_resource),
}
def build(name):
    f, back = CARDS[name]
    face, corner = f()
    if corner is not None: face = merge(face, {corner: corners(corner)})
    return face, back(), corner
