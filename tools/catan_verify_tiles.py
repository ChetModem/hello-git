"""Independent checks on a fixed tiles folder (re-reads everything from disk)."""
import re, glob, os, sys, json, numpy as np, trimesh, xml.dom.minidom as xm
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry import Polygon
D = sys.argv[1]; ok = True
def bad(msg):
    global ok; ok = False; print('FAIL', msg)
for f in glob.glob(f'{D}/3D/Objects/*.model') + [f'{D}/3D/3dmodel.model', f'{D}/Metadata/model_settings.config']:
    try: xm.parse(f)
    except Exception as e: bad(f'xml {f}: {e}')
rels = open(f'{D}/3D/_rels/3dmodel.model.rels').read()
FILES = {os.path.basename(f): open(f).read() for f in glob.glob(f'{D}/3D/Objects/*.model')}
for fn in FILES:
    if f'/3D/Objects/{fn}' not in rels: bad(f'{fn} missing from rels')
paint = sum(t.count('paint_color') for t in FILES.values()); print('paint attributes left:', paint); paint and bad('paint left')
def mesh(fn, cid):
    o = FILES[fn]; i = o.find(f'<object id="{cid}"'); b = o[i:o.find('</object>', i)]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float); t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int)
    return trimesh.Trimesh(v, t, process=False) if len(t) else None
nm = 0
for fn, o in FILES.items():
    for cid in re.findall(r'<object id="(\d+)"', o):
        m = mesh(fn, cid)
        if m is None: continue
        nm += 1
        if not m.is_watertight: bad(f'{fn}#{cid} not watertight')
        if not m.is_winding_consistent: bad(f'{fn}#{cid} winding')
        if (m.area_faces < 1e-10).sum(): print(f'note {fn}#{cid}: {(m.area_faces < 1e-10).sum()} zero-area faces')
print('mesh objects checked:', nm)
S = open(f'{D}/3D/3dmodel.model').read(); MS = open(f'{D}/Metadata/model_settings.config').read()
for oid, tr in re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"', S):
    a = np.array(list(map(float, tr.split())))
    if abs(a[2]) > 1e-9 or abs(a[5]) > 1e-9 or abs(a[6]) > 1e-9 or abs(a[7]) > 1e-9 or abs(a[8] - 1) > 1e-9: bad(f'item {oid} still tilted')
    ob = S[S.find(f'<object id="{oid}"'):]; ob = ob[:ob.find('</object>')]
    nc = len(re.findall(r'<component ', ob))
    mo = re.search(rf'<object id="{oid}">.*?</object>', MS, re.S).group(0); npart = len(re.findall(r'<part id=', mo))
    nv = len(re.findall(rf'<assemble_item object_id="{oid}" volume_id=', MS))
    if not (nc == npart and (nv == 0 or nv == nc)): bad(f'object {oid}: components {nc}, parts {npart}, assemble volumes {nv}')
    for path, cid in re.findall(r'p:path="([^"]+)" objectid="(\d+)"', ob):
        if f'<object id="{cid}"' not in FILES.get(path.split('/')[-1], ''): bad(f'object {oid} references missing mesh {path}#{cid}')
print('items checked:', len(re.findall(r'<item ', S)), '| overall:', 'PASS' if ok else 'FAIL')
