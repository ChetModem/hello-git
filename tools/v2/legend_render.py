import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import glyphs as G
res, H = pickle.load(open('legend_v2.pkl', 'rb'))
W = 240.0; S = 9
COLS = {1: (25, 25, 25), 2: (240, 240, 240), 3: (200, 60, 50), 4: (110, 120, 60), 5: (240, 190, 140), 6: (170, 170, 175), 7: (0, 128, 0), 8: (128, 128, 255), 9: (255, 128, 0)}
img = Image.new('RGB', (int(W * S) + 40, int(H * S) + 40), 'white'); d = ImageDraw.Draw(img)
def poly(g, col):
    for p in G.pieces(g):
        d.polygon([(20 + (x + W / 2) * S, 20 + (H / 2 - y) * S) for x, y in p.exterior.coords], fill=col)
        for h in p.interiors: d.polygon([(20 + (x + W / 2) * S, 20 + (H / 2 - y) * S) for x, y in h.coords], fill=COLS[1])
poly(G.rr(-W / 2, -H / 2, W / 2, H / 2, 4), COLS[1])
for k, g in sorted(res.items()): poly(g, COLS[k])
img.save('legend_v2.png'); print(img.size)
