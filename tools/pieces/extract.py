"""Pull the settlement, city and road meshes out of the player-pieces file and draw their silhouettes from the front,
side and top (each view = union of the projected triangles)."""
import zipfile, re, sys, pickle, numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
F = '/home/user/hello-git/catan-player-pieces-0.2nozzle-v2.3mf'
z = zipfile.ZipFile(F); S = z.read('3D/3dmodel.model').decode()
cache = {}
def objfile(path):
    if path not in cache: cache[path] = z.read(path.lstrip('/')).decode()
    return cache[path]
def mesh(path, oid):
    o = objfile(path); i = o.find(f'<object id="{oid}"'); b = o[i:o.find('</object>', i)]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float)
    t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int)
    return v, t
def piece(oid):
    i = S.find(f'<object id="{oid}"'); b = S[i:S.find('</object>', i)]
    V, T = [], []; n = 0
    for path, cid, tr in re.findall(r'<component p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]+)"', b):
        v, t = mesh(path, cid); m = np.array(tr.split(), float)
        R = m[:9].reshape(3, 3); v = v @ R + m[9:12]
        V.append(v); T.append(t + n); n += len(v)
    return np.vstack(V), np.vstack(T)
def silhouette(v, t, axes):
    tris = [Polygon(v[f][:, axes]) for f in t]
    tris = [p for p in tris if p.is_valid and p.area > 1e-6]
    return unary_union(tris).buffer(0.01).buffer(-0.01)
out = {}
for name, oid in (('settlement', '15'), ('city', '4'), ('road', '33')):
    v, t = piece(oid); b = v.min(0), v.max(0)
    print(name, 'size x %.1f y %.1f z %.1f' % tuple(b[1] - b[0]), 'triangles', len(t))
    out[name] = {k: silhouette(v, t, ax) for k, ax in (('front', [0, 2]), ('side', [1, 2]), ('top', [0, 1]))}
pickle.dump(out, open('silhouettes.pkl', 'wb'))
