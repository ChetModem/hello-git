"""Build the special cards file and the legend + stand file from design.py, on the card template
(face down on the smooth plate, 0.2 first layer then 0.1 layers - same settings as the other cards)."""
import os, re, sys, json, uuid, shutil, subprocess, numpy as np, trimesh, xml.dom.minidom as xm
from shapely import affinity
from shapely.geometry import Polygon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D

SP = D.SP
TEMPLATE = f'{SP}/set_wheat'
COLOURS = {7: '#008000', 8: '#8080FF', 9: '#FF8000'}      # same overrides as the development cards
STRIDE = 307.2                                            # Bambu plate spacing for a 256 mm bed

def mirror(g):                    # face view -> as printed (face down)
    return affinity.scale(g, -1, 1, origin=(0, 0))

def extrude(poly, z0, z1):
    poly = poly.simplify(0.01).buffer(0)
    ms = []
    for g in (poly.geoms if hasattr(poly, 'geoms') else [poly]):
        if g.area < 0.05: continue
        e = trimesh.creation.extrude_polygon(g, z1 - z0); e.vertices[:, 2] += z0; ms.append(e)
    m = trimesh.util.concatenate(ms)
    if m.volume < 0: m.invert()
    assert m.is_watertight and m.is_winding_consistent, 'mesh not closed'
    return m

def template_mesh(cid, dz=0.25):
    o = open(f'{TEMPLATE}/3D/Objects/object_205.model').read(); s = open(f'{TEMPLATE}/3D/3dmodel.model').read()
    i = o.find(f'<object id="{cid}"'); b = o[i:o.find('</object>', i)]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float)
    t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int)
    tr = re.search(rf'objectid="{cid}"[^>]*transform="([^"]*)"', s).group(1).split()
    v = v + [float(tr[9]), float(tr[10]), float(tr[11]) + dz]
    return trimesh.Trimesh(v, t, process=False)

FACE, BACKING = (0.0, 0.2), (0.2, 0.3)   # face colour = first (0.2 mm) layer, then one same-colour 0.1 mm layer

def card_parts(shapes, corner_slot):
    """shapes: {slot: polygon in face view}. Returns list of (name, extruder, mesh, extra metadata)."""
    parts = [('Card', 1, template_mesh(11), {})]
    for k, cid in enumerate((12, 13, 14, 15)):                                 # corner hexes, face + backing
        parts.append((f'Corner hex {k + 1}', corner_slot, template_mesh(cid), {}))
    for k, cid in enumerate((18, 19, 20, 21)):
        parts.append((f'Corner hex backing {k + 1}', corner_slot, template_mesh(cid), {}))
    for slot, g in sorted(shapes.items()):
        g = mirror(g)
        parts.append((f'Icon colour {slot}', slot, extrude(g, *FACE), {}))
        parts.append((f'Icon backing colour {slot}', slot, extrude(g, *BACKING), {}))
    parts.append(('Rear logo (special)', 2, extrude(mirror(D.special_back()), 0.3, 0.5), {'top_surface_pattern': 'monotonicline'}))
    return parts

def write_project(out, objects, plate_names):
    """objects: list of dict(name, plate, x, y, parts)."""
    d = out + '.dir'; shutil.rmtree(d, ignore_errors=True); shutil.copytree(TEMPLATE, d)
    # --- meshes
    o = open(f'{d}/3D/Objects/object_205.model').read()
    head = o[:o.find('<resources>') + len('<resources>')]; tail = '\n </resources>\n</model>\n'
    s = open(f'{d}/3D/3dmodel.model').read()
    s = re.sub(r'\s*<object id="168".*?</object>', '', s, flags=re.S); s = re.sub(r'\s*<item objectid="168"[^>]*/>', '', s)
    m = open(f'{d}/Metadata/model_settings.config').read()
    m = re.sub(r'\s*<object id="168">.*?</object>', '', m, flags=re.S)
    m = re.sub(r'\s*<assemble_item object_id="168"[^>]*/>', '', m)
    plate_tpl = re.search(r'\s*<plate>.*?</plate>', m, re.S).group(0); m = m.replace(plate_tpl, '')
    meshxml = []; objxml = ''; items = ''; mobj = ''; asm = []; nid = 1000; oid = 2000
    for ob in objects:
        oid += 1; ob['oid'] = oid; comps = ''; parts = ''
        for k, (pname, ext, mesh, extra) in enumerate(ob['parts']):
            nid += 1
            vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in mesh.vertices)
            tx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in mesh.faces)
            meshxml.append(f'\n  <object id="{nid}" p:UUID="{uuid.uuid4()}" type="model">\n   <mesh>\n    <vertices>\n{vx}    </vertices>\n    <triangles>\n{tx}    </triangles>\n   </mesh>\n  </object>')
            comps += f'\n    <component p:path="/3D/Objects/object_205.model" objectid="{nid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
            ex = ''.join(f'\n      <metadata key="{a}" value="{b}"/>' for a, b in extra.items())
            parts += (f'\n    <part id="{nid}" subtype="normal_part" uuid="{uuid.uuid4()}">\n      <metadata key="name" value="{pname}"/>\n'
                      f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n      <metadata key="extruder" value="{ext}"/>{ex}\n'
                      f'      <mesh_stat face_count="{len(mesh.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>')
            asm.append(f'<assemble_item object_id="{oid}" volume_id="{k}" transform="1 0 0 0 1 0 0 0 1 0 0 0" />')
        X = ob['x'] + STRIDE * (ob['plate'] - 1); Y = ob['y']
        objxml += f'\n  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>{comps}\n   </components>\n  </object>'
        items += f'\n  <item objectid="{oid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {X} {Y} 0" printable="1"/>'
        mobj += f'\n  <object id="{oid}">\n    <metadata key="name" value="{ob["name"]}"/>\n    <metadata key="extruder" value="1"/>{parts}\n  </object>'
        asm.insert(len(asm) - len(ob['parts']), f'<assemble_item object_id="{oid}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 {X} {Y} 0" offset="0 0 0" />')
    open(f'{d}/3D/Objects/object_205.model', 'w').write(head + ''.join(meshxml) + tail)
    s = s.replace('<resources>', '<resources>' + objxml, 1); s = re.sub(r'(<build[^>]*>)', lambda q: q.group(1) + items, s, count=1)
    open(f'{d}/3D/3dmodel.model', 'w').write(s)
    plates = ''
    for pl, pname in enumerate(plate_names, 1):
        p = re.sub(r'\s*<model_instance>.*?</model_instance>', '', plate_tpl, flags=re.S)
        p = re.sub(r'(plater_id" value=")\d+', rf'\g<1>{pl}', p); p = re.sub(r'(plater_name" value=")[^"]*', rf'\g<1>{pname}', p)
        p = re.sub(r'\s*<metadata key="(thumbnail_file|thumbnail_no_light_file|top_file|pick_file)"[^>]*/>', '', p)   # stale pictures; Studio redraws them
        p = p.replace('</plate>', ''.join(f'\n    <model_instance>\n      <metadata key="object_id" value="{ob["oid"]}"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{900000 + ob["oid"]}"/>\n    </model_instance>' for ob in objects if ob['plate'] == pl) + '\n  </plate>')
        plates += p
    m = re.sub(r'(<config>)', lambda q: q.group(1) + mobj + plates, m, count=1)
    m = re.sub(r'<assemble>.*?</assemble>', lambda _: '<assemble>\n   ' + '\n   '.join(asm) + '\n  </assemble>', m, flags=re.S)
    open(f'{d}/Metadata/model_settings.config', 'w').write(m)
    for f in ['Metadata/plate_1.png', 'Metadata/plate_1_small.png', 'Metadata/plate_no_light_1.png', 'Metadata/top_1.png', 'Metadata/pick_1.png']:
        if os.path.exists(f'{d}/{f}'): os.remove(f'{d}/{f}')
    s2 = open(f'{d}/3D/3dmodel.model').read()
    s2 = re.sub(r'\s*<metadata name="Thumbnail_(Middle|Small)">[^<]*</metadata>', '', s2); open(f'{d}/3D/3dmodel.model', 'w').write(s2)
    json.dump({f'plate_{i}': {"nozzle_sequence": [], "optimal_assignment": [], "sequence": []} for i in range(1, len(plate_names) + 1)}, open(f'{d}/Metadata/filament_sequence.json', 'w'))
    c = json.load(open(f'{d}/Metadata/project_settings.config')); idx = c['filament_self_index']
    for sl, col in COLOURS.items():
        c['filament_colour'][sl - 1] = col
        for i, x in enumerate(idx):
            if x == str(sl): c['filament_flow_ratio'][i] = '1.01'
    json.dump(c, open(f'{d}/Metadata/project_settings.config', 'w'), indent=4)
    for f in ['3D/3dmodel.model', 'Metadata/model_settings.config', '3D/Objects/object_205.model']: xm.parse(f'{d}/{f}')
    if os.path.exists(out): os.remove(out)
    # drop thumbnail references in rels/content types if they point at removed files
    rels = f'{d}/_rels/.rels'
    if os.path.exists(rels):
        r = open(rels).read(); r = re.sub(r'\s*<Relationship [^>]*Target="/Metadata/plate_1[^"]*"[^>]*/>', '', r); open(rels, 'w').write(r)
    subprocess.run(f"cd '{d}' && zip -q -X '{out}' '[Content_Types].xml' && zip -q -r -X '{out}' . -x '[Content_Types].xml'", shell=True, check=True)
    return d

if __name__ == '__main__':
    REPO = '/home/user/hello-git'
    # ---------------- cards: 4 building costs + longest road + largest army on one plate
    slots = [(1, 46.5, 131.5), (1, 101.5, 131.5), (1, 156.5, 131.5), (1, 211.5, 131.5), (2, 101.5, 131.5), (2, 156.5, 131.5)]
    cards = []
    defs = [('Building Costs 1', D.building_costs, 2), ('Building Costs 2', D.building_costs, 2), ('Building Costs 3', D.building_costs, 2),
            ('Building Costs 4', D.building_costs, 2), ('Longest Road', D.longest_road, 9), ('Largest Army', D.largest_army, 9)]
    for (name, f, corner), (pl, x, y) in zip(defs, slots):
        sh = f()
        # corner hexes come from the template parts; take them out of the design shapes
        hexes = D.unary_union([D.hexagon(*c) for c in D.CORNERS]).buffer(0.05)
        sh = {k: v.difference(hexes).buffer(0) for k, v in sh.items()}
        sh = {k: v for k, v in sh.items() if v.area > 0.05}
        cards.append(dict(name=name, plate=pl, x=x, y=y, parts=card_parts(sh, corner)))
    write_project(f'{REPO}/catan-special-cards-6.3mf', cards, ['Building Costs x4 (6 colours)', 'Longest Road + Largest Army (5 colours)'])
    print('cards written')
    # ---------------- legend board (plate 1) + two stand feet (plate 2)
    L = D.legend(); W, H = D.BOARD_W, D.BOARD_H
    parts = [('Board', 1, extrude(D.board_outline(), 0.0, D.BOARD_T), {})]
    for slot, g in sorted(L.items()):
        g = mirror(g)
        parts.append((f'Legend colour {slot}', slot, extrude(g, *FACE), {}))
        parts.append((f'Legend backing colour {slot}', slot, extrude(g, *BACKING), {}))
    prof = D.stand_profile()
    foot = trimesh.creation.extrude_polygon(prof, D.FOOT_W)            # profile in (y, z) extruded along x
    foot.apply_transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))   # (u,v,w) -> x=w, y=u, z=v
    foot.apply_translation([-D.FOOT_W / 2, -27.0, 0])
    if foot.volume < 0: foot.invert()
    assert foot.is_watertight
    objs = [dict(name='Rules legend', plate=1, x=128.0, y=72.0, parts=parts),
            dict(name='Legend stand left', plate=2, x=98.0, y=128.0, parts=[('Stand foot', 1, foot, {})]),
            dict(name='Legend stand right', plate=2, x=158.0, y=128.0, parts=[('Stand foot', 1, foot.copy(), {})])]
    write_project(f'{REPO}/catan-rules-legend-with-stand.3mf', objs, ['Rules legend', 'Legend stand (2 feet)'])
    print('legend written', W, H)
