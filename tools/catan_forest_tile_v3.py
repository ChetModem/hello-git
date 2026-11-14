import re, os, subprocess, numpy as np, trimesh, xml.dom.minidom as xm
from shapely.ops import unary_union
from shapely import affinity
SP = os.path.dirname(os.path.abspath(__file__)); D = f'{SP}/tree_x2d'
s = open(f'{D}/3D/3dmodel.model').read(); p = f'{D}/3D/Objects/object_3048.model'; o = open(p).read()
it = list(map(float, re.search(r'<item objectid="5"[^>]*transform="([^"]*)"', s).group(1).split()))
comps = dict(re.findall(r'<component p:path="[^"]+" objectid="(\d+)"[^>]*transform="([^"]*)"', s))
def mesh(cid):
    i = o.find(f'<object id="{cid}"'); b = o[i:o.find('</object>', i)]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float) + list(map(float, comps[cid].split()[9:12]))
    return trimesh.Trimesh(v, np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int))
def sec(m, zw):
    S = m.section([0, 0, 1], [0, 0, zw - it[11]])
    if S is None: return None
    q, T = S.to_2D(); return affinity.affine_transform(unary_union(q.polygons_full), [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]])
outline = sec(mesh('1'), 1.0)
excl = []
for cid in ('2', '4'):                         # trees, and the house / stones detail part
    m = mesh(cid)
    for zw in np.arange(3.02, 15.2, 0.1):
        g = sec(m, zw)
        if g is not None and not g.is_empty: excl.append(g)
footprint = unary_union(excl).buffer(0.6)
area = outline.buffer(-0.3).difference(footprint).buffer(-0.05).buffer(0.05)
area = unary_union([g for g in (area.geoms if hasattr(area, 'geoms') else [area]) if g.area > 2])
Z0, Z1 = 2.0, 6.9                              # world height: recess floor up to the top of the ground
ms_ = []
for g in (area.geoms if hasattr(area, 'geoms') else [area]):
    e = trimesh.creation.extrude_polygon(g.simplify(0.05), Z1 - Z0); e.vertices[:, 2] += Z0 - it[11]; ms_.append(e)
mod = trimesh.util.concatenate(ms_)
if mod.volume < 0: mod.invert()
print(f'ground ironing area {area.area:.0f} mm2 of {outline.area:.0f} (trees + house excluded: {footprint.intersection(outline).area:.0f} mm2), pieces {len(ms_)}, watertight {mod.is_watertight}')
i = o.find('<object id="5"'); j = o.find('</object>', i); b = o[i:j]
vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in mod.vertices)
tx = ''.join(f'<triangle v1="{a}" v2="{c}" v3="{e}"/>\n' for a, c, e in mod.faces)
b = re.sub(r'<vertices>.*?</vertices>', lambda _: '<vertices>\n' + vx + '</vertices>', b, flags=re.S)
b = re.sub(r'<triangles>.*?</triangles>', lambda _: '<triangles>\n' + tx + '</triangles>', b, flags=re.S)
open(p, 'w').write(o[:i] + b + o[j:])
mset = open(f'{D}/Metadata/model_settings.config').read()
mset = mset.replace('value="Recess ironing"', 'value="Ground ironing"')
mset = re.sub(r'(<metadata key="name" value="Ground ironing"/>.*?<mesh_stat face_count=")\d+', lambda x: x.group(1) + str(len(mod.faces)), mset, flags=re.S)
mset = mset.replace('value="Forest tile X2D test v2"', 'value="Forest tile X2D test v3"')
open(f'{D}/Metadata/model_settings.config', 'w').write(mset)
for f in ['Metadata/model_settings.config', '3D/Objects/object_3048.model']: xm.parse(f'{D}/{f}')
# picture of the ironing area for checking
from PIL import Image, ImageDraw
sc = 8; bx = outline.bounds; im = Image.new('RGB', (int((bx[2] - bx[0]) * sc) + 20, int((bx[3] - bx[1]) * sc) + 20), 'white'); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - bx[0]) * sc + 10, (bx[3] - y) * sc + 10)
d.polygon([P(*c) for c in outline.exterior.coords], fill=(120, 120, 120))
for g in (area.geoms if hasattr(area, 'geoms') else [area]):
    d.polygon([P(*c) for c in g.exterior.coords], fill=(90, 170, 255))
    for h in g.interiors: d.polygon([P(*c) for c in h.coords], fill=(120, 120, 120))
im.save(f'{SP}/ground_ironing.png')
out = '/home/user/hello-git/catan-forest-tile-x2d-test-v3.3mf'
if os.path.exists(out): os.remove(out)
subprocess.run(f"cd '{D}' && zip -q -X '{out}' '[Content_Types].xml' && zip -q -r -X '{out}' . -x '[Content_Types].xml'", shell=True, check=True)
