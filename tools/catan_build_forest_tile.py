import json, re, os, shutil, subprocess, numpy as np, trimesh, xml.dom.minidom as xm
SP = os.path.dirname(os.path.abspath(__file__)); D = f'{SP}/tree_x2d'
shutil.rmtree(D, ignore_errors=True); shutil.copytree(f'{SP}/tree', D)
os.remove(f'{D}/Metadata/filament_settings_1.config')
# --- repair the small mesh holes in the tree and detail parts
p = f'{D}/3D/Objects/object_3048.model'; o = open(p).read()
for oid in ('2', '4'):
    i = o.find(f'<object id="{oid}"'); j = o.find('</object>', i); b = o[i:j]
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', b), float); t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', b), int)
    m = trimesh.Trimesh(v, t); m.merge_vertices(); trimesh.repair.fill_holes(m); trimesh.repair.fix_normals(m)
    vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in m.vertices)
    tx = ''.join(f'<triangle v1="{a}" v2="{c}" v3="{e}"/>\n' for a, c, e in m.faces)
    b = re.sub(r'<vertices>.*?</vertices>', lambda _: '<vertices>\n' + vx + '</vertices>', b, flags=re.S)
    b = re.sub(r'<triangles>.*?</triangles>', lambda _: '<triangles>\n' + tx + '</triangles>', b, flags=re.S)
    o = o[:i] + b + o[j:]
    print(f'part {oid}: broken faces after repair {len(trimesh.repair.broken_faces(m))}, faces {len(m.faces)}')
open(p, 'w').write(o)
# --- one colour: every part on filament 1
ms = open(f'{D}/Metadata/model_settings.config').read()
ms = re.sub(r'(<metadata key="extruder" value=")\d', r'\g<1>1', ms)
ms = ms.replace('Auto For Flush', 'Manual').replace('value="Wood"', 'value="Forest tile X2D test"')
open(f'{D}/Metadata/model_settings.config', 'w').write(ms)
# --- variable layer height: 0.2 mm for the flat base, 0.08 mm from where the terrain and trees start (z 3.0) to the top
prof = '0;0.2;2.8;0.2;3.0;0.08;15.2;0.08'
open(f'{D}/Metadata/layer_heights_profile.txt', 'w').write(f'object_id=1|{prof}\nobject_id=5|{prof}\n')
# --- X2D project settings, starting from the near-stock X2D profile in the original card project
c = json.load(open(f'{SP}/3mf/Metadata/project_settings.config'))
idx = c['filament_self_index']
def F(slot, key, val):
    L = c[key]
    if len(L) == len(idx):
        for k, x in enumerate(idx):
            if x == str(slot): L[k] = val
    else: L[slot - 1] = val
def ALL(key, val): c[key] = [val] * len(c[key]) if isinstance(c[key], list) else val
set_ = {
 'layer_height': '0.12', 'initial_layer_print_height': '0.2', 'curr_bed_type': 'Textured PEI Plate',
 'wall_generator': 'arachne', 'wall_loops': '3', 'top_shell_layers': '6', 'top_shell_thickness': '0.6', 'bottom_shell_layers': '4',
 'seam_position': 'aligned', 'reduce_crossing_wall': '1', 'ironing_type': 'no ironing', 'enable_prime_tower': '0',
 'enable_support': '1', 'support_type': 'tree(auto)', 'support_on_build_plate_only': '1', 'support_threshold_angle': '20',
 'sparse_infill_density': '15%', 'top_surface_pattern': 'monotonicline', 'filament_map_mode': 'Manual', 'brim_type': 'no_brim',
}
for k, v in set_.items(): c[k] = v
for k, v in [('outer_wall_speed', '60'), ('inner_wall_speed', '120'), ('small_perimeter_speed', '50%'), ('top_surface_speed', '100'),
             ('internal_solid_infill_speed', '200'), ('sparse_infill_speed', '250'), ('gap_infill_speed', '60'), ('initial_layer_speed', '40')]:
    ALL(k, v)
c['filament_map'] = ['1'] * len(c['filament_map'])
# filament 1 = SUNLU PLA+ 2.0 grey (maker: 205-215 C at 50-100 mm/s, bed 50-60 C)
F(1, 'filament_settings_id', 'Generic PLA @BBL X2D 0.4 nozzle'); F(1, 'filament_vendor', 'SUNLU'); F(1, 'filament_type', 'PLA')
F(1, 'filament_colour', '#808080'); F(1, 'filament_ids', 'GFL99')
F(1, 'nozzle_temperature', '210'); F(1, 'nozzle_temperature_initial_layer', '215'); F(1, 'filament_flow_ratio', '0.98')
F(1, 'filament_max_volumetric_speed', '15'); F(1, 'textured_plate_temp', '55'); F(1, 'textured_plate_temp_initial_layer', '55')
F(1, 'fan_min_speed', '100'); F(1, 'fan_max_speed', '100'); F(1, 'slow_down_layer_time', '10'); F(1, 'slow_down_min_speed', '15')
d = c['different_settings_to_system']; d[0] = ';'.join(sorted(set(filter(None, d[0].split(';'))) | set(set_) | {'outer_wall_speed', 'inner_wall_speed', 'small_perimeter_speed', 'top_surface_speed', 'internal_solid_infill_speed', 'sparse_infill_speed', 'gap_infill_speed', 'initial_layer_speed'}))
json.dump(c, open(f'{D}/Metadata/project_settings.config', 'w'), indent=4)
for f in ['3D/3dmodel.model', 'Metadata/model_settings.config', '3D/Objects/object_3048.model']: xm.parse(f'{D}/{f}')
out = '/home/user/hello-git/catan-forest-tile-x2d-test.3mf'
if os.path.exists(out): os.remove(out)
subprocess.run(f"cd '{D}' && zip -q -X '{out}' '[Content_Types].xml' && zip -q -r -X '{out}' . -x '[Content_Types].xml'", shell=True, check=True)
k = [n for n, x in enumerate(idx) if x == '1'][0]
print('printer', c['printer_settings_id'], '| layer', c['layer_height'], '| walls', c['wall_loops'], c['wall_generator'], '| seam', c['seam_position'],
      '| outer wall', c['outer_wall_speed'][0], '| temp', c['nozzle_temperature'][k], '| fan', c['fan_min_speed'][0], c['fan_max_speed'][0], '| min layer time', c['slow_down_layer_time'][0], '| parts on filament', set(re.findall(r'key="extruder" value="(\d)"', ms)))
