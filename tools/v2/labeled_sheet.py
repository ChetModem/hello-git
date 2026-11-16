"""Full v2 set with each card plainly labelled above it."""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
from PIL import ImageFont
R = pickle.load(open('v2_cards.pkl', 'rb'))
FL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
def back_img(b):
    img = Image.new('RGB', (CW, CH), (235, 235, 235)); draw(img, V1.CARD, COLS[1]); draw(img, b, COLS[2]); return img
rows = [[(n, card_img(R[n][0])) for n in ('Brick', 'Wood', 'Sheep', 'Wheat', 'Ore')],
        [(n, card_img(R[n][0])) for n in ('Knight', 'Victory Point', 'Road Building', 'Year of Plenty', 'Monopoly')],
        [(n, card_img(R[n][0])) for n in ('Building Costs', 'Longest Road', 'Largest Army')],
        [('Back: resource', back_img(R['Brick'][1])), ('Back: development', back_img(R['Knight'][1])),
         ('Back: building costs', back_img(R['Building Costs'][1])), ('Back: longest road', back_img(R['Longest Road'][1])),
         ('Back: largest army', back_img(R['Largest Army'][1]))]]
gap, lab = 30, 56
W = 5 * (CW + gap) + gap; H = len(rows) * (CH + lab + gap) + gap
out = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(out); y = gap
for r in rows:
    x = gap
    for name, im in r:
        tw = d.textlength(name, font=FL)
        d.text((x + (CW - tw) / 2, y), name, fill='black', font=FL)
        out.paste(im, (x, y + lab)); x += CW + gap
    y += CH + lab + gap
out.save('labeled_sheet.png'); print(out.size)
