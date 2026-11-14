import re, json, os, uuid, subprocess, numpy as np, trimesh, xml.dom.minidom as xm
SP = os.path.dirname(os.path.abspath(__file__)); D = f'{SP}/tree_x2d'
s = open(f'{D}/3D/3dmodel.model').read(); ms = open(f'{D}/Metadata/model_settings.config').read()
p = f'{D}/3D/Objects/object_3048.model'; o = open(p).read()
it = list(map(float, re.search(r'<item objectid="5"[^>]*transform="([^"]*)"', s).group(1).split()))
if 'Recess ironing' not in ms:
    # modifier cylinder: inside the 28 mm recess, around its floor (world z 2.45)
    cyl = trimesh.creation.cylinder(radius=13.6, height=0.9, sections=96)
    cyl.apply_translation([47.0, 48.0, (2.0 + 2.9) / 2 - it[11]])
    nid = str(max(int(x) for x in re.findall(r'<object id="(\d+)"', o)) + 1)
    vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in cyl.vertices)
    tx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in cyl.faces)
    o = o.replace('</resources>', f' <object id="{nid}" p:UUID="{uuid.uuid4()}" type="model">\n  <mesh>\n   <vertices>\n{vx}   </vertices>\n   <triangles>\n{tx}   </triangles>\n  </mesh>\n </object>\n</resources>', 1)
    open(p, 'w').write(o)
    s = s.replace('</components>', f'  <component p:path="/3D/Objects/object_3048.model" objectid="{nid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>', 1)
    open(f'{D}/3D/3dmodel.model', 'w').write(s)
    part = (f'    <part id="5" subtype="modifier_part" uuid="{uuid.uuid4()}">\n      <metadata key="name" value="Recess ironing"/>\n'
            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n      <metadata key="extruder" value="1"/>\n'
            '      <metadata key="ironing_type" value="top"/>\n      <metadata key="ironing_pattern" value="zig-zag"/>\n'
            '      <metadata key="ironing_flow" value="15%"/>\n      <metadata key="ironing_spacing" value="0.1"/>\n'
            '      <metadata key="ironing_speed" value="30"/>\n      <metadata key="ironing_inset" value="0.2"/>\n'
            f'      <mesh_stat face_count="{len(cyl.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n  </object>')
    ms = ms.replace('  </object>', part, 1)
    last = re.findall(r'<assemble_item object_id="5" volume_id="\d+"[^>]*/>', ms)[-1]
    ms = ms.replace(last, last + '\n   <assemble_item object_id="5" volume_id="4" transform="1 0 0 0 1 0 0 0 1 0 0 0" />', 1)
    ms = ms.replace('value="Forest tile X2D test"', 'value="Forest tile X2D test v2"')
    open(f'{D}/Metadata/model_settings.config', 'w').write(ms)
c = json.load(open(f'{D}/Metadata/project_settings.config')); idx = c['filament_self_index']
def ALL(k, v): c[k] = [v] * len(c[k]) if isinstance(c[k], list) else v
c['top_shell_layers'] = '8'
ALL('z_hop', '0.4'); ALL('z_hop_types', 'Spiral Lift'); ALL('retraction_minimum_travel', '0.5'); ALL('wipe', '1'); ALL('wipe_distance', '2')
for k, x in enumerate(idx):
    if x == '1': c['nozzle_temperature'][k] = '205'; c['nozzle_temperature_initial_layer'][k] = '210'
d = c['different_settings_to_system']; d[0] = ';'.join(sorted(set(filter(None, d[0].split(';'))) | {'top_shell_layers', 'z_hop', 'z_hop_types', 'retraction_minimum_travel', 'wipe', 'wipe_distance'}))
json.dump(c, open(f'{D}/Metadata/project_settings.config', 'w'), indent=4)
pr = json.load(open(f'{D}/Metadata/filament_settings_1.config'))
pr['nozzle_temperature'] = ['205'] * len(pr['nozzle_temperature']); pr['nozzle_temperature_initial_layer'] = ['210'] * len(pr['nozzle_temperature_initial_layer'])
pr['nozzle_temperature_range_low'] = ['200'] * len(pr['nozzle_temperature_range_low'])
json.dump(pr, open(f'{D}/Metadata/filament_settings_1.config', 'w'), indent=4)
for f in ['3D/3dmodel.model', 'Metadata/model_settings.config', '3D/Objects/object_3048.model']: xm.parse(f'{D}/{f}')
out = '/home/user/hello-git/catan-forest-tile-x2d-test-v2.3mf'
if os.path.exists(out): os.remove(out)
subprocess.run(f"cd '{D}' && zip -q -X '{out}' '[Content_Types].xml' && zip -q -r -X '{out}' . -x '[Content_Types].xml'", shell=True, check=True)
k = [n for n, x in enumerate(idx) if x == '1'][0]
print('modifier parts:', ms.count('modifier_part'), '| top layers', c['top_shell_layers'], '| z-hop', c['z_hop'][0], c['z_hop_types'][0], '| min travel', c['retraction_minimum_travel'][0], '| temp', c['nozzle_temperature'][k], '/', c['nozzle_temperature_initial_layer'][k], '| infill', c['sparse_infill_pattern'])
