"""Settlements and cities: solid purple base (no grey core), 1 mm taller, fully grey top under the
cobbles, paint removed. Then 0.2 mm nozzle quality settings and a SUNLU grey preset for filament 8."""
import re, json, os, shutil, subprocess, uuid, numpy as np, trimesh, xml.dom.minidom as xm
from shapely.ops import unary_union
SP = os.path.dirname(os.path.abspath(__file__)); D = f'{SP}/pp_out'
shutil.rmtree(D, ignore_errors=True); shutil.copytree(f'{SP}/pp', D)
RAISE, SKIN = 1.0, 0.24          # extra purple height; grey skin under the cobbles (3 layers at 0.08)
PIECES = {'settlement': ('object_3033.model', '7', ['8', '9']), 'city': ('object_2760.model', '1', ['2', '3'])}

def read(o, oid):
    i = o.find(f'<object id="{oid}"'); j = o.find('</object>', i); b = o[i:j]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float)
    t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int)
    return i, j, b, v, t
def write(o, oid, m):
    i, j, b, _, _ = read(o, oid)
    vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in m.vertices)
    tx = ''.join(f'<triangle v1="{a}" v2="{c}" v3="{e}"/>\n' for a, c, e in m.faces)   # no paint_color: paint removed
    b = re.sub(r'<vertices>.*?</vertices>', lambda _: '<vertices>\n' + vx + '</vertices>', b, flags=re.S)
    b = re.sub(r'<triangles>.*?</triangles>', lambda _: '<triangles>\n' + tx + '</triangles>', b, flags=re.S)
    return o[:i] + b + o[j:]

new_part = {}
for name, (fn, main, others) in PIECES.items():
    p = f'{D}/3D/Objects/{fn}'; o = open(p).read()
    _, _, _, v, t = read(o, main)
    m = trimesh.Trimesh(v, t); m.merge_vertices(); trimesh.repair.fill_holes(m); trimesh.repair.fix_normals(m)
    z0 = m.bounds[0][2]
    # top of the full base disc: last height where the cross-section is still the full circle
    full = None
    for dz in np.arange(0.5, 4.0, 0.02):
        a = unary_union(m.section([0, 0, 1], [0, 0, z0 + dz]).to_2D()[0].polygons_full).area
        if full is None: full = a
        if a < full * 0.99: disc_top = dz - 0.02; break
    cut = z0 + disc_top - SKIN
    sec, T = m.section([0, 0, 1], [0, 0, z0 + 1.0]).to_2D()
    disc = unary_union(sec.polygons_full)
    base = trimesh.creation.extrude_polygon(disc, (cut - z0) + RAISE)
    base.apply_transform(T); base.apply_translation([0, 0, z0 - base.bounds[0][2]])
    if base.volume < 0: base.invert()
    upper = trimesh.intersections.slice_mesh_plane(m, [0, 0, 1], [0, 0, cut], cap=True)
    upper.apply_translation([0, 0, RAISE])
    print(f'{name}: disc top {disc_top:.2f} mm, cut at {cut - z0:.2f} mm, purple base {base.bounds[1][2]-base.bounds[0][2]:.2f} mm tall (watertight {base.is_watertight}), grey body watertight {upper.is_watertight}')
    o = write(o, main, upper)
    for oid in others:
        _, _, _, v2, t2 = read(o, oid); mm = trimesh.Trimesh(v2, t2, process=False); mm.apply_translation([0, 0, RAISE]); o = write(o, oid, mm)
    nid = str(max(int(x) for x in re.findall(r'<object id="(\d+)"', o)) + 1)
    hdr = re.match(r'<object id="\d+"([^>]*)>', read(o, main)[2]).group(1)
    hdr = re.sub(r'p:UUID="[^"]*"', f'p:UUID="{uuid.uuid4()}"', hdr)
    o = o.replace('</resources>', f' <object id="{nid}"{hdr}>\n  <mesh>\n   <vertices>\n   </vertices>\n   <triangles>\n   </triangles>\n  </mesh>\n </object>\n</resources>', 1)
    o = write(o, nid, base)
    open(p, 'w').write(o); new_part[name] = (fn, main, nid, len(base.faces))

# add the purple base as a new part to every settlement / city object
s = open(f'{D}/3D/3dmodel.model').read(); ms = open(f'{D}/Metadata/model_settings.config').read()
for name, (fn, main, nid, nf) in new_part.items():
    path = f'/3D/Objects/{fn}'
    for ob in re.findall(r'<object id="\d+"[^>]*>\s*<components>.*?</components>', s, re.S):
        comp = re.search(rf'<component p:path="{re.escape(path)}" objectid="{main}"[^>]*transform="([^"]*)"/>', ob)
        if not comp: continue
        oid = re.match(r'<object id="(\d+)"', ob).group(1)
        add = f'\n    <component p:path="{path}" objectid="{nid}" p:UUID="{uuid.uuid4()}" transform="{comp.group(1)}"/>'
        s = s.replace(ob, ob.replace('</components>', add + '\n   </components>'), 1)
        mo = re.search(rf'<object id="{oid}">.*?</object>', ms, re.S).group(0)
        mat = re.findall(r'<metadata key="matrix" value="([^"]+)"/>', mo)[0]
        part = (f'\n    <part id="{9000 + int(nid)}" subtype="normal_part" uuid="{uuid.uuid4()}">\n      <metadata key="name" value="Purple base"/>'
                f'\n      <metadata key="matrix" value="{mat}"/>\n      <metadata key="extruder" value="1"/>'
                f'\n      <mesh_stat face_count="{nf}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>')
        mo2 = mo.replace('</object>', part + '\n  </object>')
        mo2 = re.sub(r'<metadata face_count="\d+"/>', '', mo2)
        ms = ms.replace(mo, mo2, 1)
        asm = re.findall(rf'<assemble_item object_id="{oid}" volume_id="(\d+)"[^>]*/>', ms)
        if asm:
            last = re.findall(rf'<assemble_item object_id="{oid}"[^>]*/>', ms)[-1]
            ms = ms.replace(last, last + f'\n   <assemble_item object_id="{oid}" volume_id="{max(map(int, asm)) + 1}" transform="{" ".join(comp.group(1).split())}" />', 1)
open(f'{D}/3D/3dmodel.model', 'w').write(s); open(f'{D}/Metadata/model_settings.config', 'w').write(ms)

# --- 0.2 mm nozzle quality settings
c = json.load(open(f'{D}/Metadata/project_settings.config')); idx = c['filament_self_index']
def F(slot, key, val):
    L = c[key]
    if len(L) == len(idx):
        for k, x in enumerate(idx):
            if x == str(slot): L[k] = val
    else: L[slot - 1] = val
def ALL(k, v): c[k] = [v] * len(c[k]) if isinstance(c[k], list) else v
setv = {'printer_settings_id': 'Bambu Lab X2D 0.2 nozzle', 'printer_variant': '0.2', 'layer_height': '0.08', 'initial_layer_print_height': '0.1',
        'line_width': '0.22', 'outer_wall_line_width': '0.22', 'inner_wall_line_width': '0.22', 'top_surface_line_width': '0.22',
        'internal_solid_infill_line_width': '0.22', 'sparse_infill_line_width': '0.22', 'initial_layer_line_width': '0.25', 'initial_layer_infill_line_width': '0.25',
        'skeleton_infill_line_width': '0.22', 'skin_infill_line_width': '0.22', 'support_line_width': '0.22',
        'wall_generator': 'arachne', 'wall_loops': '3', 'seam_position': 'aligned', 'reduce_crossing_wall': '1', 'filament_map_mode': 'Manual'}
for k, v in setv.items():
    if k in c: c[k] = v
c['nozzle_diameter'] = ['0.2'] * len(c['nozzle_diameter']); c['print_compatible_printers'] = ['Bambu Lab X2D 0.2 nozzle']
c['filament_map'] = ['1'] * len(c['filament_map'])
for k, v in [('outer_wall_speed', '40'), ('inner_wall_speed', '60'), ('small_perimeter_speed', '50%'), ('top_surface_speed', '60'),
             ('internal_solid_infill_speed', '80'), ('sparse_infill_speed', '80'), ('gap_infill_speed', '40'), ('initial_layer_speed', '30'), ('initial_layer_infill_speed', '30')]:
    if k in c: ALL(k, v)
for k in ['fan_min_speed', 'fan_max_speed']: ALL(k, '100')
ALL('slow_down_layer_time', '12')
c['filament_max_volumetric_speed'] = ['3'] * len(c['filament_max_volumetric_speed'])
NAME = 'SUNLU PLA+ 2.0 Grey (0.2 nozzle)'
F(8, 'filament_settings_id', NAME); F(8, 'filament_vendor', 'SUNLU'); F(8, 'filament_colour', '#8E9089')
F(8, 'nozzle_temperature', '210'); F(8, 'nozzle_temperature_initial_layer', '215'); F(8, 'filament_flow_ratio', '0.98')
for i, x in enumerate(c['filament_settings_id']):
    if i != 7 and 'X2D 0.4 nozzle' in x: c['filament_settings_id'][i] = x.replace('0.4 nozzle', '0.2 nozzle')
d = c['different_settings_to_system']; d[0] = ';'.join(sorted(set(filter(None, d[0].split(';'))) | {k for k in setv if k in c} | {'outer_wall_speed', 'inner_wall_speed', 'small_perimeter_speed', 'top_surface_speed', 'internal_solid_infill_speed', 'sparse_infill_speed', 'gap_infill_speed', 'initial_layer_speed', 'initial_layer_infill_speed'}))
json.dump(c, open(f'{D}/Metadata/project_settings.config', 'w'), indent=4)
ks = [k for k, x in enumerate(idx) if x == '8']
preset = {'filament_extruder_variant': [c['filament_extruder_variant'][k] for k in ks], 'from': 'project', 'inherits': 'Generic PLA @BBL X2D 0.2 nozzle', 'name': NAME, 'version': '2.0.0.0',
          'filament_settings_id': [NAME], 'filament_vendor': ['SUNLU'], 'filament_type': ['PLA'], 'filament_colour': ['#8E9089'],
          'nozzle_temperature': ['210'] * len(ks), 'nozzle_temperature_initial_layer': ['215'] * len(ks), 'filament_flow_ratio': ['0.98'] * len(ks),
          'filament_max_volumetric_speed': ['3'] * len(ks), 'nozzle_temperature_range_low': ['205'] * len(ks), 'nozzle_temperature_range_high': ['215'] * len(ks),
          'fan_min_speed': ['100'], 'fan_max_speed': ['100'], 'slow_down_layer_time': ['12'], 'textured_plate_temp': ['55'], 'textured_plate_temp_initial_layer': ['55']}
os.remove(f'{D}/Metadata/filament_settings_1.config')
json.dump(preset, open(f'{D}/Metadata/filament_settings_8.config', 'w'), indent=4)
for f in ['3D/3dmodel.model', 'Metadata/model_settings.config'] + [f'3D/Objects/{v[0]}' for v in new_part.values()]: xm.parse(f'{D}/{f}')
out = '/home/user/hello-git/catan-player-pieces-0.2nozzle.3mf'
if os.path.exists(out): os.remove(out)
subprocess.run(f"cd '{D}' && zip -q -X '{out}' '[Content_Types].xml' && zip -q -r -X '{out}' . -x '[Content_Types].xml'", shell=True, check=True)
print('purple base parts added:', ms.count('value="Purple base"'), '| printer', c['printer_settings_id'], '| filament 8', c['filament_settings_id'][7])
