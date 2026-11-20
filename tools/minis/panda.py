"""Original panda adventurer mini (28-32 mm scale) on a 25 mm base: chubby panda with a bamboo staff and a satchel.
Colour parts are solid and do not overlap: green staff > black details > white body > grey base."""
import numpy as np, trimesh
from trimesh.creation import icosphere, cylinder, capsule, box
def ell(c, r, rot=None, sub=4):
    m = icosphere(subdivisions=sub, radius=1.0); m.apply_scale(r)
    if rot is not None: m.apply_transform(rot)
    m.apply_translation(c); return m
def rot(axis, deg): return trimesh.transformations.rotation_matrix(np.radians(deg), axis)
def limb(a, b, r):
    a, b = np.array(a, float), np.array(b, float); v = b - a; L = np.linalg.norm(v)
    m = capsule(height=L, radius=r, count=[24, 24]); z = np.array([0, 0, 1.0]); ax = np.cross(z, v / L)
    if np.linalg.norm(ax) > 1e-9: m.apply_transform(trimesh.transformations.rotation_matrix(np.arccos(np.dot(z, v / L)), ax))
    m.apply_translation((a + b) / 2); return m
U = lambda ms: trimesh.boolean.union(ms, engine='manifold')
D = lambda a, b: trimesh.boolean.difference([a, b], engine='manifold')
I = lambda ms: trimesh.boolean.intersection(ms, engine='manifold')

BASE_T = 2.5
base = U([cylinder(radius=12.5, height=2.0, sections=96).apply_translation([0, 0, 1.0]),
          cylinder(radius=12.0, height=0.5, sections=96).apply_translation([0, 0, 2.25])])

# white: round body, head, muzzle
body = ell([0, 0, 12.2], [8.6, 7.6, 9.4])
head = ell([0, -0.6, 24.2], [7.3, 7.0, 6.9])
muzzle = ell([0, -6.3, 22.6], [3.3, 2.3, 2.3])
white = U([body, head, muzzle])

# black: legs, arms, ears, eye patches, nose, strap, satchel
legs = [limb([s * 3.7, -0.6, BASE_T + 1.2], [s * 3.9, -0.4, 7.0], 3.1) for s in (-1, 1)]
feet = [ell([s * 3.9, -1.6, BASE_T + 1.1], [3.0, 3.6, 1.4]) for s in (-1, 1)]
STAFF_X, STAFF_Y = 10.2, -3.6
arm_r = limb([7.0, -0.4, 18.2], [STAFF_X - 0.4, STAFF_Y + 0.4, 16.0], 2.35)             # raised: holds the staff
hand_r = ell([STAFF_X - 0.3, STAFF_Y + 0.2, 16.0], [2.5, 2.4, 2.7])
arm_l = limb([-7.0, -0.4, 18.2], [-8.6, -2.6, 11.4], 2.35)                              # resting by the satchel
hand_l = ell([-8.5, -2.9, 10.9], [2.4, 2.4, 2.4])
ears = [ell([s * 5.3, 0.2, 29.6], [2.6, 1.6, 2.6]) for s in (-1, 1)]
shell = ell([0, -0.6, 24.2], [7.65, 7.35, 7.25])                                        # just proud of the head surface
patches = [I([ell([s * 2.75, -6.0, 25.0], [2.0, 2.4, 2.7], rot([0, 1, 0], s * 28)), shell]) for s in (-1, 1)]
nose = ell([0, -8.45, 23.5], [1.35, 0.9, 0.95])
strap_band = box(extents=[2.0, 40, 40]); strap_band.apply_transform(rot([0, 1, 0], -38)); strap_band.apply_translation([0, 0, 13.5])
strap = I([D(ell([0, 0, 12.2], [9.1, 8.1, 9.9]), body), strap_band])
satchel = U([box(extents=[3.2, 4.6, 4.4]).apply_translation([-7.9, -0.6, 9.4])]).apply_transform(rot([0, 0, 1], 0))
satchel = I([satchel, ell([-6.4, -0.6, 9.6], [3.6, 3.6, 3.4])]) if False else satchel
black = U(legs + feet + [arm_r, hand_r, arm_l, hand_l] + ears + patches + [nose, strap, satchel])

# white eye glints inside the patches (1.3 mm: big enough to print)
glints = [I([ell([s * 2.45, -6.6, 25.6], [0.65, 1.2, 0.75]), ell([0, -0.6, 24.2], [7.75, 7.45, 7.35])]) for s in (-1, 1)]

# green: bamboo staff with node rings and a small top leaf
staff = U([cylinder(radius=1.35, height=32.0, sections=40).apply_translation([STAFF_X, STAFF_Y, BASE_T + 16.0])] +
          [cylinder(radius=1.75, height=0.7, sections=40).apply_translation([STAFF_X, STAFF_Y, z]) for z in (8.0, 14.0, 22.5, 28.5)] +
          [ell([STAFF_X + 1.6, STAFF_Y, BASE_T + 31.0], [2.6, 0.9, 1.1], rot([0, 1, 0], -30))])

green = staff
black = D(D(black, green), U(glints))
white = D(D(U([white] + glints), black), green)
base = D(D(D(base, green), black), white)
parts = {'base': (6, base), 'white': (2, white), 'black': (1, black), 'green': (7, green)}
for n, (slot, m) in parts.items():
    assert m.is_watertight, n
    print(f'{n:6s} filament {slot}  volume {m.volume:6.0f} mm3  z {m.bounds[0][2]:.1f}-{m.bounds[1][2]:.1f}')
allm = trimesh.util.concatenate([m for _, m in parts.values()]); b = allm.bounds
print('mini %.1f x %.1f x %.1f mm' % tuple(b[1] - b[0]))
import pickle; pickle.dump({k: (s, (m.vertices, m.faces)) for k, (s, m) in parts.items()}, open('panda_parts.pkl', 'wb'))
