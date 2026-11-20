"""Simple painter's-algorithm renderer (PIL only): four views of the mini."""
import pickle, numpy as np, trimesh
from PIL import Image, ImageDraw
P = pickle.load(open('panda_druid_parts.pkl', 'rb'))
COL = {6: (158, 158, 163), 2: (242, 242, 242), 1: (32, 32, 32), 7: (40, 140, 55), 4: (110, 120, 60)}
tris, cols, norms = [], [], []
for k, (slot, (v, f)) in P.items():
    m = trimesh.Trimesh(v, f, process=False); tris.append(m.vertices[m.faces]); norms.append(m.face_normals); cols += [COL[slot]] * len(m.faces)
tris = np.vstack(tris); norms = np.vstack(norms); cols = np.array(cols, float)
def view(az, el, size=520, scale=12.5):
    a, e = np.radians(az), np.radians(el)
    R = np.array([[np.cos(a), np.sin(a), 0], [-np.sin(a) * np.sin(e), np.cos(a) * np.sin(e), np.cos(e)], [np.sin(a) * np.cos(e), -np.cos(a) * np.cos(e), np.sin(e)]])
    # camera looks along -R[2]; screen x = R[0], screen y = R[1]
    p = (tris - [0, 0, 16]) @ R.T; n = norms @ R.T
    vis = n[:, 2] > 0
    order = np.argsort(p[vis][:, :, 2].mean(1))
    light = np.array([-0.35, 0.55, 0.75]); light /= np.linalg.norm(light)
    shade = 0.42 + 0.58 * np.clip(n[vis] @ light, 0, 1)
    im = Image.new('RGB', (size, size), 'white'); d = ImageDraw.Draw(im)
    pv, cv = p[vis], cols[vis] * shade[:, None]
    for i in order:
        q = pv[i]; d.polygon([(size / 2 + x * scale, size / 2 - y * scale) for x, y, _ in q], fill=tuple(int(c) for c in np.clip(cv[i], 0, 255)))
    return im
views = [view(0, 8), view(35, 15), view(90, 10), view(200, 15)]
out = Image.new('RGB', (520 * 4, 520), 'white')
for i, im in enumerate(views): out.paste(im, (i * 520, 0))
out.save('panda_druid_views.png'); print(out.size, len(tris), 'triangles')
