"""Independent check of a built 3MF (reads only the file)."""
import sys, re, zipfile, json, numpy as np, trimesh, xml.dom.minidom as xm, io
from shapely.ops import unary_union
from shapely import affinity
from PIL import Image, ImageDraw
F = sys.argv[1]; OUT = sys.argv[2]
z = zipfile.ZipFile(F); names = z.namelist(); ok = True
def bad(m):
    global ok; ok = False; print('FAIL', m)
for n in names:
    if n.endswith('.model') or n.endswith('.config') and 'model_settings' in n:
        try: xm.parseString(z.read(n))
        except Exception as e: bad(f'xml {n} {e}')
S = z.read('3D/3dmodel.model').decode(); MS = z.read('Metadata/model_settings.config').decode()
O = {n.split('/')[-1]: z.read(n).decode() for n in names if n.startswith('3D/Objects/')}
rels = z.read('3D/_rels/3dmodel.model.rels').decode()
for fn in O:
    if f'/3D/Objects/{fn}' not in rels: bad(f'{fn} not in rels')
P = json.loads(z.read('Metadata/project_settings.config'))
cols = P['filament_colour']
def mesh(fn, cid):
    o = O[fn]; i = o.find(f'<object id="{cid}"'); b = o[i:o.find('</object>', i)]
    return trimesh.Trimesh(np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float), np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int), process=False)
def sec(m, zz):
    s = m.section([0, 0, 1], [0, 0, zz])
    if s is None: return None
    q, T = s.to_2D(); return affinity.affine_transform(unary_union(q.polygons_full), [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]]).buffer(0)
plates = {}
for k, p in enumerate(re.findall(r'<plate>.*?</plate>', MS, re.S), 1):
    for oid in re.findall(r'key="object_id" value="(\d+)"', p): plates[oid] = k
used = set(); report = []
for oid, tr in re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"', S):
    t = list(map(float, tr.split())); X, Y, Z = t[9:12]
    mo = re.search(rf'<object id="{oid}">.*?</object>', MS, re.S).group(0)
    name = re.search(r'key="name" value="([^"]+)"', mo).group(1)
    parts = re.findall(r'<part id="\d+" subtype="(\w+)"[^>]*>(.*?)</part>', mo, re.S)
    ob = S[S.find(f'<object id="{oid}"'):]; ob = ob[:ob.find('</object>')]
    comps = re.findall(r'p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]*)"', ob)
    nv = len(re.findall(rf'<assemble_item object_id="{oid}" volume_id=', MS))
    if not (len(comps) == len(parts) == nv): bad(f'{name}: components {len(comps)} parts {len(parts)} assemble {nv}')
    pl = plates.get(oid)
    if pl is None: bad(f'{name} on no plate')
    byext = {}; allm = []
    for (path, cid, ctr), (st, body) in zip(comps, parts):
        m = mesh(path.split('/')[-1], cid); m.apply_translation(np.array(list(map(float, ctr.split()[9:12]))) + [X - 307.2 * (pl - 1), Y, Z])
        if not m.is_watertight or not m.is_winding_consistent: bad(f'{name}: part {re.search(chr(34)+"name"+chr(34)+r" value="+chr(34)+"([^"+chr(34)+"]+)", body)} not closed')
        ex = int(re.search(r'key="extruder" value="(\d+)"', body).group(1)); used.add(ex)
        byext.setdefault(ex, []).append(m); allm.append(m)
    b = trimesh.util.concatenate(allm).bounds
    if b[0][0] < 0 or b[0][1] < 0 or b[1][0] > 256 or b[1][1] > 256: bad(f'{name}: outside the bed {np.round(b, 1)}')
    if abs(b[0][2]) > 1e-6: bad(f'{name}: not on the plate (z min {b[0][2]})')
    report.append((name, pl, byext, b))
    print(f'{name}: plate {pl}, x {b[0][0]:.1f}-{b[1][0]:.1f}, y {b[0][1]:.1f}-{b[1][1]:.1f}, z {b[0][2]:.2f}-{b[1][2]:.2f}, parts {len(parts)}, extruders {sorted(byext)}')
print('extruders used:', sorted(used), {e: cols[e - 1] for e in sorted(used)}, '| filament map', P['filament_map'][:9], P['filament_map_mode'])
# face layer colours: overlaps between colours (body ext 1 excluded) and thin pieces
def thin(g, w):
    r = g.buffer(-w / 2, join_style=2, mitre_limit=10).buffer(w / 2, join_style=2, mitre_limit=10)
    lost = g.difference(r).buffer(-0.01).buffer(0.01)
    return [round(p.area, 2) for p in (lost.geoms if hasattr(lost, 'geoms') else [lost]) if p.area > 0.12]
imgs = []
for name, pl, byext, b in report:
    if b[1][2] < 0.6 or 'legend' in name.lower() and 'stand' not in name.lower():
        L = {e: unary_union([g for m in ms for g in [sec(m, 0.1)] if g is not None]) for e, ms in byext.items()}
        Lb = {e: unary_union([g for m in ms for g in [sec(m, 0.25)] if g is not None]) for e, ms in byext.items()}
        col = {e: g for e, g in L.items() if e != 1 and not g.is_empty}
        ov = sum(col[a].intersection(col[c]).area for a in col for c in col if a < c)
        diff = sum(col[e].symmetric_difference(Lb.get(e)).area for e in col)
        tc = {e: thin(g, 0.58 if 'legend' not in name.lower() else 0.5) for e, g in col.items()}
        from shapely.strtree import STRtree
        ps = [(e, p) for e, g in col.items() for p in (g.geoms if hasattr(g, 'geoms') else [g]) if not p.is_empty]
        tree = STRtree([p for _, p in ps]); lim = 0.5 if 'legend' in name.lower() else 0.6; close = []
        for i, (e, p) in enumerate(ps):
            for j in tree.query(p.buffer(lim)):
                if j > i:
                    dd = p.distance(ps[j][1])
                    if dd < lim: close.append((round(dd, 2), e, ps[j][0], round(p.centroid.x, 1), round(p.centroid.y, 1)))
        print(f'  {name}: separate pieces closer than {lim} mm: {len(close)} {sorted(close)[:6]}')
        print(f'  {name}: colour overlap {ov:.3f} mm2, face vs backing mismatch {diff:.3f} mm2, thin bits {({e: v for e, v in tc.items() if v} if not "legend" in name.lower() else {e: len(v) for e, v in tc.items() if v}) or "none"}')
        # face view = looking at the plate side = mirror x
        base = unary_union([g for m in byext.get(1, []) for g in [sec(m, 0.1)] if g is not None])
        cx = (b[0][0] + b[1][0]) / 2; cy = (b[0][1] + b[1][1]) / 2; Sc = 8
        W = int((b[1][0] - b[0][0]) * Sc) + 10; H = int((b[1][1] - b[0][1]) * Sc) + 10
        img = Image.new('RGB', (W, H), (235, 235, 235))
        def draw(g, c):
            mask = Image.new('L', img.size, 0)
            for p in (g.geoms if hasattr(g, 'geoms') else [g]):
                if p.is_empty or p.geom_type != 'Polygon': continue
                t = Image.new('L', img.size, 0); d = ImageDraw.Draw(t)
                d.polygon([(W / 2 - (x - cx) * Sc, H / 2 - (y - cy) * Sc) for x, y in p.exterior.coords], fill=255)
                for h in p.interiors: d.polygon([(W / 2 - (x - cx) * Sc, H / 2 - (y - cy) * Sc) for x, y in h.coords], fill=0)
                mask.paste(255, (0, 0), t)
            img.paste(c, (0, 0), mask)
        draw(base, (20, 20, 20))
        for e, g in col.items():
            h = cols[e - 1].lstrip('#'); draw(g, tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
        imgs.append((name, img))
if imgs:
    Wt = sum(i.width for _, i in imgs[:6]) + 10 * len(imgs[:6]); Ht = max(i.height for _, i in imgs)
    sheet = Image.new('RGB', (min(Wt, 4000), Ht * ((len(imgs) + 5) // 6) + 10), 'white'); x = 0; y = 0
    for k, (n, i) in enumerate(imgs):
        if k and k % 6 == 0: x = 0; y += Ht + 10
        sheet.paste(i, (x, y)); x += i.width + 10
    sheet.save(OUT)
print('OVERALL', 'PASS' if ok else 'FAIL')
