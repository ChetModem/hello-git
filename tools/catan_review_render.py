"""Draw face (as seen after flipping) and back of the first card in each print file, all at one scale,
and measure every card's icon: size, area, centre offset, colours, corner hexes."""
import zipfile, re, json, sys, numpy as np, trimesh, pickle
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry import box, Point
from PIL import Image, ImageDraw, ImageFont
R = '/home/user/hello-git/'
FILES = [('Brick', R + 'finished/FINISHED-catan-brick-19-cards.3mf', None), ('Wood', R + 'catan-wood-19-cards.3mf', None),
         ('Sheep', R + 'finished/FINISHED-catan-sheep-19-cards.3mf', None), ('Wheat', R + 'catan-wheat-19-cards.3mf', None),
         ('Ore', R + 'catan-ore-19-cards.3mf', None),
         ('Knight', R + 'catan-knight-14-cards.3mf', None), ('Victory Point', R + 'catan-victory-point-5-cards.3mf', None),
         ('Road Building', R + 'catan-road-building-2-cards.3mf', None), ('Year of Plenty', R + 'catan-year-of-plenty-2-cards.3mf', None),
         ('Monopoly', R + 'catan-monopoly-2-cards.3mf', None),
         ('Building Costs', R + 'catan-special-cards-6.3mf', 'Building Costs 1'), ('Longest Road', R + 'catan-special-cards-6.3mf', 'Longest Road'),
         ('Largest Army', R + 'catan-special-cards-6.3mf', 'Largest Army')]
def mat(tr):
    a = list(map(float, tr.split())); M = np.eye(4); M[:3, :3] = np.array(a[:9]).reshape(3, 3).T; M[:3, 3] = a[9:12]; return M
def sec(m, z):
    s = m.section([0, 0, 1], [0, 0, z])
    if s is None: return None
    q, T = s.to_2D(); return affinity.affine_transform(unary_union(q.polygons_full), [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]]).buffer(0)
def load(fn, want):
    z = zipfile.ZipFile(fn); S = z.read('3D/3dmodel.model').decode(); MS = z.read('Metadata/model_settings.config').decode()
    O = {n.split('/')[-1]: z.read(n).decode() for n in z.namelist() if n.startswith('3D/Objects/')}
    P = json.loads(z.read('Metadata/project_settings.config')); cols = P['filament_colour']
    for oid, tr in re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"', S):
        mo = re.search(rf'<object id="{oid}">.*?</object>', MS, re.S).group(0)
        name = re.search(r'key="name" value="([^"]+)"', mo).group(1)
        if want and name != want: continue
        oext = int(re.search(r'key="extruder" value="(\d+)"', mo[:mo.find('<part')]).group(1))
        parts = re.findall(r'<part id="\d+" subtype="(\w+)"[^>]*>(.*?)</part>', mo, re.S)
        ob = S[S.find(f'<object id="{oid}"'):]; ob = ob[:ob.find('</object>')]
        comps = re.findall(r'p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]*)"', ob)
        M = mat(tr); byz = {}
        for (path, cid, ctr), (st, body) in zip(comps, parts):
            o = O[path.split('/')[-1]]; i = o.find(f'<object id="{cid}"'); b = o[i:o.find('</object>', i)]
            m = trimesh.Trimesh(np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float), np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int), process=False)
            m.apply_transform(M @ mat(ctr)); ex = re.search(r'key="extruder" value="(\d+)"', body); ex = int(ex.group(1)) if ex else oext
            pn = re.search(r'key="name" value="([^"]+)"', body).group(1); byz.setdefault(ex, []).append((pn, m))
        allm = trimesh.util.concatenate([m for v in byz.values() for _, m in v]); b = allm.bounds
        cx, cy = (b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2; z0 = b[0][2]; z1 = b[1][2]
        face = {}; back = {}
        for ex, ms in byz.items():
            f = unary_union([g for _, m in ms for g in [sec(m, z0 + 0.1)] if g is not None])
            bk = unary_union([g for _, m in ms for g in [sec(m, z1 - 0.05)] if g is not None])
            # face view = looking at the plate side: mirror x about the card centre
            face[ex] = affinity.translate(affinity.scale(f, -1, 1, origin=(cx, cy)), -cx, -cy)
            back[ex] = affinity.translate(bk, -cx, -cy)
        corner_names = [pn for ex, ms in byz.items() for pn, _ in ms if 'orner' in pn]
        return dict(name=name, face=face, back=back, cols=cols, corners=bool(corner_names), size=(b[1][0] - b[0][0], b[1][1] - b[0][1], z1 - z0))
data = {}
for label, fn, want in FILES:
    data[label] = load(fn, want); print(label, 'loaded', [round(v, 2) for v in data[label]['size']])
pickle.dump(data, open('cards.pkl', 'wb'))
