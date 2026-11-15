"""Designs for the extra cards (Building Costs, Longest Road, Largest Army) and the table legend.
All sizes are final millimetres. Coordinates: card/board centre at (0,0), x right, y up, as seen
looking at the printed face."""
import os, sys, pickle, numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SP)
import dev_icons                                        # the solid dev-card icon code (same as tools/catan_dev_icons.py)

GAP = 0.7       # smallest black gap between coloured shapes
LINE = 0.7      # thinnest coloured line

# ---------------------------------------------------------------- text
class _Pen(BasePen):
    def __init__(self, gs):
        super().__init__(gs); self.contours = []; self.cur = []
    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)
    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            a = (1-t)**3; b = 3*(1-t)**2*t; c = 3*(1-t)*t**2; d = t**3
            self.cur.append((a*p0[0]+b*p1[0]+c*p2[0]+d*p3[0], a*p0[1]+b*p1[1]+c*p2[1]+d*p3[1]))
    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 7)[1:]:
            a = (1-t)**2; b = 2*(1-t)*t; c = t**2
            self.cur.append((a*p0[0]+b*p1[0]+c*p2[0], a*p0[1]+b*p1[1]+c*p2[1]))
    def _closePath(self):
        if len(self.cur) > 2: self.contours.append(self.cur)
        self.cur = []
    _endPath = _closePath

FONTS = {}
TRACK = 0.55        # mm of extra space between letters (bold text otherwise nearly touches)
I_DOT_LIFT = 0.45   # mm: extra space between the dot and stem of i and j
def _font(bold):
    f = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if f not in FONTS:
        t = TTFont(f); gs = t.getGlyphSet(); cm = t.getBestCmap()
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(gs); gs[cm[ord('H')]].draw(bp)
        FONTS[f] = (t, gs, cm, t['hmtx'], t['head'].unitsPerEm, bp.bounds[3])
    return FONTS[f]

def text(s, cap, bold=True, track=None):
    """Text outline with its baseline at y=0, starting at x=0; cap = capital letter height in mm."""
    t, gs, cmap, hmtx, upm, caph = _font(bold)
    k = cap / caph; x = 0; polys = []
    tr = (TRACK if track is None else track) / k
    for ch in s:
        g = cmap.get(ord(ch), 'space'); adv = hmtx[g][0]
        pen = _Pen(gs); gs[g].draw(pen)
        shape = Polygon()
        for c in pen.contours:
            p = Polygon(c).buffer(0)
            shape = shape.symmetric_difference(p)      # even-odd: holes in letters come out right
        if ch in 'ij' and hasattr(shape, 'geoms') and len(shape.geoms) == 2:
            dot, stem = sorted(shape.geoms, key=lambda g: -g.centroid.y)
            shape = unary_union([stem, affinity.translate(dot, 0, I_DOT_LIFT / k)])   # open the dot gap (prints as 'l' otherwise)
        if not shape.is_empty: polys.append(affinity.translate(affinity.scale(shape, k, k, origin=(0, 0)), x * k, 0))
        x += adv + tr
    return unary_union(polys) if polys else Polygon(), (x - tr) * k

def width(s, cap, bold=True):
    return text(s, cap, bold)[1]

def wrap(s, cap, maxw, bold=False):
    words = s.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if width(t, cap, bold) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

# ---------------------------------------------------------------- mini icons (about 6.5 mm)
def rr(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=12)

def stadium(a, b, w):
    return LineString([a, b]).buffer(w / 2, quad_segs=16)

def m_brick():
    h, w = 1.9, 3.0
    return unary_union([rr(-w/2, GAP/2, w/2, GAP/2 + h, 0.3),
                        rr(-w - GAP/2, -GAP/2 - h, -GAP/2, -GAP/2, 0.3), rr(GAP/2, -GAP/2 - h, w + GAP/2, -GAP/2, 0.3)])

def m_wood():
    r = 1.4; d = 2 * r + GAP
    return unary_union([Point(-d/2, -1.25).buffer(r, quad_segs=24), Point(d/2, -1.25).buffer(r, quad_segs=24),
                        Point(0, -1.25 + d * np.sqrt(3) / 2).buffer(r, quad_segs=24)])

def m_wheat():
    """Stalk with two tiers of grains at 30 deg and a top grain. Parallel grains sit 1.95 mm apart
    vertically = 1.69 mm apart square-on, leaving 0.74 mm of black between them."""
    w = 0.95
    parts = [stadium((0, -3.0), (0, 1.6), 0.9), stadium((0, 2.05), (0, 3.4), 1.0)]
    for y in (-1.2, 0.75):
        for sd in (-1, 1):
            parts.append(stadium((sd * 0.2, y), (sd * 1.7, y + 0.866), w))
    return unary_union(parts)

def m_sheep():
    body = unary_union([Point(x, y).buffer(1.25, quad_segs=24) for x, y in
                        [(-2.2, 0.6), (-1.1, 1.55), (0.3, 1.75), (1.6, 1.3), (2.3, 0.1), (1.5, -1.1), (0, -1.3), (-1.4, -1.0), (-2.4, -0.5)]]
                       + [Polygon([(-2.4, -0.8), (2.2, -1.0), (2.2, 1.2), (-2.2, 1.4)])])
    head = affinity.scale(Point(0, 0).buffer(1, quad_segs=24), 1.15, 1.45); head = affinity.translate(head, 2.55, -0.1)
    body = body.difference(head.buffer(GAP))
    legs = unary_union([rr(x - 0.55, -3.8, x + 0.55, -2.0, 0.3) for x in (-1.3, 0.9)]).difference(body.buffer(0.0))
    legs = legs.difference(body.buffer(GAP))
    return unary_union([body, head, legs]).buffer(0)

def m_ore():
    big = Polygon([(-1.2, -2.7), (3.4, -2.7), (1.1, 2.9)])
    small = Polygon([(-3.6, -2.7), (0.6, -2.7), (-1.5, 0.9)]).difference(big.buffer(GAP))
    soft = lambda p, r: p.buffer(-r, join_style=1).buffer(r, quad_segs=8)
    return unary_union([soft(big, 0.35), soft(small, 0.3)])

# pieces (white)
def p_road():
    return affinity.rotate(rr(-3.9, -1.0, 3.9, 1.0, 0.4), 25)

def p_settlement():
    return Polygon([(-2.6, -2.6), (2.6, -2.6), (2.6, 0.6), (0, 3.0), (-2.6, 0.6)])

def p_city():
    return Polygon([(-3.6, -2.8), (3.6, -2.8), (3.6, 0.6), (0.2, 0.6), (0.2, 1.6), (-1.7, 3.4), (-3.6, 1.6)])

def p_devcard():
    card = rr(-2.5, -3.3, 2.5, 3.3, 0.6)
    hexo = Polygon([(1.1 * np.cos(np.radians(a)), 1.1 * np.sin(np.radians(a))) for a in range(30, 390, 60)])
    return card.difference(hexo.buffer(LINE / 2).difference(hexo.buffer(-LINE / 2)))

# ---------------------------------------------------------------- dev icons at any size, gaps kept printable
def dev_icon(name, height):
    p0 = dev_icons.solid(name, 1.0); h0 = p0.bounds[3] - p0.bounds[1]
    k = height / h0
    for _ in range(3):
        p = dev_icons.solid(name, k); k = height / (p.bounds[3] - p.bounds[1])
    p = affinity.scale(dev_icons.solid(name, k), -k, k, origin=(0, 0))   # stored as printed (face down) -> mirror to the face view
    b = p.bounds
    return affinity.translate(p, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)

def knight_helmet(height):
    """Knight helmet that keeps its crest at small sizes: the crest is thickened to at least 0.7 mm
    while staying 0.7 mm clear of the helmet."""
    g = dev_icon('knight', height)
    ps = sorted((list(g.geoms) if hasattr(g, 'geoms') else [g]), key=lambda p: -p.area)
    helmet, small = ps[0], ps[1:]
    crest = unary_union(small)
    if not crest.is_empty:
        t = 0.0
        while t < 0.4:
            c2 = crest.buffer(t, join_style=1).difference(helmet.buffer(GAP))
            if not printable(c2, w=0.7, speck=0.5).is_empty: crest = c2; break
            t += 0.05
    return unary_union([helmet, crest])

def hexagon(cx, cy, w=6.06):
    r = w / np.sqrt(3)
    return Polygon([(cx + r * np.cos(np.radians(a)), cy + r * np.sin(np.radians(a))) for a in range(90, 450, 60)])

CORNERS = [(-20, 32), (20, 32), (-20, -32), (20, -32)]
CARD = rr(-27, -40, 27, 40, 3.0)

def place(g, x, y): return affinity.translate(g, x, y)

def printable(g, w=0.6, speck=2.0):
    g = g.buffer(-w / 2, join_style=1).buffer(w / 2, join_style=1).buffer(0)
    gs = [x for x in (list(g.geoms) if hasattr(g, 'geoms') else [g]) if x.area >= speck]      # no stray specks left behind
    keep = [x for x in gs if not any(y.area > x.area and x.distance(y) < 0.6 for y in gs if y is not x) or x.area > 6]
    return unary_union(keep)

# ---------------------------------------------------------------- cards: {colour slot: shape}
RES = {'brick': (3, m_brick), 'wood': (4, m_wood), 'wheat': (5, m_wheat), 'sheep': (2, m_sheep), 'ore': (6, m_ore)}

HEX_W = 6.5      # resource hexagon width on the Building Costs card (mm), same pointy-top shape as the corner hexes
NUM_CAP = 4.6    # count number cut into the hexagon in black
RES_SLOT = {'brick': 3, 'wood': 4, 'wheat': 5, 'sheep': 2, 'ore': 6}

def res_hex(n=1, w=HEX_W):
    """Resource hexagon in the resource card's colour; a count of 2+ is cut into it in black."""
    h = hexagon(0, 0, w).buffer(0.25, join_style=1).buffer(-0.25, join_style=1)     # softened corners
    if n > 1:
        t, _ = text(str(n), NUM_CAP, True, track=0); b = t.bounds
        h = h.difference(place(t, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2))
    return h

def building_costs():
    """No corner hexes on this card: one row per thing you can buy, one resource-coloured hexagon per card it costs."""
    rows = [(p_road, [('brick', 1), ('wood', 1)]),
            (p_settlement, [('brick', 1), ('wood', 1), ('wheat', 1), ('sheep', 1)]),
            (p_city, [('ore', 1), ('ore', 1), ('ore', 1), ('wheat', 1), ('wheat', 1)]),
            (p_devcard, [('ore', 1), ('wheat', 1), ('sheep', 1)])]
    out = {2: [], 3: [], 4: [], 5: [], 6: []}
    for i, (piece, res) in enumerate(rows):
        y = 24.0 - i * 16.0
        pc = affinity.scale(piece(), 1.25, 1.25, origin=(0, 0)); b = pc.bounds
        out[2].append(place(pc, -18.6 - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2))
        x = -13.0
        for r, n in res:
            out[RES_SLOT[r]].append(place(res_hex(n), x + HEX_W / 2, y)); x += HEX_W + 1.0
        assert x - 1.0 <= 23.6, f'row {i} too wide: ends at {x - 1.0:.1f}'
    return {k: printable(unary_union(v), speck=0.5) for k, v in out.items() if v}

def trophies(y, h=9.5):
    t = dev_icon('vp', h)
    t = t.buffer(0.3, join_style=2, mitre_limit=10).buffer(-0.3, join_style=2, mitre_limit=10)   # fill black slivers under 0.6 mm (handle loops)
    w = t.bounds[2] - t.bounds[0]
    return unary_union([place(t, -(w / 2 + 1.5), y), place(t, w / 2 + 1.5, y)])

def longest_road():
    seg = 8.6; wd = 2.6; pts = [(-17.2, 4.0)]
    ang = [30, -30, 30, -30, 30]
    roads = []
    x, y = pts[0]
    for a in ang:
        dx, dy = seg * np.cos(np.radians(a)), seg * np.sin(np.radians(a))
        off = (wd + GAP) / np.sqrt(3) + 0.05      # caps at a 60 deg bend sit sqrt(3)*off apart: leaves >= 0.7 mm
        a0 = (x + off * np.cos(np.radians(a)), y + off * np.sin(np.radians(a)))
        a1 = (x + dx - off * np.cos(np.radians(a)), y + dy - off * np.sin(np.radians(a)))
        roads.append(stadium(a0, a1, wd)); x, y = x + dx, y + dy
    r = unary_union(roads); b = r.bounds
    r = affinity.translate(r, -(b[0] + b[2]) / 2, 9.0 - (b[1] + b[3]) / 2)
    return {2: r, 9: unary_union([printable(trophies(-11.0))] + [hexagon(*c) for c in CORNERS])}

def largest_army():
    big = knight_helmet(24.0); small = knight_helmet(17.0)      # leader in the middle, two either side
    base = -3.0                                                           # all three stand on the same line
    wb = big.bounds[2] - big.bounds[0]; ws = small.bounds[2] - small.bounds[0]; gap = 1.4
    helms = unary_union([place(big, 0, base - big.bounds[1])] +
                        [place(small, sd * (wb / 2 + gap + ws / 2), base - small.bounds[1]) for sd in (-1, 1)])
    return {8: printable(helms, speck=0.8), 9: unary_union([printable(trophies(-13.5))] + [hexagon(*c) for c in CORNERS])}

CARDS = {'building-costs': (building_costs, 4), 'longest-road': (longest_road, 1), 'largest-army': (largest_army, 1)}

# ---------------------------------------------------------------- legend board
COLS = {1: (20, 20, 20), 2: (240, 240, 240), 3: (200, 60, 50), 4: (110, 120, 60), 5: (240, 190, 140), 6: (170, 170, 175),
        7: (0, 150, 60), 8: (128, 128, 255), 9: (255, 128, 0)}


ENTRIES = [
    ('knight', 8, 'KNIGHT', 'Move the robber. Steal 1 resource from a player next to it.'),
    ('vp', 9, 'VICTORY POINT', 'Worth 1 point. Keep it secret until you win.'),
    ('rb', 7, 'ROAD BUILDING', 'Build 2 free roads.'),
    ('yop', 7, 'YEAR OF PLENTY', 'Take any 2 resources from the bank.'),
    ('mono', 7, 'MONOPOLY', 'Name a resource. Everyone gives you all of theirs.'),
    ('lr', 9, 'LONGEST ROAD', '2 points. First to build 5 roads in a row. A longer road takes it.'),
    ('la', 9, 'LARGEST ARMY', '2 points. First to play 3 knights. Playing more takes it.'),
]
FOOT = 'Development cards: play 1 per turn, but not on the turn you buy it.'

TITLE_CAP, BODY_CAP, LEAD, ICON_H = 4.0, 3.4, 2.4, 14.0
EMBOLDEN = 0.06
BOARD_W = 240.0; MARGIN = 8.0; ICON_COL = 22.0; COL_GAP = 8.0
BOARD_H = None

def _icon(key):
    if key == 'lr': return 2, _road_chain(5.4, 1.8)        # white, like the pieces on the Building Costs card
    if key == 'la': return 8, largest_army_small()
    return {'knight': 8, 'vp': 9, 'rb': 7, 'yop': 7, 'mono': 7}[key], dev_icon(key, ICON_H)

def _entry(key, slot, title, body, colw):
    """Shapes for one entry with its top-left at (0,0); returns (shapes, height)."""
    out = {}
    isl, ic = _icon(key); b = ic.bounds
    if b[2] - b[0] > ICON_COL - 2: k = (ICON_COL - 2) / (b[2] - b[0]); ic = affinity.scale(ic, k, k, origin=(0, 0)); b = ic.bounds
    t, _ = text(title, TITLE_CAP, True)
    out.setdefault(slot, []).append(place(t.buffer(EMBOLDEN, join_style=1), ICON_COL, -TITLE_CAP))
    y = -TITLE_CAP - LEAD
    for ln in wrap(body, BODY_CAP, colw - ICON_COL, True):
        y -= BODY_CAP; t, _ = text(ln, BODY_CAP, True); out.setdefault(2, []).append(place(t.buffer(EMBOLDEN, join_style=1), ICON_COL, y)); y -= LEAD
    h = max(-y - LEAD, b[3] - b[1])
    out.setdefault(isl, []).append(place(ic, ICON_COL / 2 - 1 - (b[0] + b[2]) / 2, -h / 2 - (b[1] + b[3]) / 2))
    return out, h

def legend():
    global BOARD_H
    colw = (BOARD_W - 2 * MARGIN - COL_GAP) / 2
    cols = [ENTRIES[:4], ENTRIES[4:]]
    blocks = []; heights = []
    for ci, ents in enumerate(cols):
        y = 0; x0 = -BOARD_W / 2 + MARGIN + ci * (colw + COL_GAP)
        for e in ents:
            sh, h = _entry(*e, colw); blocks.append((sh, x0, y)); y -= h + 6.0
        heights.append(-y - 6.0)
    top = max(heights)
    # footer
    fx = 3.6 + 3 * 7.4 + 3.4 + 5.0
    flines = wrap(FOOT, BODY_CAP, BOARD_W - 2 * MARGIN - fx, True)
    fh = len(flines) * (BODY_CAP + LEAD) - LEAD
    BOARD_H = round(2 * MARGIN + top + 7.0 + fh + 0.5, 1)
    out = {}
    def add(slot, g): out.setdefault(slot, []).append(g)
    Y0 = BOARD_H / 2 - MARGIN
    for sh, x0, y in blocks:
        for slot, gs in sh.items():
            for g in gs: add(slot, place(g, x0, Y0 + y))
    yf = -BOARD_H / 2 + MARGIN + fh
    add(2, box(-BOARD_W / 2 + MARGIN, yf + 3.15, BOARD_W / 2 - MARGIN, yf + 3.85))            # divider line
    xx = -BOARD_W / 2 + MARGIN
    for r in ('ore', 'wheat', 'sheep'):
        add(RES_SLOT[r], place(res_hex(1, 6.4), xx + 3.2, yf - fh / 2)); xx += 6.4 + 1.0
    g = affinity.scale(p_devcard(), 1.15, 1.15, origin=(0, 0)); b = g.bounds; add(2, place(g, xx + 0.8 - b[0], yf - fh / 2 - (b[1] + b[3]) / 2))
    y = yf
    for ln in flines:
        y -= BODY_CAP; t, _ = text(ln, BODY_CAP, True); add(2, place(t.buffer(EMBOLDEN, join_style=1), -BOARD_W / 2 + MARGIN + fx, y)); y -= LEAD
    # thin white border
    add(2, rr(-BOARD_W / 2 + 3, -BOARD_H / 2 + 3, BOARD_W / 2 - 3, BOARD_H / 2 - 3, 3).difference(
        rr(-BOARD_W / 2 + 3.8, -BOARD_H / 2 + 3.8, BOARD_W / 2 - 3.8, BOARD_H / 2 - 3.8, 2.2)))
    res = {k: unary_union(v) for k, v in out.items()}
    for k in res:
        if k in (8, 9): res[k] = printable(res[k])          # knight helmets / trophies: drop stray specks
        elif k != 2: res[k] = printable(res[k], speck=0)
    return res

def _road_chain(seg, wd):
    x, y = 0, 0; roads = []
    for a in [30, -30, 30, -30, 30]:
        c, s = np.cos(np.radians(a)), np.sin(np.radians(a)); off = (wd + GAP) / np.sqrt(3) + 0.05
        roads.append(stadium((x + off * c, y + off * s), (x + seg * c - off * c, y + seg * s - off * s), wd)); x, y = x + seg * c, y + seg * s
    r = unary_union(roads); b = r.bounds
    return affinity.translate(r, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)

def largest_army_small():
    h = dev_icon('knight', 11.0); w = h.bounds[2] - h.bounds[0]
    return unary_union([place(h, dx * (w + 0.9), 0) for dx in (-1, 0, 1)])


# ---------------------------------------------------------------- back of the new cards
def special_back():
    """Outer hex ring (as on the resource back) plus one inner ring turned 30 degrees, points to the
    outer ring's flat sides. Lines only, no solid areas. Resource back = 1 ring, development = 3 nested."""
    res = pickle.load(open(os.path.join(SP, 'logo.pkl'), 'rb'))
    dev = pickle.load(open(os.path.join(SP, 'dev_shapes.pkl'), 'rb'))['knight']['logo']
    rings = sorted(dev.geoms, key=lambda g: g.area)            # inner, middle, outer
    spacing = rings[2].distance(rings[1])                      # black space between rings on the dev back
    inner = affinity.rotate(rings[1], 30, origin=(0, 0))
    for _ in range(40):                                        # same spacing to the outer ring as the dev back
        d = inner.distance(res)
        if abs(d - spacing) < 0.02: break
        k = 1 + (d - spacing) / 20.0; inner = affinity.scale(inner, k, k, origin=(0, 0))
    return unary_union([res, inner]).buffer(0)

def board_outline():
    return rr(-BOARD_W / 2, -BOARD_H / 2, BOARD_W / 2, BOARD_H / 2, 4)

# ---------------------------------------------------------------- stand (side profile, y = depth, z = height)
BOARD_T = 2.4          # board thickness
SLOT = BOARD_T + 0.45  # slot width (0.2 mm play each side after printing)
LEAN = 15.0            # board leans back this many degrees from vertical
FOOT_W = 24.0          # each foot is this wide (x)
def stand_profile():
    body = Polygon([(0, 0), (54, 0), (54, 6), (40, 15), (12, 15), (0, 6)])
    body = body.buffer(1.0, join_style=1).buffer(-1.0, join_style=1)      # soften the corners
    a = np.radians(LEAN)
    # slot: bottom at z=4, centred at y=19, tilted back (towards +y) by LEAN
    d = np.array([np.sin(a), np.cos(a)]); n = np.array([np.cos(a), -np.sin(a)])
    c0 = np.array([19.0, 4.0])
    slot = Polygon([c0 - n * SLOT / 2, c0 + n * SLOT / 2, c0 + n * SLOT / 2 + d * 30, c0 - n * SLOT / 2 + d * 30])
    return body.difference(slot).buffer(0)
