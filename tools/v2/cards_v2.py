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

V1_DEV_BACK = pickle.load(open(os.path.join(SPD, 'dev_shapes.pkl'), 'rb'))['knight']['logo']
def back_resource(): return RES_LOGO
def back_dev_v1(): return V1_DEV_BACK
def back_costs_v1():
    """Building Costs back: the hex ring with three coin stacks inside (same family as the trophy back)."""
    return unary_union([RES_LOGO, G.coin_stacks3(1.2)]).buffer(0)
def back_trophy_v1():
    """The original Longest Road / Largest Army back (hex ring + trophy outline), traced from the v2 trophy."""
    t = G.trophy(17.5)
    sil = Polygon(max(G.pieces(t), key=lambda p: p.area).exterior)
    inside = sil.buffer(-LW, join_style=1)
    cup = max(G.pieces(inside), key=lambda p: p.area)
    return unary_union([RES_LOGO, centre(sil.difference(cup))]).buffer(0)
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
G.GAP = G.LINE          # v2 final pass: every card uses the resource set's 0.8 mm lines and gaps

def fanned_cards(colours, w=8.6, h=12.0, spread=16.0, dx=5.0, hy=0.0, blocker=None):
    """Cards fanned left to right (later ones in front), drawn like every card in the set: white card, solid black
    hexagon. A hexagon is only cut where all of it shows; a card whose hexagon would be covered stays plain white."""
    n = len(colours); shapes = []
    for i in range(n):
        a = spread * (i - (n - 1) / 2); ox = (i - (n - 1) / 2) * dx; org = (ox, -h * 0.9)
        body = affinity.rotate(affinity.translate(G.rr(-w / 2, -h / 2, w / 2, h / 2, min(0.9, w * 0.12)), ox, 0), -a, origin=org)
        hx = affinity.rotate(affinity.translate(G.hexagon(0, hy, w * 0.52), ox, 0), -a, origin=org)
        shapes.append((body, hx))
    out = Polygon()
    for i, (body, hx) in enumerate(shapes):
        front = unary_union([s_[0] for s_ in shapes[i + 1:]]) if i + 1 < n else Polygon()
        if blocker is not None: front = unary_union([front, blocker])
        cut = front.buffer(G.GAP, join_style=1) if not front.is_empty else Polygon()
        vis = body.difference(cut)
        if hx.buffer(G.GAP).within(vis): vis = vis.difference(hx)
        out = unary_union([out, vis])
    return {WHITE: out}

# ---------------------------------------------------------------- development cards
def knight():
    """Helmet sized to about the same weight as the other icons (it was the heaviest by ~20%)."""
    for h in np.arange(31.0, 18.0, -0.2):
        g, k = G.fit_zone(G.helmet(h))
        if g.area <= KNIGHT_WEIGHT: return {PURPLE: g}, PURPLE
VP_WEIGHT = 285.0
def victory_point():
    """The one trophy (solid handles, black star), sized by weight like the resource icons."""
    for hgt in np.arange(26.0, 15.0, -0.2):
        g = G.trophy(hgt)
        if g.area <= VP_WEIGHT and ZONE.contains(g): return {ORANGE: g}, ORANGE
def road_building():
    """Road (same stones as Longest Road) crossed with a hammer, built at final size."""
    for k in np.arange(1.2, 0.6, -0.01):
        g = G.road_hammer3(k)
        if ZONE.contains(g): return {WHITE: g}, GREEN
def year_of_plenty():
    """Same card size as Monopoly's (built at final size)."""
    monopoly(); s_ = yop_card_scale() * monopoly.scale_note
    f = fanned_cards([None, None], w=11.0 * s_, h=15.4 * s_, spread=14.0, dx=YOP_DX * s_)
    allg = unary_union(list(f.values())); b = allg.bounds
    return {k: place(v, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2) for k, v in f.items()}, GREEN
def yop_card_scale():
    f = fanned_cards([None, None], w=11.0, h=15.4, spread=14.0, dx=YOP_DX)
    allg = unary_union(list(f.values())); _, s_ = G.fill_zone(allg); return s_
YOP_DX = 7.4                     # far enough apart that both solid hexagons show whole
MONO_OVERLAP = 0.45
def monopoly_at(s_):
    w, h = 11.0 * s_, 15.4 * s_
    plain = fanned_cards([None, None, None], w=w, h=h, spread=12.0, dx=3.2 * s_)[WHITE]
    cb = plain.bounds
    cr = G.crown3(w * 1.35); crb = cr.bounds
    ov = MONO_OVERLAP * (crb[3] - crb[1])
    cr = place(cr, (cb[0] + cb[2]) / 2 - (crb[0] + crb[2]) / 2, cb[3] - ov - crb[1])        # crown resting on the fan
    hull = cr.convex_hull
    cards = fanned_cards([None, None, None], w=w, h=h, spread=12.0, dx=3.2 * s_, hy=-h * 0.17, blocker=hull)[WHITE]
    cards = unary_union([p for p in G.pieces(cards) if p.area > 2.0])
    g = unary_union([cards, cr]); b = g.bounds
    return place(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
def monopoly():
    """Built at its final size (no shrinking afterwards, so the 0.8 mm lines and gaps stay 0.8 mm)."""
    yop = yop_card_scale(); s_ = yop
    while s_ > 0.4 and not ZONE.contains(monopoly_at(s_)): s_ -= 0.01
    monopoly.scale_note = s_ / yop
    return {WHITE: G.printable(monopoly_at(s_), w=0.6, speck=0.8)}, GREEN

# ---------------------------------------------------------------- table cards
TROPHY_H, TABLE_GAP = 12.5, 4.0
def trophies():
    t = G.trophy(TROPHY_H)
    w = t.bounds[2] - t.bounds[0]
    return unary_union([place(t, -(w / 2 + 1.6), 0), place(t, w / 2 + 1.6, 0)])
def table_layout(top_slot, top):
    """Table cards: the card's picture, TABLE_GAP above the pair of trophies, the whole group centred on the card."""
    tr = trophies(); tb = tr.bounds; t = G.centre(top)
    t = place(t, 0, tb[3] + TABLE_GAP - t.bounds[1])
    allg = unary_union([t, tr]); b = allg.bounds; dy = -(b[1] + b[3]) / 2
    return {top_slot: place(t, 0, dy), ORANGE: place(tr, 0, dy)}, ORANGE
def longest_road():
    return table_layout(WHITE, G.longest_road3(4, 10.6))
def largest_army():
    big = G.helmet(22.0); small = G.helmet(15.5); gap = 1.4
    wb = big.bounds[2] - big.bounds[0]; ws = small.bounds[2] - small.bounds[0]
    h = unary_union([place(big, 0, -big.bounds[1])] + [place(small, sd * (wb / 2 + gap + ws / 2), -small.bounds[1]) for sd in (-1, 1)])
    return table_layout(PURPLE, h)
def building_costs():
    """Rows: piece on the left, one hexagon per resource card it costs (the layout you preferred)."""
    rows = [('road', ['brick', 'wood']), ('settlement', ['brick', 'wood', 'wheat', 'sheep']),
            ('city', ['ore', 'ore', 'ore', 'wheat', 'wheat']), ('dev', ['ore', 'wheat', 'sheep'])]
    slot = {'brick': BRICK, 'wood': WOOD, 'wheat': WHEAT, 'sheep': WHITE, 'ore': ORE}
    piece = {'road': affinity.rotate(G.road_piece(), 30, origin=(0, 0)),
             'settlement': affinity.scale(V1.p_settlement(), 1.25, 1.25, origin=(0, 0)),
             'city': affinity.scale(V1.p_city(), 1.25, 1.25, origin=(0, 0)),
             'dev': G.card_solid(6.0, 8.4)}
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
def ore_card(opt='plain'):
    if opt == 'plain': g = G.fit_zone(G.ore_mountains_plain(1.0))[0]
    elif opt == 'rocks': g = G.fit_zone(G.ore_rocks())[0]
    else: g = G.at_final(G.ingots3d)[0]
    return {ORE: g}, ORE

RES_ICONS = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resource_icons_v2.pkl'), 'rb'))   # locked set
RES_SLOT = {'brick': BRICK, 'wood': WOOD, 'sheep': WHITE, 'wheat': WHEAT, 'ore': ORE}
def resource(n): return lambda: ({RES_SLOT[n]: RES_ICONS[n]}, RES_SLOT[n])
CARDS = {
    'Brick': (resource('brick'), back_resource), 'Wood': (resource('wood'), back_resource), 'Sheep': (resource('sheep'), back_resource),
    'Wheat': (resource('wheat'), back_resource), 'Ore': (resource('ore'), back_resource),
    'Knight': (knight, back_dev_v1), 'Victory Point': (victory_point, back_dev_v1), 'Road Building': (road_building, back_dev_v1),
    'Year of Plenty': (year_of_plenty, back_dev_v1), 'Monopoly': (monopoly, back_dev_v1),
    'Building Costs': (building_costs, back_costs_v1), 'Longest Road': (longest_road, back_trophy_v1), 'Largest Army': (largest_army, back_trophy_v1),
}
SINGLE_ICON = {'Knight', 'Victory Point', 'Road Building', 'Year of Plenty', 'Monopoly'}
KNIGHT_WEIGHT = 300.0
TALL_LINE, WIDE_LINE = RES_ICONS['wood'].bounds[1], RES_ICONS['brick'].bounds[1]
SPECK = {}
def finish(name, face):
    """Same finishing rules as the resource set: 0.3 mm rounded tips, no specks under 2 mm2,
    single development icons centred on their weight (like the resource icons)."""
    out = {}
    for k, v in face.items():
        v = G.soften(v, 0.3)
        out[k] = unary_union([p for p in G.pieces(v) if p.area >= SPECK.get(name, 2.0)])
    if name in SINGLE_ICON:          # the resource placement rule
        allg = unary_union(list(out.values())); b = allg.bounds; hgt = b[3] - b[1]
        if hgt >= 24.5: dy = TALL_LINE - b[1]          # tall icons stand on the tall line
        elif hgt <= 18.0: dy = WIDE_LINE - b[1]        # low wide icons on the wide line
        else: dy = -(b[1] + b[3]) / 2                  # in between: centred
        out = {k: affinity.translate(v, 0, dy) for k, v in out.items()}
    return out
def build(name):
    f, back = CARDS[name]
    face, corner = f()
    if name not in ('Brick', 'Wood', 'Sheep', 'Wheat', 'Ore'): face = finish(name, face)
    if corner is not None: face = merge(face, {corner: corners(corner)})
    return face, back(), corner
