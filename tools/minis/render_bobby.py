"""Preview renderer for bobby_panda.py: sphere-traces the sampled distance field (numpy + scipy + PIL only).

    python3 render_bobby.py bobby_fields_0.1.npz out.png [az,el az,el ...]
"""
import sys, numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image

COL = {'green': (70, 150, 60), 'arms': (30, 30, 32), 'black': (30, 30, 32), 'tan': (205, 160, 110), 'olive': (112, 122, 62),
       'sclera': (245, 245, 240), 'white': (238, 238, 232), 'base': (150, 150, 156)}

def load(path):
    z = np.load(path); xs, ys, zs = z['xs'], z['ys'], z['zs']
    names = [k for k in z.files if k not in ('xs', 'ys', 'zs')]
    stack = np.stack([z[k] for k in names])
    return xs, ys, zs, names, stack.min(0), stack.argmin(0).astype(np.uint8)

def render(xs, ys, zs, names, S, lab, az, el, H=900, Wd=700, scale=None, ctr=(0, 0, 15.8)):
    vox = xs[1] - xs[0]; o = np.array([xs[0], ys[0], zs[0]])
    def samp(P, vol=S, order=1):
        idx = ((P - o) / vox).T
        return map_coordinates(vol, idx, order=order, mode='nearest')
    a, e = np.radians(az), np.radians(el)
    fwd = np.array([np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), -np.sin(e)])       # az 0 = looking at the face
    right = np.array([np.cos(a), -np.sin(a), 0.0]); up = np.cross(right, fwd)
    scale = scale or 36.0 / H
    ctr = np.array(ctr, float)
    u = (np.arange(Wd) - Wd / 2) * scale; v = (H / 2 - np.arange(H)) * scale
    U, V = np.meshgrid(u, v)
    P = ctr + U[..., None] * right + V[..., None] * up - fwd * 30
    P = P.reshape(-1, 3); D = np.broadcast_to(fwd, P.shape)
    t = np.zeros(len(P)); hit = np.zeros(len(P), bool); alive = np.ones(len(P), bool)
    for _ in range(220):
        idx = np.where(alive)[0]
        if not len(idx): break
        q = P[idx] + D[idx] * t[idx, None]
        d = samp(q)
        h = d < 0.01; hit[idx[h]] = True; alive[idx[h]] = False
        t[idx] += np.maximum(d * 0.8, 0.01)
        alive[idx[t[idx] > 60]] = False
    img = np.full((len(P), 3), 255.0)
    hi = np.where(hit)[0]; q = P[hi] + D[hi] * t[hi, None]
    eps = vox * 0.8
    n = np.stack([samp(q + [eps, 0, 0]) - samp(q - [eps, 0, 0]), samp(q + [0, eps, 0]) - samp(q - [0, eps, 0]), samp(q + [0, 0, eps]) - samp(q - [0, 0, eps])], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    L = np.argmin(np.stack([np.abs(q[:, 0] * 0)]), 0)
    labs = samp(q - n * vox * 0.6, lab.astype(np.float32), order=0).astype(int)
    base = np.array([COL[names[k]] for k in labs], float)
    key = np.array([-0.45, -0.7, 0.75]); key /= np.linalg.norm(key)
    fill = np.array([0.7, -0.3, 0.2]); fill /= np.linalg.norm(fill)
    rim = np.clip(1 + n @ fwd, 0, 1) ** 3
    ao = np.clip(0.5 * (samp(q + n * 0.5) / 0.5 + samp(q + n * 1.4) / 1.4), 0, 1) ** 0.7
    # shadow from key light
    sh = np.ones(len(q)); ts = np.full(len(q), 0.25); al = np.ones(len(q), bool)
    for _ in range(60):
        ii = np.where(al)[0]
        if not len(ii): break
        d = samp(q[ii] + n[ii] * 0.05 + key * ts[ii, None])
        blk = d < 0.02; sh[ii[blk]] = 0.35; al[ii[blk]] = False
        ts[ii] += np.maximum(d, 0.05); al[ii[ts[ii] > 25]] = False
    diff = np.clip(n @ key, 0, 1) * sh
    lum = 0.22 + 0.62 * diff + 0.18 * np.clip(n @ fill, 0, 1) + 0.12 * rim
    hv = (key - fwd); hv /= np.linalg.norm(hv)
    spec = 0.18 * np.clip(n @ hv, 0, 1) ** 24 * sh
    img[hi] = np.clip(base * (lum * (0.55 + 0.45 * ao))[:, None] + 255 * spec[:, None], 0, 255)
    return Image.fromarray(img.reshape(H, Wd, 3).astype(np.uint8))

if __name__ == '__main__':
    xs, ys, zs, names, S, lab = load(sys.argv[1])
    views = [tuple(map(float, s.split(','))) for s in sys.argv[3:]] or [(0, 10), (-35, 15), (90, 10), (180, 15)]
    ims = [render(xs, ys, zs, names, S, lab, a, e) for a, e in views]
    out = Image.new('RGB', (sum(i.width for i in ims), ims[0].height), 'white')
    x = 0
    for im in ims: out.paste(im, (x, 0)); x += im.width
    out.save(sys.argv[2]); print('saved', sys.argv[2], out.size)
