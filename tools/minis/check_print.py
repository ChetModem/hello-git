"""Printability check on a sampled solid (upright, 0.1 mm grid): islands (parts that start in mid-air)
and overhang regions steeper than 45 degrees, grouped in 3D and reported by location and size.

    python3 check_print.py bobby_fields_0.1.npz
"""
import sys, numpy as np
from scipy import ndimage as nd
d = np.load(sys.argv[1]); xs, ys, zs = d['xs'], d['ys'], d['zs']
solid = np.min(np.stack([d[k] for k in d.files if k not in ('xs', 'ys', 'zs')]), 0) < 0
vox = float(xs[1] - xs[0])
k = int(round(0.1 / vox))                   # 45 deg: each 0.1 mm layer may step out 0.1 mm
st = nd.generate_binary_structure(2, 1)
over = np.zeros_like(solid); islands = []
z0 = int(np.argmax(solid.any((0, 1))))
for i in range(z0 + 1, solid.shape[2]):
    cur, below = solid[:, :, i], solid[:, :, i - 1]
    sup = nd.binary_dilation(below, st, iterations=max(k, 1))
    over[:, :, i] = cur & ~sup
    lab, n = nd.label(cur)
    for j in range(1, n + 1):
        m = lab == j
        if not (m & below).any():
            c = np.argwhere(m).mean(0)
            islands.append((zs[i], xs[int(c[0])], ys[int(c[1])], m.sum() * vox * vox))
print('islands (start in mid-air):')
for z, x, y, a in islands: print(f'  z {z:5.1f}  at x {x:5.1f} y {y:5.1f}  area {a:.2f} mm2')
lab, n = nd.label(over, nd.generate_binary_structure(3, 3))
regs = []
for j, sl in enumerate(nd.find_objects(lab), 1):
    m = lab[sl] == j; a = m.sum() * vox * vox
    if a < 0.4: continue
    c = np.argwhere(m).mean(0) + [s.start for s in sl]
    regs.append((a, zs[sl[2].start], zs[sl[2].stop - 1], xs[int(c[0])], ys[int(c[1])], zs[int(c[2])]))
print('overhang regions > 45 deg (projected area mm2, z range, centre):')
for a, za, zb, x, y, z in sorted(regs, reverse=True)[:25]: print(f'  {a:6.1f} mm2  z {za:5.1f}-{zb:5.1f}  centre ({x:5.1f},{y:5.1f},{z:5.1f})')
# thin features: solid whose local thickness is under ~0.8 mm (two nozzle lines)
dist = nd.distance_transform_edt(solid) * vox
thick = nd.maximum_filter(dist, size=int(round(1.2 / vox)))
thin = solid & (thick < 0.4)
lab, n = nd.label(thin, nd.generate_binary_structure(3, 3))
print('thin spots (< 0.8 mm thick):')
for j, sl in enumerate(nd.find_objects(lab), 1):
    m = lab[sl] == j; v = m.sum() * vox ** 3
    if v < 0.01: continue
    c = np.argwhere(m).mean(0) + [s.start for s in sl]
    print(f'  {v:6.3f} mm3 at ({xs[int(c[0])]:5.1f},{ys[int(c[1])]:5.1f},{zs[int(c[2])]:5.1f})')
