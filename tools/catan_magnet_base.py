"""Swap the Catan base's 3x6 mm cylinder slots for enclosed D pockets that let a
5x3 mm disc magnet turn freely (OpenForge style), sealed with a print pause."""
import sys, numpy as np, trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
SRC, OUT = sys.argv[1], sys.argv[2]
FLOOR, CAV = 0.4, 5.2          # floor thickness, cavity height (roof = rim top - FLOOR - CAV)
D_W = 5.6                      # pocket width and round-end diameter (5 mm disc + clearance)
WALL = 1.0                     # wall between pocket and the outer edge face (OpenForge uses 1.0)

m = trimesh.load(SRC); m.merge_vertices()
trimesh.repair.fix_normals(m); trimesh.repair.fill_holes(m)
m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
assert m.is_watertight
c = (m.bounds[0][:2] + m.bounds[1][:2]) / 2
APO = m.bounds[1][0] - c[0]    # centre to flat outer face (39.5)

# rim cross-section between the old slots (plane y = c + 12, +x edge): polygon in (r, z)
sec = m.section([0, 1, 0], [0, c[1] + 12, 0])
loops = [np.asarray(e) for e in sec.discrete]
rim = max((Polygon(np.c_[l[:, 0] - c[0], l[:, 2]]) for l in loops if l[:, 0].mean() > c[0]), key=lambda p: p.area).buffer(0)
rim = rim.intersection(box(25, -1, APO, 10))
print('rim profile r %.2f..%.2f, z %.2f..%.2f' % (rim.bounds[0], rim.bounds[2], rim.bounds[1], rim.bounds[3]))

def extrude_rz(poly, t0, t1):
    """(r,z) polygon swept along t in [t0,t1] -> mesh in local frame (x=r, y=t, z=z)."""
    e = trimesh.creation.extrude_polygon(poly, t1 - t0)       # (x=r, y=z, z=t)
    v = e.vertices.copy(); e.vertices = np.c_[v[:, 0], v[:, 2] + t0, v[:, 1]]
    if e.volume < 0: e.invert()
    return e

def to_edge(mesh, ang):
    R = trimesh.transformations.rotation_matrix(np.radians(ang), [0, 0, 1])
    T = trimesh.transformations.translation_matrix([c[0], c[1], 0])
    out = mesh.copy(); out.apply_transform(T @ R); return out

plug = extrude_rz(rim, -4.2, 4.2)                     # fills the old 7 mm slot with the normal rim shape
rb = APO - WALL                                       # flat face of the D
D = unary_union([box(rb - D_W / 2, -D_W / 2, rb, D_W / 2), Point(rb - D_W / 2, 0).buffer(D_W / 2, quad_segs=32)])
pocket = trimesh.creation.extrude_polygon(D, CAV); pocket.vertices[:, 2] += FLOOR
angles = [0, 60, 120, 180, 240, 300]
out = trimesh.boolean.union([m] + [to_edge(plug, a) for a in angles], engine='manifold')
out = trimesh.boolean.difference([out] + [to_edge(pocket, a) for a in angles], engine='manifold')
print('result watertight', out.is_watertight, 'volume %.1f -> %.1f' % (m.volume, out.volume))
print('pocket: D %.1f wide x %.1f deep, floor %.1f, cavity %.1f tall (z %.1f..%.1f), roof %.2f; outer wall %.1f, inner wall %.2f'
      % (D_W, D_W, FLOOR, CAV, FLOOR, FLOOR + CAV, 6.0 - FLOOR - CAV, WALL, rb - D_W - 32.2))
out.export(OUT)
