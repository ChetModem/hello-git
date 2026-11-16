import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
import glyphs as G, cards_v2 as C
r6 = pickle.load(open('set_r6.pkl', 'rb'))['set']; r7 = pickle.load(open('set_r7.pkl', 'rb')); r8 = pickle.load(open('set_r8.pkl', 'rb'))['ores']; r12 = pickle.load(open('set_r12.pkl', 'rb'))
def card(slot, icon): return {slot: unary_union([icon, C.corners(slot)])}
locked = {'brick': r6['brick'], 'wood': r6['pine'], 'sheep': r6['sheep'], 'wheat': r7['wheat_mid'], 'ore': r12['veer_a']}
pickle.dump(locked, open('resource_icons_v2.pkl', 'wb'))
rows = [[card(3, locked['brick']), card(4, locked['wood']), card(2, locked['sheep']), card(5, locked['wheat']), card(6, locked['ore'])]]
gap = 24; W = 5 * (CW + gap) + gap; H = 1 * (CH + gap * 2) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for f in r: out.paste(card_img(f), (x, y)); x += CW + gap
    y += CH + gap * 2
out.save('locked_set.png')
Z = G.safe_zone()
for n, g in locked.items(): print(n, round(g.area), 'zone', Z.contains(g), 'closest %.2f' % G.closest(g))
