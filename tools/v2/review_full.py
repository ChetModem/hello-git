import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
R = pickle.load(open('v2_cards.pkl', 'rb'))
def back_img(b):
    img = Image.new('RGB', (CW, CH), (235, 235, 235)); draw(img, V1.CARD, COLS[1]); draw(img, b, COLS[2]); return img
rows = [[card_img(R[n][0]) for n in ('Brick', 'Wood', 'Sheep', 'Wheat', 'Ore')],
        [card_img(R[n][0]) for n in ('Knight', 'Victory Point', 'Road Building', 'Year of Plenty', 'Monopoly')],
        [card_img(R[n][0]) for n in ('Building Costs', 'Longest Road', 'Largest Army')],
        [back_img(R[n][1]) for n in ('Brick', 'Knight', 'Building Costs', 'Longest Road')]]
gap = 24; W = 5 * (CW + gap) + gap; H = len(rows) * (CH + 2 * gap) + gap
out = Image.new('RGB', (W, H), 'white'); y = gap
for r in rows:
    x = gap
    for im in r: out.paste(im, (x, y)); x += CW + gap
    y += CH + 2 * gap
out.save('review_full.png'); out.resize((W // 4, H // 4), Image.LANCZOS).save('review_full_small.png'); print(out.size)
