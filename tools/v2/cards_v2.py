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
BACK_LINES = 'even'               # 'original' or 'even' (inner drawings at the ring's line weight)
def even_lines(drawing, now):
    """Thicken / thin a line drawing evenly on both sides so its strokes match the ring's LW."""
    d = (LW - now) / 2
    return drawing.buffer(d, join_style=2, mitre_limit=3) if d > 0 else drawing.buffer(d, join_style=2, mitre_limit=3).buffer(0)
def back_parts(full):
    inner = full.difference(RES_LOGO.buffer(0.05)); return unary_union([p for p in G.pieces(inner) if p.area > 0.5])
def with_even(full, now):
    if BACK_LINES != 'even': return full
    return unary_union([RES_LOGO, even_lines(back_parts(full), now)]).buffer(0)
COIN_LW = 1.35                    # coins a touch lighter so the thick lines don't crowd the gaps between coins
def back_dev_v1(): return with_even(V1_DEV_BACK, 1.23)
def back_costs_v1():
    """Building Costs back: the hex ring with three coin stacks inside (same family as the trophy back)."""
    if BACK_LINES == 'even': return unary_union([RES_LOGO, G.coin_stacks3(COIN_LW)]).buffer(0)
    return unary_union([RES_LOGO, G.coin_stacks3(1.2)]).buffer(0)
def back_trophy_v1():
    """The original Longest Road / Largest Army back (hex ring + trophy outline), traced from the v2 trophy."""
    t = G.trophy(17.5)
    sil = Polygon(max(G.pieces(t), key=lambda p: p.area).exterior)
    inside = sil.buffer(-LW, join_style=1)
    cup = max(G.pieces(inside), key=lambda p: p.area)
    return with_even(unary_union([RES_LOGO, centre(sil.difference(cup))]).buffer(0), 1.82)
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

def fanned_cards(colours, w=8.6, h=12.0, spread=16.0, dx=5.0, hy=0.0, blocker=None, hx0=0.0, hr=0.52, mark=None):
    """Cards fanned left to right (later ones in front), drawn like every card in the set: white card, solid black
    hexagon. A hexagon is only cut where all of it shows; a card whose hexagon would be covered stays plain white."""
    n = len(colours); shapes = []
    for i in range(n):
        a = spread * (i - (n - 1) / 2); ox = (i - (n - 1) / 2) * dx; org = (ox, -h * 0.9)
        body = affinity.rotate(affinity.translate(G.rr(-w / 2, -h / 2, w / 2, h / 2, min(0.9, w * 0.12)), ox, 0), -a, origin=org)
        m0 = mark(w) if mark is not None else G.hexagon(hx0, hy, w * hr)
        hx = affinity.rotate(affinity.translate(m0, ox, 0), -a, origin=org)
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
VP_FIT = 'after'                  # 'before': sized to the ring, then moved to the tall line; 'after': sized where it stands
def victory_point(fit=None):
    """The one trophy (solid handles, black star), sized by weight like the resource icons."""
    fit = fit or VP_FIT
    for hgt in np.arange(26.0, 15.0, -0.2):
        g = G.trophy(hgt)
        if fit == 'after': g = place(g, 0, TALL_LINE - g.bounds[1])
        if g.area <= VP_WEIGHT and ZONE.contains(g): return {ORANGE: g}, ORANGE
def road_building():
    """Road (same stones as Longest Road) crossed with a hammer, built at final size."""
    for k in np.arange(1.2, 0.6, -0.01):
        g = G.road_tool6(k, 'hammer')
        if ZONE.contains(place(g, 0, -g.centroid.y)): return {WHITE: g}, GREEN     # sized where it stands (centred on its weight)
CARD_W, CARD_H = 11.0, 15.4      # the card drawing's proportions (scaled by s_)
FAN_EXTRA = 1.2                  # fixed extra spacing in a fan: the 0.8 mm gaps do not shrink with the drawing
YOP_DX = 7.4                     # Year of Plenty card spacing (scaled), as before
CROWN_W, CROWN_GAP = 1.7, 1.4
def monopoly_at(s_):
    """Crown just above a fan of three cards, every card showing its centre hexagon."""
    w, h = CARD_W * s_, CARD_H * s_
    cards = fanned_cards([None] * 3, w=w, h=h, spread=14.0, dx=7.4 * s_ + FAN_EXTRA)[WHITE]; cb = cards.bounds
    cr = G.crown4(w * CROWN_W, 0.9); crb = cr.bounds
    cr = place(cr, (cb[0] + cb[2]) / 2 - (crb[0] + crb[2]) / 2, cb[3] + CROWN_GAP - crb[1])
    g = unary_union([cards, cr]); b = g.bounds
    return place(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
MONO_WEIGHT = 290.0
def monopoly_scale():
    for s_ in np.arange(1.6, 0.4, -0.01):
        g = monopoly_at(s_)
        if ZONE.contains(g) and g.area <= MONO_WEIGHT: return s_
def monopoly():
    """Built at its final size (no shrinking afterwards, so the 0.8 mm lines and gaps stay 0.8 mm)."""
    return {WHITE: monopoly_at(monopoly_scale())}, GREEN
YOP_WEIGHT = 270.0
def year_of_plenty_at(s_):
    f = fanned_cards([None, None], w=CARD_W * s_, h=CARD_H * s_, spread=14.0, dx=YOP_DX * s_ + FAN_EXTRA)[WHITE]
    b = f.bounds; return place(f, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
def year_of_plenty():
    """Two cards, each with its whole centre hexagon, sized by weight like every other icon
    (matching Monopoly's card size would leave it at ~106 mm2: Monopoly's three-card fan has to be small to fit)."""
    for s_ in np.arange(1.6, 0.4, -0.01):
        g = year_of_plenty_at(s_)
        if ZONE.contains(g) and g.area <= YOP_WEIGHT: return {WHITE: g}, GREEN

# ---------------------------------------------------------------- table cards
TROPHY_H, TABLE_GAP = 12.5, 4.0
LR_SEED = 4
LR_DIP = {2: dict(up=0.0, lo=0.5, lo_pre=0.55, up_pre=0.0)}
LR_NUDGE = {(2, 1, 0): 0.2}
def trophies():
    t = G.trophy(TROPHY_H)
    w = t.bounds[2] - t.bounds[0]
    return unary_union([place(t, -(w / 2 + 1.6), 0), place(t, w / 2 + 1.6, 0)])
TROPHY_BOTTOM = -18.2          # one fixed trophy row for every table card (where Largest Army's sat)
def table_layout(top_slot, top, centre_y=None):
    """Table cards: the pair of trophies always in the same place; the card's picture TABLE_GAP above them
    (or with its middle at centre_y)."""
    tr = trophies(); tr = place(tr, 0, TROPHY_BOTTOM - tr.bounds[1]); t = G.centre(top)
    t = place(t, 0, tr.bounds[3] + TABLE_GAP - t.bounds[1]) if centre_y is None else place(t, 0, centre_y)
    return {top_slot: t, ORANGE: tr}, ORANGE
def longest_road():
    """Road of evened irregular cobbles, 4 runs at 20 degrees; the dip's joints placed by hand (offset, angled,
    nothing straight across), one joint nudged 1 mm to even the stones."""
    army = largest_army()[0][PURPLE]; mid = (army.bounds[1] + army.bounds[3]) / 2     # road's middle level with the helmets'
    return table_layout(WHITE, G.longest_road11(LR_DIP, nudge=LR_NUDGE, seed=LR_SEED), centre_y=mid)
ARMY_GAP = 1.4
def largest_army(gap=None):
    big = G.helmet(22.0); small = G.helmet(15.5); gap = ARMY_GAP if gap is None else gap
    wb = big.bounds[2] - big.bounds[0]; ws = small.bounds[2] - small.bounds[0]
    h = unary_union([place(big, 0, -big.bounds[1])] + [place(small, sd * (wb / 2 + gap + ws / 2), -small.bounds[1]) for sd in (-1, 1)])
    return table_layout(PURPLE, h)
BC_PIECES = 'original'            # 'original' Catan shapes or 'own' (this set's printed pieces, drawn flat)
BC_ROAD_ANGLE = 30.0               # road piece at the angle you preferred
BC_ALIGN = 'optical'                 # 'box' (outer edges), 'weight' (centred on weight), 'optical' (weight + visual edge)
def visual_right(g, frac=0.5, step=0.05):
    """x of the right-most column where the piece covers at least frac of its own height (its visual edge)."""
    b = g.bounds; h = b[3] - b[1]; x = b[2]
    while x > b[0]:
        col = g.intersection(G.box(x - step, b[1] - 1, x, b[3] + 1))
        if not col.is_empty and (col.bounds[3] - col.bounds[1]) >= frac * h and col.area / step >= frac * h * 0.9: return x
        x -= step
    return b[2]
BC_GAP = 1.6                      # every piece ends the same distance before its first hexagon
def bc_pieces(kind):
    if kind == 'own':
        return {'road': G.road_piece_top(), 'settlement': G.own_settlement2(8.2), 'city': G.own_city2(10.0), 'dev': G.card_solid(6.0, 8.4)}
    return {'road': affinity.rotate(G.road_piece(), BC_ROAD_ANGLE, origin=(0, 0)),
            'settlement': affinity.scale(V1.p_settlement(), 1.25, 1.25, origin=(0, 0)),
            'city': affinity.scale(V1.p_city(), 1.25, 1.25, origin=(0, 0)), 'dev': G.card_solid(6.0, 8.4)}
def building_costs(kind=None):
    """Rows: piece on the left (right-aligned, same gap before the hexagons in every row), one hexagon per resource card."""
    rows = [('road', ['brick', 'wood']), ('settlement', ['brick', 'wood', 'wheat', 'sheep']),
            ('city', ['ore', 'ore', 'ore', 'wheat', 'wheat']), ('dev', ['ore', 'wheat', 'sheep'])]
    slot = {'brick': BRICK, 'wood': WOOD, 'wheat': WHEAT, 'sheep': WHITE, 'ore': ORE}
    piece = bc_pieces(kind or BC_PIECES)
    out = {}
    for i, (p, res) in enumerate(rows):
        y = 21.0 - i * 14.0; x = -13.0
        g = piece[p]; b = g.bounds
        cy = g.centroid.y if BC_ALIGN in ('weight', 'optical') else (b[1] + b[3]) / 2          # vertical: centred on weight
        edge = visual_right(g) if BC_ALIGN == 'optical' else b[2]                              # horizontal: where it looks solid
        out = merge(out, {WHITE: place(g, x - BC_GAP - edge, y - cy)})
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
KNIGHT_WEIGHT = 275.0
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
        else: dy = -allg.centroid.y                    # in between: centred on its weight (as the sheep)
        out = {k: affinity.translate(v, 0, dy) for k, v in out.items()}
    return out
def build(name):
    f, back = CARDS[name]
    face, corner = f()
    if name not in ('Brick', 'Wood', 'Sheep', 'Wheat', 'Ore'): face = finish(name, face)
    if corner is not None: face = merge(face, {corner: corners(corner)})
    return face, back(), corner
