import re, json, shutil, os, subprocess, pickle, uuid, numpy as np, trimesh, xml.dom.minidom as xm
from shapely import affinity
SP = os.path.dirname(os.path.abspath(__file__))
F = pickle.load(open(f'{SP}/dev_final.pkl', 'rb')); SH = pickle.load(open(f'{SP}/dev_shapes.pkl', 'rb'))
SLOT = {'knight': 8, 'vp': 9, 'rb': 7, 'yop': 7, 'mono': 7}
COUNT = {'knight': 14, 'vp': 5, 'rb': 2, 'yop': 2, 'mono': 2}
TITLE = {'knight': 'knight', 'vp': 'victory-point', 'rb': 'road-building', 'yop': 'year-of-plenty', 'mono': 'monopoly'}
COL = {7: '#008000', 8: '#8080FF', 9: '#FF8000'}
OFF = 0.24142456
slots = [(46.5,131.5),(101.5,131.5),(156.5,131.5),(211.5,131.5),(101.5,212.5),(156.5,212.5),(211.5,212.5),(101.5,50.5),(156.5,50.5),(211.5,50.5)]

def mesh_xml(poly, z0, z1):
    ms = []
    poly = poly.simplify(0.01).buffer(0)          # drop near-duplicate points that break the mesh
    for g in (poly.geoms if hasattr(poly, 'geoms') else [poly]):
        if g.area < 0.05: continue
        e = trimesh.creation.extrude_polygon(g, z1 - z0); e.vertices[:, 2] += z0; ms.append(e)
    m = trimesh.util.concatenate(ms)
    if m.volume < 0: m.invert()
    assert m.is_watertight
    vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in m.vertices)
    tx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in m.faces)
    return vx, tx, len(m.faces)

def put(o, oid, poly, z0, z1):
    i = o.find(f'<object id="{oid}"'); j = o.find('</object>', i); b = o[i:j]
    vx, tx, n = mesh_xml(poly, z0, z1)
    b = re.sub(r'<vertices>.*?</vertices>', lambda _: '<vertices>\n' + vx + '</vertices>', b, flags=re.S)
    b = re.sub(r'<triangles>.*?</triangles>', lambda _: '<triangles>\n' + tx + '</triangles>', b, flags=re.S)
    return o[:i] + b + o[j:], n

for name in SLOT:
    d = f'{SP}/dev_{name}'; shutil.rmtree(d, ignore_errors=True); shutil.copytree(f'{SP}/set_wheat', d)
    o = open(f'{d}/3D/Objects/object_205.model').read()
    icon = affinity.translate(F[name], 0, -OFF)                 # icon part sits 0.24 mm up in the card
    o, nf = put(o, 17, icon, -0.1, 0.1)                         # face layer
    o, _ = put(o, 22, icon, 0.1, 0.2)                           # same-colour backing layer
    o, nl = put(o, 16, SH[name]['logo'], -0.1, 0.1)             # this card's own back: three nested hexagons
    open(f'{d}/3D/Objects/object_205.model', 'w').write(o)
    m = open(f'{d}/Metadata/model_settings.config').read()
    m = re.sub(r'(<object id="168">\s*<metadata key="name" value=")[^"]*("/>\s*<metadata key="extruder" value=")\d', rf'\g<1>{TITLE[name]}\g<2>{SLOT[name]}', m)
    m = m.replace('value="Wheat icon"', f'value="{TITLE[name]} icon"').replace('value="Rear Logo (2)"', 'value="Rear Logo (dev)"')
    m = re.sub(r'(<metadata key="name" value="[^"]+ icon"/>.*?<mesh_stat face_count=")\d+', lambda x: x.group(1) + str(nf), m, count=1, flags=re.S)
    m = re.sub(r'(<metadata key="name" value="Rear Logo \(dev\)"/>.*?<mesh_stat face_count=")\d+', lambda x: x.group(1) + str(nl), m, count=1, flags=re.S)
    m = re.sub(r'(<metadata key="top_surface_pattern" value=")[^"]*', r'\1monotonicline', m)   # rings: plain lines like the rest of the back
    # lay out COUNT cards, 10 per plate
    s = open(f'{d}/3D/3dmodel.model').read()
    base = re.search(r'\s*<object id="168".*?</object>', s, re.S).group(0); item = re.search(r'<item objectid="168"[^>]*/>', s).group(0)
    s = s.replace(base, '', 1).replace(item, '', 1)
    ob = re.search(r'<object id="168">.*?</object>', m, re.S).group(0); asm = re.findall(r'<assemble_item object_id="168"[^>]*/>', m)
    m = m.replace(ob, '', 1); m = re.sub(r'\s*<assemble_item object_id="168"[^>]*/>', '', m)
    pos = [(k // 10 + 1, slots[k % 10][0] + 307.2 * (k // 10), slots[k % 10][1]) for k in range(COUNT[name])]
    ids = [str(601 + k) for k in range(COUNT[name])]
    objs = ''; items = ''; mobjs = ''; asms = []
    for n, (oid, (pl, x, y)) in enumerate(zip(ids, pos), 1):
        objs += re.sub(r'p:UUID="[^"]*"', lambda _: f'p:UUID="{uuid.uuid4()}"', base.replace('<object id="168"', f'<object id="{oid}"'))
        it = re.sub(r'transform="[^"]*"', f'transform="1 0 0 0 1 0 0 0 1 {x} {y} 0.25"', item.replace('objectid="168"', f'objectid="{oid}"'))
        items += '\n  ' + re.sub(r'p:UUID="[^"]*"', f'p:UUID="{uuid.uuid4()}"', it)
        b = re.sub(r'(<object id="\d+">\s*<metadata key="name" value=")[^"]*', rf'\g<1>{TITLE[name]} {n:02d}', ob.replace('<object id="168">', f'<object id="{oid}">'))
        mobjs += '\n  ' + re.sub(r'uuid="[^"]*"', lambda _: f'uuid="{uuid.uuid4()}"', b)
        for a in asm:
            a2 = a.replace('object_id="168"', f'object_id="{oid}"')
            if 'volume_id' not in a2: a2 = re.sub(r'transform="[^"]*"', f'transform="1 0 0 0 1 0 0 0 1 {x} {y} 0.25"', a2)
            asms.append(a2)
    s = s.replace('</resources>', objs + '\n </resources>', 1); s = re.sub(r'(<build[^>]*>)', lambda q: q.group(1) + items, s, count=1)
    open(f'{d}/3D/3dmodel.model', 'w').write(s)
    m = re.sub(r'(<config>)', lambda q: q.group(1) + mobjs, m, count=1)
    m = m.replace('<assemble>', '<assemble>\n   ' + '\n   '.join(asms), 1)
    plate = re.search(r'\s*<plate>.*?</plate>', m, re.S).group(0)
    nplates = max(p for p, _, _ in pos); newp = ''
    for pl in range(1, nplates + 1):
        cnt = sum(1 for p, _, _ in pos if p == pl)
        p = re.sub(r'\s*<model_instance>.*?</model_instance>', '', plate, flags=re.S)
        p = re.sub(r'(plater_id" value=")\d+', rf'\g<1>{pl}', p)
        p = re.sub(r'(plater_name" value=")[^"]*', rf'\g<1>{TITLE[name].replace("-", " ").title()} {pl} of {nplates} ({cnt} cards)', p)
        if pl > 1: p = re.sub(r'\s*<metadata key="(thumbnail_file|thumbnail_no_light_file|top_file|pick_file)"[^>]*/>', '', p)
        p = p.replace('</plate>', ''.join(f'\n    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{840000 + k}"/>\n    </model_instance>' for k, (oid, (pp, _, _)) in enumerate(zip(ids, pos)) if pp == pl) + '\n  </plate>')
        newp += p
    m = m.replace(plate, newp)
    open(f'{d}/Metadata/model_settings.config', 'w').write(m)
    json.dump({f'plate_{i}': {"nozzle_sequence": [], "optimal_assignment": [], "sequence": []} for i in range(1, nplates + 1)}, open(f'{d}/Metadata/filament_sequence.json', 'w'))
    c = json.load(open(f'{d}/Metadata/project_settings.config')); idx = c['filament_self_index']
    for sl, col in COL.items():
        c['filament_colour'][sl - 1] = col
        for i, x in enumerate(idx):
            if x == str(sl): c['filament_flow_ratio'][i] = '1.01'
    for k in range(min(nplates, len(c['wipe_tower_x']))): c['wipe_tower_x'][k] = '35.5'; c['wipe_tower_y'][k] = '195.556'
    json.dump(c, open(f'{d}/Metadata/project_settings.config', 'w'), indent=4)
    for f in ['3D/3dmodel.model', 'Metadata/model_settings.config', '3D/Objects/object_205.model']: xm.parse(f'{d}/{f}')
    out = f'/home/user/hello-git/catan-{TITLE[name]}-{COUNT[name]}-cards.3mf'
    if os.path.exists(out): os.remove(out)
    subprocess.run(f"cd {d} && zip -q -X {out} '[Content_Types].xml' && zip -q -r -X {out} . -x '[Content_Types].xml'", shell=True, check=True)
    ex = set(re.findall(r'<object id="\d+">\s*<metadata key="name" value="[^"]+"/>\s*<metadata key="extruder" value="(\d)"', m))
    print(f'{os.path.basename(out)}: {len(ids)} cards on {nplates} plate(s), icon filament {ex}, plates: {re.findall(r"plater_name\" value=\"([^\"]+)", m)}')
