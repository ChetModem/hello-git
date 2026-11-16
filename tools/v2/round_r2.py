import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
G.GAP = G.LINE
Z = C.ZONE
def full(name, f):
    face, corner = f(); face = C.finish(name, face) if name in C.SINGLE_ICON else face
    return C.merge(face, {corner: C.corners(corner)}) if corner is not None else face
def back_img(b):
    img = Image.new('RGB', (CW, CH), (235, 235, 235)); draw(img, V1.CARD, COLS[1]); draw(img, b, COLS[2]); return img
info = []
# row 1: Victory Point fit options + Knight before/after
vp_now = full('Victory Point', lambda: C.victory_point('before'))
vp_fit = full('Victory Point', lambda: C.victory_point('after'))
def vp_centred():
    f, c = C.victory_point('before'); g = f[C.ORANGE]; b = g.bounds; return {C.ORANGE: G.place(g, 0, -(b[1] + b[3]) / 2)}, c
vp_cen = C.merge(vp_centred()[0], {C.ORANGE: C.corners(C.ORANGE)})
C.KNIGHT_WEIGHT = 300.0; kn_old = full('Knight', C.knight); C.KNIGHT_WEIGHT = 275.0; kn_new = full('Knight', C.knight)
for n, f, sl in (('VP now', vp_now, C.ORANGE), ('VP sized where it stands', vp_fit, C.ORANGE), ('VP centred', vp_cen, C.ORANGE), ('Knight 300', kn_old, C.PURPLE), ('Knight 275', kn_new, C.PURPLE)):
    g = f[sl].difference(C.corners(0).buffer(0.01)); b = g.bounds
    info.append(f'{n:26s} ink {g.area:4.0f} h {b[3]-b[1]:4.1f} bottom {b[1]:+5.1f} in ring {Z.contains(g)}')
row1 = [vp_now, vp_fit, vp_cen, kn_old, kn_new]
# row 2: Longest Road now / a (middle level with the helmets) / b (bigger road) + Road Building + Largest Army
la = C.largest_army()[0]; helm_mid = (lambda b: (b[1] + b[3]) / 2)(la[C.PURPLE].bounds)
road = G.longest_road11(C.LR_DIP, nudge=C.LR_NUDGE, seed=C.LR_SEED)
G_RW, G_RS = G.ROAD_W, G.ROAD_STONE
G.ROAD_W, G.ROAD_STONE = G_RW * 1.12, G_RS * 1.12
road_b = centre_b = G.centre(G.soften(G.cobbled_path11(G.winding_pts(4, 11.6, 20), G.ROAD_W, G.ROAD_STONE, bends=C.LR_DIP, seed=C.LR_SEED, nudge=C.LR_NUDGE)))
G.ROAD_W, G.ROAD_STONE = G_RW, G_RS
def tc(f): return {**f, C.ORANGE: unary_union([f[C.ORANGE], C.corners(C.ORANGE)])}
lr_now = tc(C.table_layout(C.WHITE, road)[0]); lr_a = tc(C.table_layout(C.WHITE, road, centre_y=helm_mid)[0]); lr_b = tc(C.table_layout(C.WHITE, road_b)[0])
rb = full('Road Building', C.road_building)
row2 = [lr_now, lr_a, lr_b, rb, C.merge(la, {C.ORANGE: C.corners(C.ORANGE)})]
for n, f in (('LR now', lr_now), ('LR a', lr_a), ('LR b', lr_b)):
    w = f[C.WHITE]; b = w.bounds; info.append(f'{n:26s} road {b[2]-b[0]:4.1f}x{b[3]-b[1]:4.1f} middle {(b[1]+b[3])/2:+5.1f} smallest {min(p.area for p in G.pieces(w)):4.1f} closest {G.closest(w):.2f}')
info.append(f'helmets middle {helm_mid:+.1f}')
# row 3: Building Costs: original pieces (right-aligned, road level) / own pieces ; Largest Army spacing
bc_o = C.building_costs('original')[0]; bc_n = C.building_costs('own')[0]
la_even = C.merge(C.largest_army(gap=3.2)[0], {C.ORANGE: C.corners(C.ORANGE)})
row3 = [C.build('Building Costs')[0] if False else pickle.load(open('v2_cards.pkl', 'rb'))['Building Costs'][0], bc_o, bc_n, C.merge(la, {C.ORANGE: C.corners(C.ORANGE)}), la_even]
for n, f in (('BC original', bc_o), ('BC own', bc_n), ('LA gap 3.2', la_even)):
    g = unary_union(list(f.values())); info.append(f'{n:26s} closest {G.closest(g):.2f} smallest {min(p.area for p in G.pieces(g)):4.1f}')
# row 4: backs now / even line weight
C.BACK_LINES = 'original'; backs_o = [C.back_dev_v1(), C.back_costs_v1(), C.back_trophy_v1()]
C.BACK_LINES = 'even'; backs_e = [C.back_dev_v1(), C.back_costs_v1(), C.back_trophy_v1()]
C.BACK_LINES = 'original'
for n, b in zip(('dev', 'costs', 'trophy'), backs_e):
    inner = C.back_parts(b); info.append(f'back {n:6s} even: stroke ~{2*inner.area/inner.length:.2f} closest {G.closest(b):.2f} in card {V1.CARD.buffer(-2).contains(b)}')
rows = [[card_img(f) for f in row1], [card_img(f) for f in row2], [card_img(f) for f in row3],
        [back_img(b) for b in backs_o] + [back_img(b) for b in backs_e[:2]], [back_img(backs_e[2])]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('round_r2.png'); print(out.size); print('\n'.join(info))
pickle.dump(dict(road_b=road_b, helm_mid=helm_mid), open('round_r2.pkl', 'wb'))
