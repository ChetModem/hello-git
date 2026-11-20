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
# right paw raised to the mouth, holding a bamboo stalk across it (munching); left paw holds a druid staff
arm_r = limb([7.0, -0.4, 18.6], [5.2, -6.6, 21.0], 2.35)
hand_r = ell([4.9, -7.6, 21.3], [2.4, 2.2, 2.6])
STAFF_X, STAFF_Y = -10.4, -3.4
arm_l = limb([-7.0, -0.4, 18.2], [STAFF_X + 0.5, STAFF_Y + 0.5, 15.6], 2.35)
hand_l = ell([STAFF_X + 0.2, STAFF_Y + 0.2, 15.6], [2.5, 2.4, 2.7])
ears = [ell([s * 5.3, 0.2, 29.6], [2.6, 1.6, 2.6]) for s in (-1, 1)]
shell = ell([0, -0.6, 24.2], [7.65, 7.35, 7.25])                                        # just proud of the head surface
patches = [I([ell([s * 2.75, -6.0, 25.0], [2.0, 2.4, 2.7], rot([0, 1, 0], s * 28)), shell]) for s in (-1, 1)]
nose = ell([0, -8.45, 23.5], [1.35, 0.9, 0.95])
strap_band = box(extents=[2.0, 40, 40]); strap_band.apply_transform(rot([0, 1, 0], 38)); strap_band.apply_translation([0, 0, 13.5])
strap = I([D(ell([0, 0, 12.2], [9.1, 8.1, 9.9]), body), strap_band])
satchel = I([box(extents=[3.6, 5.0, 4.8]).apply_translation([7.9, -0.8, 9.2]), ell([7.6, -0.8, 9.4], [2.6, 3.2, 3.0])])   # rounded herb pouch on the right hip
satchel = I([satchel, ell([-6.4, -0.6, 9.6], [3.6, 3.6, 3.4])]) if False else satchel
black = U(legs + feet + [arm_r, hand_r, arm_l, hand_l] + ears + patches + [nose, strap, satchel])

# white eye glints inside the patches (1.3 mm: big enough to print)
glints = [I([ell([s * 2.45, -6.6, 25.6], [0.65, 1.2, 0.75]), ell([0, -0.6, 24.2], [7.75, 7.45, 7.35])]) for s in (-1, 1)]

# green: the bamboo stalk in the mouth (with node rings), the leaf wreath, the leaves on the staff
stalk_a, stalk_b = np.array([-1.6, -8.9, 22.6]), np.array([10.6, -8.2, 20.6])
bamboo = U([limb(stalk_a, stalk_b, 1.2)] + [limb(stalk_a + (stalk_b - stalk_a) * t, stalk_a + (stalk_b - stalk_a) * (t + 0.03), 1.55) for t in (0.62, 0.9)])
def leaf(c, ang_z, tilt=20, size=(2.3, 1.05, 1.1)):
    return ell(c, size, rot([0, 0, 1], ang_z) @ rot([0, 1, 0], tilt))
def ang_dist(a, b): return abs((a - b + 180) % 360 - 180)
vine = D(ell([0, -0.6, 28.0], [6.75, 6.45, 1.1]), ell([0, -0.6, 28.0], [5.9, 5.6, 2.0]))                        # thin vine ring
wreath = U([vine.intersection(ell([0, -0.6, 24.2], [9, 9, 9]))] +
           [leaf([6.3 * np.cos(np.radians(a)), -0.6 + 6.0 * np.sin(np.radians(a)), 28.3], a + 90, 25) for a in range(0, 360, 20)
            if ang_dist(a, 0) > 24 and ang_dist(a, 180) > 24])       # the ears (at the sides) stay clear
wreath = D(wreath, U(ears))
top = BASE_T + 33.5
staff_leaves = U([leaf([STAFF_X + 1.7 * np.cos(np.radians(a)), STAFF_Y + 1.7 * np.sin(np.radians(a)), top - 2.0 - (a % 120) / 60], a, 35) for a in range(0, 360, 60)])
# wood: the druid staff with a knotted head
wood = U([cylinder(radius=1.35, height=top - BASE_T, sections=40).apply_translation([STAFF_X, STAFF_Y, (BASE_T + top) / 2]),
          ell([STAFF_X, STAFF_Y, top], [2.0, 2.0, 1.8]), ell([STAFF_X, STAFF_Y, BASE_T + 9.0], [1.7, 1.7, 1.0])])
green = U([bamboo, wreath, staff_leaves])
green = D(green, wood)

black = D(D(D(black, green), wood), U(glints))
white = D(D(D(U([white] + glints), black), green), wood)
base = D(D(D(D(base, green), black), white), wood)
parts = {'base': (6, base), 'white': (2, white), 'black': (1, black), 'green': (7, green), 'wood': (4, wood)}
for n, (slot, m) in parts.items():
    assert m.is_watertight, n
    print(f'{n:6s} filament {slot}  volume {m.volume:6.0f} mm3  z {m.bounds[0][2]:.1f}-{m.bounds[1][2]:.1f}')
allm = trimesh.util.concatenate([m for _, m in parts.values()]); b = allm.bounds
print('mini %.1f x %.1f x %.1f mm' % tuple(b[1] - b[0]))
import pickle; pickle.dump({k: (s, (m.vertices, m.faces)) for k, (s, m) in parts.items()}, open('panda_druid_parts.pkl', 'wb'))
