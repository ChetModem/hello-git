"""Catan base for 5x3 mm disc magnets, inserted after printing like the original:
each D pocket has a 5.6 x 5.2 mm channel from the inside of the hex, closed by a
printed plug that restores the rim and leaves the round end of the D for the magnet."""
import sys, numpy as np, trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
SRC, OUT_BASE, OUT_ALL = sys.argv[1:4]
FLOOR, CAV, D_W, WALL, FIT = 0.4, 5.2, 6.3, 1.0, 0.1   # D_W must exceed the disc diagonal sqrt(5^2+3^2)=5.83 to let it turn

m = trimesh.load(SRC); m.merge_vertices()
trimesh.repair.fix_normals(m); trimesh.repair.fill_holes(m)
m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
c = (m.bounds[0][:2] + m.bounds[1][:2]) / 2
APO = m.bounds[1][0] - c[0]
# keep only the hex body (drop the designer's old plugs printed in the centre)
parts = m.split(only_watertight=False)
body = max(parts, key=lambda p: p.volume)
print('designer file: %d bodies; keeping the hex (%.0f mm3), dropping %d old plugs' % (len(parts), body.volume, len(parts) - 1))

sec = body.section([0, 1, 0], [0, c[1] + 12, 0])
rim = max((Polygon(np.c_[np.asarray(l)[:, 0] - c[0], np.asarray(l)[:, 2]]) for l in sec.discrete
           if np.asarray(l)[:, 0].mean() > c[0]), key=lambda p: p.area).buffer(0)
rim = rim.intersection(box(25, -1, APO, 10))
r_in = rim.bounds[0]

def extrude_rz(poly, t0, t1):
    e = trimesh.creation.extrude_polygon(poly, t1 - t0)
    v = e.vertices.copy(); e.vertices = np.c_[v[:, 0], v[:, 2] + t0, v[:, 1]]
    if e.volume < 0: e.invert()
    return e

def to_edge(mesh, ang):
    R = trimesh.transformations.rotation_matrix(np.radians(ang), [0, 0, 1])
    T = trimesh.transformations.translation_matrix([c[0], c[1], 0])
    o = mesh.copy(); o.apply_transform(T @ R); return o

rb = APO - WALL; rc = rb - D_W / 2           # D flat face and round-end centre
D = unary_union([box(rc, -D_W / 2, rb, D_W / 2), Point(rc, 0).buffer(D_W / 2, quad_segs=32)])
chan = box(r_in - 1, -D_W / 2, rc, D_W / 2)  # straight channel from the inside to the D
cut2d = unary_union([D, chan])
cut = trimesh.creation.extrude_polygon(cut2d, CAV); cut.vertices[:, 2] += FLOOR
plugfill = extrude_rz(rim, -4.2, 4.2)        # fill the old slot with plain rim first

angles = [0, 60, 120, 180, 240, 300]
base = trimesh.boolean.union([body] + [to_edge(plugfill, a) for a in angles], engine='manifold')
base = trimesh.boolean.difference([base] + [to_edge(cut, a) for a in angles], engine='manifold')

# plug = rim cross-section inside the channel (z FLOOR..FLOOR+CAV), minus the round end of the D,
# shrunk by FIT on the sides, top and bottom so it pushes in
win = box(r_in - 1, FLOOR + FIT, rc, FLOOR + CAV - FIT)
prof = rim.intersection(win)
plug = extrude_rz(prof, -D_W / 2 + FIT, D_W / 2 - FIT)
roundend = trimesh.creation.cylinder(radius=D_W / 2, height=20, sections=96)
roundend.apply_translation([rc, 0, 3])
plug = trimesh.boolean.difference([plug, roundend], engine='manifold')
print('plug: %.2f (r) x %.2f (t) x %.2f (z) mm, volume %.1f mm3' % tuple(list(plug.extents) + [plug.volume]))

# lay plugs flat for printing (channel side-face down) in the centre of the hex, like the original
flat = plug.copy()
flat.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-90), [1, 0, 0]))
flat.apply_translation(-flat.bounds[0])
w, d = flat.extents[0], flat.extents[1]
plugs = []
for i in range(6):
    p = flat.copy(); p.apply_translation([c[0] - 1.5 * w - 2 + (i % 3) * (w + 2), c[1] - d - 1 + (i // 3) * (d + 2), 0])
    plugs.append(p)
allm = trimesh.util.concatenate([base] + plugs)
inside = all(np.linalg.norm(p.bounds.mean(0)[:2] - c) < 22 for p in plugs)
print('base watertight', base.is_watertight, '| plugs sit in the centre opening:', inside, '| plug footprint %.1f x %.1f, height %.1f' % (w, d, flat.extents[2]))
base.export(OUT_BASE); allm.export(OUT_ALL)
