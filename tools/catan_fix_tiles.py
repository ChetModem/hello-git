"""Fix every tile / piece in a Bambu 3MF project (extracted folder), in place.

1. Mesh repair on every mesh object: merge vertices, drop zero-area and duplicate
   triangles, delete stray fragments (<0.01 mm3 or <4 faces), close open bodies
   (pymeshfix), make normals consistent.
2. Remove colour painting (paint_color).
3. Level plate items that were tilted (keep only the rotation about z).
4. Flatten the number-token recess floor where the base mesh has small bumps.
5. Overhang fill: per printed object, layer by layer (0.08 mm), add material that
   slopes down at 55 deg under anything steeper, as a new grey part.
Writes a JSON report next to the folder.
"""
import re, json, glob, os, sys, uuid, pickle
import numpy as np, trimesh, pymeshfix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from split_edges import split_nonmanifold_edges
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry import Polygon, Point

D = sys.argv[1]
REPORT = {'repair': {}, 'items_levelled': [], 'recess': {}, 'fill': {}, 'warnings': []}
ANGLE, H = 55.0, 0.08
REACH = H * np.tan(np.radians(ANGLE))

# ---------------- helpers for mesh objects inside object files ----------------
FILES = {os.path.basename(f): open(f).read() for f in glob.glob(f'{D}/3D/Objects/*.model')}

def get_mesh(fn, cid):
    o = FILES[fn]; i = o.find(f'<object id="{cid}"'); b = o[i:o.find('</object>', i)]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float)
    t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int)
    return trimesh.Trimesh(v, t, process=False) if len(t) else None

def put_mesh(fn, cid, m):
    o = FILES[fn]; i = o.find(f'<object id="{cid}"'); j = o.find('</object>', i); b = o[i:j]
    vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in m.vertices)
    tx = ''.join(f'<triangle v1="{a}" v2="{c}" v3="{e}"/>\n' for a, c, e in m.faces)
    b = re.sub(r'<vertices>.*?</vertices>', lambda _: '<vertices>\n' + vx + '</vertices>', b, flags=re.S)
    b = re.sub(r'<triangles>.*?</triangles>', lambda _: '<triangles>\n' + tx + '</triangles>', b, flags=re.S)
    FILES[fn] = o[:i] + b + o[j:]

def add_mesh(fn, m):
    o = FILES[fn]
    nid = str(max(int(x) for x in re.findall(r'<object id="(\d+)"', o)) + 1)
    while any(f'<object id="{nid}"' in x for x in FILES.values()): nid = str(int(nid) + 1)
    vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in m.vertices)
    tx = ''.join(f'<triangle v1="{a}" v2="{c}" v3="{e}"/>\n' for a, c, e in m.faces)
    FILES[fn] = o.replace('</resources>', f' <object id="{nid}" p:UUID="{uuid.uuid4()}" type="model">\n  <mesh>\n   <vertices>\n{vx}   </vertices>\n   <triangles>\n{tx}   </triangles>\n  </mesh>\n </object>\n</resources>', 1)
    return nid

# ---------------- 1 + 2: repair every mesh, remove paint ----------------
for fn in list(FILES):
    for cid in re.findall(r'<object id="(\d+)"', FILES[fn]):
        m = get_mesh(fn, cid)
        if m is None: continue
        paint = FILES[fn].count('paint_color')
        before = dict(faces=len(m.faces), volume=round(float(m.volume), 2))
        m.merge_vertices()
        m.update_faces(m.nondegenerate_faces()); m.update_faces(m.unique_faces()); m.remove_unreferenced_vertices()
        bodies = m.split(only_watertight=False)
        keep, junk, closed = [], 0, 0
        for b in bodies:
            if len(b.faces) < 4 or abs(b.volume) < 0.01: junk += 1; continue
            if not b.is_watertight or not b.is_winding_consistent:
                u, cnt = np.unique(b.edges_sorted, axis=0, return_counts=True)
                if (cnt > 2).any():
                    sb, k = split_nonmanifold_edges(b)
                    if sb.is_watertight and abs(sb.volume - b.volume) < 1e-6:
                        REPORT['warnings'].append(f'{fn}#{cid}: {int((cnt > 2).sum())} edge(s) where surfaces touched; separated without moving any geometry')
                        b = sb; closed += 1; trimesh.repair.fix_normals(b); keep.append(b); continue
                mf = pymeshfix.MeshFix(b.vertices, b.faces); mf.repair()
                nb = trimesh.Trimesh(mf.points, mf.faces)
                if abs(nb.volume - b.volume) > max(0.1, 0.0005 * abs(b.volume)):
                    REPORT['warnings'].append(f'{fn}#{cid}: hole repair would change volume {b.volume:.2f}->{nb.volume:.2f}; left unchanged')
                    keep.append(b); continue
                REPORT['warnings'].append(f'{fn}#{cid}: body closed, volume {b.volume:.3f}->{nb.volume:.3f} mm3')
                b = nb; closed += 1
            trimesh.repair.fix_normals(b)
            if b.volume < 0: b.invert()
            keep.append(b)
        nm = trimesh.util.concatenate(keep)
        ok = all(b.is_watertight for b in keep) or any(f'{fn}#{cid}:' in w for w in REPORT['warnings'])
        changed = junk or closed or len(nm.faces) != before['faces']
        if changed or paint:
            put_mesh(fn, cid, nm)
        REPORT['repair'][f'{fn}#{cid}'] = dict(before=before, after=dict(faces=len(nm.faces), volume=round(float(nm.volume), 2)),
                                                 junk_removed=junk, bodies_closed=closed, all_watertight=ok)
        if not ok: REPORT['warnings'].append(f'{fn}#{cid} still has an open body after repair')
for fn in FILES: FILES[fn] = re.sub(r'\s+paint_color="[^"]*"', '', FILES[fn])

# ---------------- 3: level tilted plate items ----------------
S = open(f'{D}/3D/3dmodel.model').read(); MS = open(f'{D}/Metadata/model_settings.config').read()
NAMES = {oid: re.search(r'key="name" value="([^"]+)"', b).group(1) for oid, b in re.findall(r'<object id="(\d+)">(.*?)</object>', MS, re.S)}
def level(mt):
    a = list(map(float, mt.group(2).split())); R = np.array(a[:9]).reshape(3, 3)
    if abs(R[0, 2]) < 1e-9 and abs(R[1, 2]) < 1e-9 and abs(R[2, 0]) < 1e-9 and abs(R[2, 1]) < 1e-9: return mt.group(0)
    yaw = np.arctan2(R[0, 1], R[0, 0]); c, s_ = np.cos(yaw), np.sin(yaw)
    # 3MF stores the 3x3 part row-major as m00 m01 m02 m10 ... ; keep yaw, drop tilt
    new = [c, s_, 0, -s_, c, 0, 0, 0, 1] + a[9:]
    REPORT['items_levelled'].append(f'{NAMES.get(mt.group(1))} (object {mt.group(1)}): tilt {np.degrees(np.arccos(min(1, R[2, 2]))):.3f} deg removed')
    return mt.group(0).replace(mt.group(2), ' '.join(f'{x:.9g}' for x in new))
S = re.sub(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"[^>]*/>', level, S)

# ---------------- object geometry in object-local frame ----------------
def object_parts(oid):
    ob = S[S.find(f'<object id="{oid}"'):]; ob = ob[:ob.find('</object>')]
    out = []
    mo = re.search(rf'<object id="{oid}">.*?</object>', MS, re.S)
    subtypes = re.findall(r'<part id="\d+" subtype="(\w+)"', mo.group(0)) if mo else []
    for k, (path, cid, tr) in enumerate(re.findall(r'<component p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]*)"', ob)):
        if k < len(subtypes) and subtypes[k] != 'normal_part': continue      # modifiers are not solid
        m = get_mesh(path.split('/')[-1], cid)
        if m is None: continue
        m = m.copy(); m.apply_translation(list(map(float, tr.split()[9:12]))); out.append((path.split('/')[-1], cid, m))
    return out

def sec(m, z):
    Sx = m.section([0, 0, 1], [0, 0, z])
    if Sx is None: return None
    q, T = Sx.to_2D(); g = unary_union(q.polygons_full)
    return affinity.affine_transform(g, [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]])

# ---------------- 4: flatten token recess floors in base meshes ----------------
BASES = set()
for oid in NAMES:
    if f'<object id="{oid}"' not in S: continue
    parts = object_parts(oid)
    if not parts: continue
    for fn, cid, m in parts:
        if m.extents[0] > 70 and m.extents[1] > 60: BASES.add((fn, cid))   # full hex bases
for fn, cid in sorted(BASES):
    m = get_mesh(fn, cid); z0, z1 = m.bounds[0][2], m.bounds[1][2]
    found = None
    for z in np.arange(z0 + 0.3, z1, 0.05):
        g = sec(m, z)
        if g is None: continue
        for gg in (g.geoms if hasattr(g, 'geoms') else [g]):
            for h in gg.interiors:
                hp = Polygon(h); circ = 4 * np.pi * hp.area / hp.length ** 2
                if 450 < hp.area < 800 and circ > 0.95: found = (z, hp); break
            if found: break
        if found: break
    if not found: REPORT['recess'][f'{fn}#{cid}'] = 'no token recess'; continue
    z, hp = found; c = hp.centroid; r = np.sqrt(hp.area / np.pi)
    n = m.face_normals; tc = m.triangles_center
    inside = np.hypot(tc[:, 0] - c.x, tc[:, 1] - c.y) < r - 0.05
    up = inside & (n[:, 2] > 0.9) & (tc[:, 2] < z + 0.06)
    if not up.any(): REPORT['recess'][f'{fn}#{cid}'] = 'recess found, floor not found'; continue
    floor = float(np.min(m.triangles[up][:, :, 2]))
    vr = np.hypot(m.vertices[:, 0] - c.x, m.vertices[:, 1] - c.y)
    sel = (vr < r + 0.15) & (m.vertices[:, 2] > floor + 1e-4) & (m.vertices[:, 2] < floor + 0.15)
    info = dict(diameter=round(2 * r, 2), floor=round(floor - z0, 3), raised_vertices=int(sel.sum()),
                max_raise=round(float((m.vertices[sel, 2] - floor).max()), 3) if sel.any() else 0)
    if sel.any():
        v = m.vertices.copy(); v[sel, 2] = floor; nm = trimesh.Trimesh(v, m.faces, process=False)
        if nm.is_watertight: put_mesh(fn, cid, nm); info['fixed'] = True
        else: info['fixed'] = False; REPORT['warnings'].append(f'recess snap would open {fn}#{cid}; left as is')
    REPORT['recess'][f'{fn}#{cid}'] = info

# ---------------- 5: overhang check + fill per printed object ----------------
def safe_z(zall, z):
    """Move a slice height off any vertex height (trimesh mis-assembles loops when the plane grazes a vertex)."""
    for _ in range(40):
        i = np.searchsorted(zall, z)
        d = min(abs(zall[i - 1] - z) if i > 0 else 1, abs(zall[i] - z) if i < len(zall) else 1)
        if d > 4e-5: return z
        z += 1.3e-4
    return z

def layers_of(meshes, ztop, agree=False):
    """Layer outlines sampled at two heights per layer.
    agree=False: union of the two (for measuring overhangs; a missed piece would look like an overhang).
    agree=True: only where BOTH samples have material (for building fill). trimesh occasionally
    mis-joins a slice outline into a phantom region; a phantom in one sample must never become
    'material above' or fill grows under nothing and shows on the surface."""
    zs = np.arange(H / 2, ztop, H)
    zall = np.unique(np.concatenate([m.vertices[:, 2] for m in meshes]))
    out = []
    for z in zs:
        a, b = [unary_union([g for m in meshes for g in [sec(m, safe_z(zall, z + dz))] if g is not None and not g.is_empty]).buffer(0) for dz in (-0.013, 0.011)]
        out.append(a.intersection(b).buffer(0) if agree else a.union(b).buffer(0))
    return zs, out

def clean(g, a=0.05):
    g = g.buffer(-0.03).buffer(0.03); gs = list(g.geoms) if hasattr(g, 'geoms') else [g]
    return unary_union([x for x in gs if x.area > a])

def overhangs(zs, L):
    return [clean(L[k].difference(L[k - 1].buffer(REACH))) if k else Polygon() for k in range(len(zs))]

def narrow(g):  # widest inscribed width of the widest piece
    w = 0
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        if p.is_empty: continue
        lo, hi = 0, 2
        for _ in range(12):
            mid = (lo + hi) / 2; (lo, hi) = (mid, hi) if not p.buffer(-mid / 2).is_empty else (lo, mid)
        w = max(w, lo)
    return w

def drop(mt):
    oid, tr = mt.group(1), mt.group(2); a = tr.split()
    zmin = min(m.bounds[0][2] for _, _, m in object_parts(oid))
    newz = -zmin
    if abs(newz - float(a[11])) > 1e-5:
        REPORT.setdefault('dropped_to_plate', []).append(f'{NAMES.get(oid)} (object {oid}): z offset {float(a[11]) + zmin:+.4f} mm corrected')
    a[11] = f'{newz:.6f}'
    return mt.group(0).replace(tr, ' '.join(a))
S = re.sub(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"[^>]*/>', drop, S)
items = re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"', S)
cache = {}
PICS = {}
for oid, tr in items:
    tz = float(tr.split()[11])
    parts = object_parts(oid)
    sig = (tuple((fn, cid, tuple(np.round(m.bounds.ravel(), 3))) for fn, cid, m in parts), round(tz, 3))
    if sig in cache:
        res = cache[sig]
    else:
        meshes = []
        for fn, cid, m in parts:
            w = m.copy(); w.apply_translation([0, 0, tz]); meshes.append(w)
        ztop = max(m.bounds[1][2] for m in meshes)
        zs, L = layers_of(meshes, ztop)
        over = overhangs(zs, L)
        tot = sum(u.area for u in over)
        res = dict(before_mm2=round(tot, 2), fill=None)
        if tot > 0.5:
            _, L = layers_of(meshes, ztop, agree=True)
            F = [None] * len(zs); F[-1] = L[-1]
            for k in range(len(zs) - 2, -1, -1): F[k] = L[k].union(F[k + 1].buffer(-REACH)).buffer(0)
            fill = [clean(F[k].difference(L[k]).buffer(0.02).intersection(F[k])) if k else Polygon() for k in range(len(zs))]
            slabs = []
            for k, g in enumerate(fill):
                for p in (g.geoms if hasattr(g, 'geoms') else [g]):
                    if p.is_empty or p.area < 0.05: continue
                    e = trimesh.creation.extrude_polygon(p.simplify(0.01), H + 0.002); e.vertices[:, 2] += zs[k] - H / 2 - 0.001; slabs.append(e)
            if slabs:
                fm = trimesh.boolean.union(slabs, engine='manifold') if len(slabs) > 1 else slabs[0]
                zs2, L2 = layers_of(meshes + [fm], ztop)
                over2 = overhangs(zs2, L2)
                res.update(fill=fm, fill_mm3=round(float(fm.volume), 1), after_mm2=round(sum(u.area for u in over2), 2),
                           widest_left_mm=round(max([narrow(u) for u in over2 if not u.is_empty] or [0]), 2), fill_watertight=bool(fm.is_watertight))
                PICS[sig] = dict(L=L, over=over, fill=fill, meshes=meshes, fm=fm)
        cache[sig] = res
        print(f'object {oid} {NAMES.get(oid)}: overhang {res["before_mm2"]} mm2 -> {res.get("after_mm2", "-")} mm2, fill {res.get("fill_mm3", 0)} mm3', flush=True)
    REPORT['fill'][f'{oid} {NAMES.get(oid)}'] = {k: v for k, v in res.items() if k != 'fill'}
    if res.get('fill') is None: continue
    # add the fill mesh (shared by identical objects) as a part
    if 'mesh_ref' not in res:
        fm = res['fill'].copy(); fm.vertices[:, 2] -= tz
        fn0 = parts[0][0]; res['mesh_ref'] = (fn0, add_mesh(fn0, fm), len(fm.faces))
    fn0, nid, nf = res['mesh_ref']
    ob = re.search(rf'<object id="{oid}"[^>]*>\s*<components>.*?</components>', S, re.S).group(0)
    S = S.replace(ob, ob.replace('</components>', f'  <component p:path="/3D/Objects/{fn0}" objectid="{nid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>'), 1)
    mo = re.search(rf'<object id="{oid}">.*?</object>', MS, re.S).group(0)
    part = (f'    <part id="{nid}" subtype="normal_part" uuid="{uuid.uuid4()}">\n      <metadata key="name" value="Overhang fill"/>\n'
            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n      <metadata key="extruder" value="1"/>\n'
            f'      <mesh_stat face_count="{nf}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n  </object>')
    MS = MS.replace(mo, mo[:mo.rfind('</object>')].rstrip() + '\n' + part, 1)
    vols = [int(x) for x in re.findall(rf'<assemble_item object_id="{oid}" volume_id="(\d+)"', MS)]
    if vols:
        last = re.findall(rf'<assemble_item object_id="{oid}"[^>]*/>', MS)[-1]
        MS = MS.replace(last, last + f'\n   <assemble_item object_id="{oid}" volume_id="{max(vols) + 1}" transform="1 0 0 0 1 0 0 0 1 0 0 0" />', 1)

# ---------------- write back ----------------
for fn, txt in FILES.items(): open(f'{D}/3D/Objects/{fn}', 'w').write(txt)
open(f'{D}/3D/3dmodel.model', 'w').write(S); open(f'{D}/Metadata/model_settings.config', 'w').write(MS)
json.dump(REPORT, open(f'{D}/../fix_report.json', 'w'), indent=1, default=str)
pickle.dump({str(i): v for i, v in enumerate(PICS.values())}, open(f'{D}/../fix_pics.pkl', 'wb'))
print('done; warnings:', REPORT['warnings'])
