import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
V1R = pickle.load(open('../review/cards.pkl', 'rb'))
CORN = unary_union([G.Point(x, y).buffer(4.6) for x in (-20, 20) for y in (-32, 32)])
def icon_of(n): return unary_union([v for k, v in V1R[n]['face'].items() if k != 1]).difference(CORN)
def card(slot, icon): return {slot: unary_union([G.optical(icon), C.corners(slot)])}
brick, sheep_v1 = icon_of('Brick'), icon_of('Sheep')
pine = G.to_weight(G.pine_tree); ore = G.fit_zone(G.ore_rocks3())[0]; ore_old = G.fit_zone(G.ore_rocks2())[0]
wheat_cur, wheat_ang, wheat_chev = G.wheat_ear_final(), G.fit_param(G.wheat_angular), G.fit_param(G.wheat_chevron)
sheep_tidy, sheep_face = G.to_weight(G.sheep_tidy, 320), G.to_weight(G.sheep_face_min, 290)
rows = [[card(3, brick), card(4, pine), card(2, sheep_tidy), card(5, wheat_ang), card(6, ore)],
        [card(2, sheep_v1), card(2, sheep_tidy), card(2, sheep_face), card(6, ore_old), card(6, ore)],
        [card(5, wheat_cur), card(5, wheat_ang), card(5, wheat_chev)]]
gap = 24; W = 5 * (CW + gap) + gap; H = 3 * (CH + gap * 2) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for f in r: out.paste(card_img(f), (x, y)); x += CW + gap
    y += CH + gap * 2
out.save('round3.png'); print(out.size)
for n, g in (('brick', brick), ('pine', pine), ('sheep v1', sheep_v1), ('wheat ang', wheat_ang), ('wheat chev', wheat_chev), ('sheep tidy', sheep_tidy), ('ore', ore)):
    o = G.optical(g); print(f'{n:12s} ink {g.area:4.0f}  outline centre after optical centring: {(o.bounds[1]+o.bounds[3])/2:+.1f} mm')
