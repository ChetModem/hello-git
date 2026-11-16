"""v2 rules legend: the exact v2 card icons, grouped by card type, sized like the cards; set's line weights;
text sized so every counter stays open."""
import os, sys, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'special'))
import glyphs as G, cards_v2 as C
import design as D
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from shapely import affinity
G.GAP = G.LINE
place = G.place
WHITE, GREEN, PURPLE, ORANGE = C.WHITE, C.GREEN, C.PURPLE, C.ORANGE

TITLE_CAP, BODY_CAP, LEAD, EMB = 4.8, 4.2, 2.6, 0.0     # 4.2 mm body text: counters stay open, strokes ~0.8 mm
BOARD_W, MARGIN, COL_GAP, ICON_COL, ICON_GAP = 240.0, 9.0, 10.0, 34.0, 3.0
ENTRY_GAP = 7.0
ICON_COL_R = 27.0                                        # the progress-card icons are narrower
LINE_W = G.LINE                                          # border and divider: the set's 0.8 mm line weight
COLW = (BOARD_W - 2 * MARGIN - COL_GAP) / 2

R = pickle.load(open(os.path.join(HERE, 'v2_cards.pkl'), 'rb'))
CORN = C.corners(0).buffer(0.01)
def card_icon(name, slots):
    f = R[name][0]; return {s: f[s].difference(CORN) for s in slots if s in f}
def lr_icon():
    return {WHITE: G.longest_road6(3, 10.2, 20, seed=3)}                     # the same road and stones, 3 runs to fit the column
def la_icon():
    return {PURPLE: R['Largest Army'][0][PURPLE]}
LEFT = [('KNIGHT', PURPLE, card_icon('Knight', [PURPLE]), 'Move the robber. Steal 1 resource from a player next to it.'),
        ('VICTORY POINT', ORANGE, card_icon('Victory Point', [ORANGE]), 'Worth 1 point. Keep it secret until you win.'),
        ('LONGEST ROAD', ORANGE, lr_icon(), '2 points. First to build 5 roads in a row. A longer road takes it.'),
        ('LARGEST ARMY', ORANGE, la_icon(), '2 points. First to play 3 knights. Playing more takes it.')]
RIGHT = [('ROAD BUILDING', GREEN, card_icon('Road Building', [WHITE]), 'Build 2 free roads.'),
         ('YEAR OF PLENTY', GREEN, card_icon('Year of Plenty', [WHITE]), 'Take any 2 resources from the bank.'),
         ('MONOPOLY', GREEN, card_icon('Monopoly', [WHITE]), 'Name a resource. Everyone gives you all of theirs.')]
FOOT = 'Development cards: play 1 per turn (not the turn you buy it). Victory Points: reveal any time to win.'

TITLE_TRACK = 0.85                                       # capitals like T-Y tuck together; a little more space keeps 0.8 mm apart
def txt(s, cap, slot, x, y, out, track=None):
    t, _ = D.text(s, cap, True, track=track); t = t.buffer(EMB, join_style=1) if EMB else t
    out.setdefault(slot, []).append(place(t, x, y))

def entry(title, tslot, icon, body, icon_col=ICON_COL):
    """Shapes with the entry's top-left at (0, 0); returns (shapes, height)."""
    out = {}; tx = icon_col + ICON_GAP
    assert D.text(title, TITLE_CAP, True, track=TITLE_TRACK)[1] <= COLW - tx, f'title too wide: {title}'
    txt(title, TITLE_CAP, tslot, tx, -TITLE_CAP, out, track=TITLE_TRACK)
    y = -TITLE_CAP - LEAD
    for ln in D.wrap(body, BODY_CAP, COLW - tx, True):
        y -= BODY_CAP; txt(ln, BODY_CAP, WHITE, tx, y, out); y -= LEAD
    th = -y - LEAD
    ib = unary_union(list(icon.values())).bounds; ih = ib[3] - ib[1]
    h = max(th, ih); dx = icon_col / 2 - (ib[0] + ib[2]) / 2; dy = -h / 2 - (ib[1] + ib[3]) / 2
    for s, g in icon.items(): out.setdefault(s, []).append(place(g, dx, dy))
    if ih > th:                                          # centre the text block on a tall icon
        for s in list(out):
            pass
    return out, h

def footer():
    """Cost key (ore, wheat, sheep = a development card) and the play rule, with a divider above."""
    out = {}
    y = 0.0
    out.setdefault(WHITE, []).append(box(0, y - LINE_W, COLW, y))                     # divider
    y -= LINE_W + 4.0
    x = 0.0; hw = 6.5
    for r in ('ore', 'wheat', 'sheep'):
        hx = place(D.hexagon(0, 0, hw).buffer(0.25, join_style=1).buffer(-0.25, join_style=1), x + hw / 2, y - 4.2)
        out.setdefault(C.RES_SLOT[r], []).append(hx); x += hw + G.LINE
    card = G.card_solid(6.0, 8.4); b = card.bounds
    out.setdefault(WHITE, []).append(place(card, x + 1.4 - b[0], y - 4.2 - (b[1] + b[3]) / 2))
    tx = x + 1.4 + (b[2] - b[0]) + 4.0
    lines = D.wrap(FOOT, BODY_CAP, COLW - tx, True)
    yy = y + 0.3
    for ln in lines:
        yy -= BODY_CAP; txt(ln, BODY_CAP, WHITE, tx, yy, out); yy -= LEAD
    return out, max(-yy - LEAD, -(y - 8.4))

def legend():
    cols = []
    for ents, icol in ((LEFT, ICON_COL), (RIGHT, ICON_COL_R)):
        y = 0.0; blocks = []
        for e in ents:
            sh, h = entry(*e, icon_col=icol); blocks.append((sh, y)); y -= h + ENTRY_GAP
        cols.append((blocks, -y - ENTRY_GAP))
    fsh, fh = footer()
    right_h = cols[1][1] + ENTRY_GAP + fh
    inner_h = max(cols[0][1], right_h)
    H = round(inner_h + 2 * MARGIN, 1)
    out = {}
    def add(s, g): out.setdefault(s, []).append(g)
    top = H / 2 - MARGIN
    for ci, (blocks, ch) in enumerate(cols):
        x0 = -BOARD_W / 2 + MARGIN + ci * (COLW + COL_GAP)
        for sh, y in blocks:
            for s, gs in sh.items():
                for g in gs: add(s, place(g, x0, top + y))
    x0 = -BOARD_W / 2 + MARGIN + COLW + COL_GAP
    for s, gs in fsh.items():
        for g in gs: add(s, place(g, x0, -H / 2 + MARGIN + fh))
    inset = 3.0
    add(WHITE, G.rr(-BOARD_W / 2 + inset, -H / 2 + inset, BOARD_W / 2 - inset, H / 2 - inset, 3).difference(
        G.rr(-BOARD_W / 2 + inset + LINE_W, -H / 2 + inset + LINE_W, BOARD_W / 2 - inset - LINE_W, H / 2 - inset - LINE_W, 3 - LINE_W)))
    res = {k: unary_union(v).buffer(0) for k, v in out.items()}
    return res, H

if __name__ == '__main__':
    res, H = legend()
    print('board %.0f x %.1f' % (BOARD_W, H))
    pickle.dump((res, H), open(os.path.join(HERE, 'legend_v2.pkl'), 'wb'))
