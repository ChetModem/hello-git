import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open('preview_v2.py').read().split('res = {}')[0])
R = pickle.load(open('v2_cards.pkl', 'rb'))
def back_img(b):
    img = Image.new('RGB', (CW, CH), (235, 235, 235)); draw(img, V1.CARD, COLS[1]); draw(img, b, COLS[2]); return img
rows = [('Development cards (v2)', ['Knight', 'Victory Point', 'Road Building', 'Year of Plenty', 'Monopoly']),
        ('Table cards (v2) and Ore (v2)', ['Building Costs', 'Longest Road', 'Largest Army', 'Ore'])]
W = 5 * (CW + 20) + 20; H = 3 * (CH + 90) + 40
out = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(out); y = 10
for title, names in rows:
    dr.text((10, y), title, fill='black', font=F); y += 34; x = 10
    for n in names:
        dr.text((x, y), n, fill=(90, 90, 90), font=F); out.paste(card_img(R[n][0]), (x, y + 30)); x += CW + 20
    y += CH + 56
dr.text((10, y), 'Backs: original designs, Building Costs now with a coin purse (development and table cards at 0.6 mm, hidden black layer)', fill='black', font=F); y += 34; x = 10
for n, b in [('resource', R['Ore'][1]), ('development', R['Knight'][1]), ('building costs', R['Building Costs'][1]), ('longest road / army', R['Longest Road'][1])]:
    dr.text((x, y), n, fill=(90, 90, 90), font=F); out.paste(back_img(b), (x, y + 30)); x += CW + 20
out.save('v2_sheet.png'); print(out.size)
