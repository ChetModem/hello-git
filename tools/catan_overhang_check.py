"""Layer-by-layer overhang check and fill for the tile (world z, object-local xy)."""
import re, numpy as np, trimesh, pickle, sys
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry import Polygon
D = sys.argv[1]; ANGLE = float(sys.argv[2]) if len(sys.argv) > 2 else 55.0
o = open(f'{D}/3D/Objects/object_3048.model').read(); s = open(f'{D}/3D/3dmodel.model').read()
it = list(map(float, re.search(r'<item objectid="5"[^>]*transform="([^"]*)"', s).group(1).split()))
comps = dict(re.findall(r'<component p:path="[^"]+" objectid="(\d+)"[^>]*transform="([^"]*)"', s))
def mesh(cid):
    i = o.find(f'<object id="{cid}"'); b = o[i:o.find('</object>', i)]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float) + list(map(float, comps[cid].split()[9:12])); v[:, 2] += it[11]
    return trimesh.Trimesh(v, np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int), process=False)
solids = [mesh(c) for c in comps if c in ('1', '2', '3', '4', '6')]          # '6' = overhang fill, if present
def sec(m, z):
    S = m.section([0, 0, 1], [0, 0, z])
    if S is None: return None
    q, T = S.to_2D(); return affinity.affine_transform(unary_union(q.polygons_full), [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]])
H = 0.08; zs = np.arange(3.0 + H / 2, max(m.bounds[1][2] for m in solids), H)
L = [unary_union([g for m in solids for g in [sec(m, z)] if g is not None and not g.is_empty]).buffer(0) for z in zs]
reach = H * np.tan(np.radians(ANGLE))
def clean(g, a=0.05):
    g = g.buffer(-0.03).buffer(0.03)
    gs = list(g.geoms) if hasattr(g, 'geoms') else [g]
    return unary_union([x for x in gs if x.area > a])
# overhang check: area of each layer not within `reach` of the layer below
over = []
below0 = unary_union([g for m in solids for g in [sec(m, 2.96)] if g is not None])
for k, z in enumerate(zs):
    below = L[k - 1] if k else below0
    u = clean(L[k].difference(below.buffer(reach)))
    over.append(u)
tot = sum(u.area for u in over)
print(f'overhang check at {ANGLE:.0f} deg: unsupported area summed over layers {tot:.1f} mm2, layers affected {sum(1 for u in over if u.area > 0)} of {len(zs)}')
pickle.dump({'zs': zs, 'L': L, 'over': over, 'reach': reach, 'it': it}, open(f'{D}/../overhang_{ANGLE:.0f}.pkl', 'wb'))
