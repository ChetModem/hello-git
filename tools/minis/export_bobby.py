"""Mesh the Bobby Panda fields and write the single-colour print project + STL (and, with --multi, the multi-colour project).

    python3 export_bobby.py bobby_fields_0.1.npz <template.3mf> <out_dir> [--multi]

The template 3MF only donates its printer/filament settings (Metadata/project_settings.config);
models, parts and metadata are written fresh.
"""
import sys, os, json, uuid, zipfile, numpy as np, trimesh, manifold3d
from skimage.measure import marching_cubes

NAMES = {'black': ('Fur: limbs, shoulders, ears, eye patches, nose (black)', 1), 'white': ('Fur: head, chest, belly (white)', 2),
         'green': ('Bamboo shoot and sprouts (green)', 7), 'tan': ('Backpack and straps (tan)', 5),
         'olive': ('Bedroll (olive)', 4), 'base': ('Flagstone base (grey)', 6)}

def mesh(field, xs, ys, zs, eps=0.01):
    f = np.pad(field, 1, constant_values=1.0)
    vox = float(xs[1] - xs[0])
    v, fa, _, _ = marching_cubes(f, 1e-4, spacing=(vox, vox, vox))   # off-zero level: no faces on exact planes
    v += np.array([xs[0], ys[0], zs[0]]) - vox
    m = trimesh.Trimesh(v, fa, process=False)
    if m.volume < 0: m.invert()
    if eps > 0:                                    # manifold-preserving simplification, max deviation eps mm
        mf = manifold3d.Manifold(manifold3d.Mesh(m.vertices.astype(np.float32), m.faces.astype(np.uint32))).simplify(eps)
        mm = mf.to_mesh(); m2 = trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)
        if m2.is_watertight: m = m2
    parts = m.split(only_watertight=False)
    m = trimesh.util.concatenate([p for p in parts if p.volume > 0.05]) if len(parts) > 1 else m
    return m

def write_3mf(path, parts, settings):
    """parts: list of (name, extruder, trimesh). One object with one volume per colour, plate centred at 128,128."""
    obj_xml = ['<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
               'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
               ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n']
    comps, cfg_parts = [], []
    for i, (name, ext, m) in enumerate(parts):
        oid = 1001 + i
        obj_xml.append(f'  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model">\n   <mesh>\n    <vertices>\n')
        obj_xml.append(''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>\n' for x, y, z in m.vertices))
        obj_xml.append('    </vertices>\n    <triangles>\n')
        obj_xml.append(''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in m.faces))
        obj_xml.append('    </triangles>\n   </mesh>\n  </object>\n')
        comps.append(f'    <component p:path="/3D/Objects/object_1.model" objectid="{oid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n')
        cfg_parts.append(f'    <part id="{oid}" subtype="normal_part">\n      <metadata key="name" value="{name}"/>\n'
                         f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n      <metadata key="extruder" value="{ext}"/>\n'
                         f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n')
    obj_xml.append(' </resources>\n <build/>\n</model>\n')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
             ' <metadata name="Application">BambuStudio-02.09.01.70</metadata>\n <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
             ' <metadata name="Title">Bobby Panda mini</metadata>\n <metadata name="Origin">original</metadata>\n <resources>\n'
             f'  <object id="2001" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n' + ''.join(comps) + '   </components>\n  </object>\n </resources>\n'
             f' <build p:UUID="{uuid.uuid4()}">\n  <item objectid="2001" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/>\n </build>\n</model>\n')
    cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <object id="2001">\n    <metadata key="name" value="Bobby Panda mini"/>\n    <metadata key="extruder" value="1"/>\n'
           + ''.join(cfg_parts) + '  </object>\n  <plate>\n    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value="Bobby Panda"/>\n'
           '    <metadata key="locked" value="false"/>\n    <model_instance>\n      <metadata key="object_id" value="2001"/>\n      <metadata key="instance_id" value="0"/>\n'
           '      <metadata key="identify_id" value="902001"/>\n    </model_instance>\n  </plate>\n  <assemble>\n'
           '   <assemble_item object_id="2001" instance_id="0" transform="1 0 0 0 1 0 0 0 1 128 128 0" offset="0 0 0" />\n  </assemble>\n</config>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    mrels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
             ' <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
          ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
          ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
          ' <Default Extension="png" ContentType="image/png"/>\n <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('[Content_Types].xml', ct); z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model); z.writestr('3D/_rels/3dmodel.model.rels', mrels)
        z.writestr('3D/Objects/object_1.model', ''.join(obj_xml))
        z.writestr('Metadata/model_settings.config', cfg)
        z.writestr('Metadata/project_settings.config', json.dumps(settings, indent=4))

SINGLE = {'layer_height': '0.08', 'initial_layer_print_height': '0.2', 'wall_loops': '3', 'sparse_infill_density': '15%',
          'sparse_infill_pattern': 'gyroid', 'seam_position': 'back',
          'enable_support': '1', 'support_type': 'tree(auto)', 'support_style': 'tree_organic', 'support_threshold_angle': '40',
          'support_on_build_plate_only': '0', 'support_top_z_distance': '0.08', 'support_bottom_z_distance': '0.08',
          'support_interface_top_layers': '2'}

# SUNLU PLA+ 2.0 (standard, not the High Speed version). SUNLU: nozzle 205-215 C at 50-100 mm/s, bed 50-60 C.
# A 0.08 mm mini never goes fast, so: 210 C (215 first layer), 55 C bed (60 first layer), full cooling,
# 15 mm3/s cap, at least 8 s per layer so the head, ears and staff tip cool between layers.
SUNLU_PLA_PLUS_2 = {
    'filament_vendor': 'SUNLU', 'filament_type': 'PLA', 'filament_settings_id': 'SUNLU PLA+ 2.0 (Bobby mini)', 'filament_ids': 'GFL99',
    'nozzle_temperature': '210', 'nozzle_temperature_initial_layer': '215',
    'nozzle_temperature_range_low': '205', 'nozzle_temperature_range_high': '245',
    'hot_plate_temp': '55', 'hot_plate_temp_initial_layer': '60', 'textured_plate_temp': '55', 'textured_plate_temp_initial_layer': '60',
    'eng_plate_temp': '55', 'eng_plate_temp_initial_layer': '60',
    'filament_density': '1.24', 'filament_flow_ratio': '0.98', 'filament_max_volumetric_speed': '15',
    'fan_min_speed': '100', 'fan_max_speed': '100', 'overhang_fan_speed': '100', 'close_fan_the_first_x_layers': '1',
    'slow_down_for_layer_cooling': '1', 'slow_down_layer_time': '8', 'slow_down_min_speed': '10',
}
def set_filament(settings, slot, values):
    """Set per-filament keys for filament `slot` (1-based): 9-long arrays hold one value per filament,
    54-long ones hold 6 extruder variants per filament."""
    n = len(settings['filament_colour'])
    for k, v in values.items():
        cur = settings.get(k)
        if not isinstance(cur, list): continue
        per = len(cur) // n
        cur[(slot - 1) * per:slot * per] = [v] * per
# fine-detail walls for a 32 mm figure
MINI_SPEEDS = {'outer_wall_speed': '40', 'inner_wall_speed': '60', 'small_perimeter_speed': '50%', 'initial_layer_speed': '25'}

if __name__ == '__main__':
    src, tpl, out = sys.argv[1:4]
    multi = '--multi' in sys.argv
    d = np.load(src); xs, ys, zs = d['xs'], d['ys'], d['zs']
    fields = {'black': np.minimum(d['black'], d['arms']), 'white': np.minimum(d['white'], d['sclera']),
              'green': d['green'], 'tan': d['tan'], 'olive': d['olive'], 'base': d['base']}
    settings = json.loads(zipfile.ZipFile(tpl).read('Metadata/project_settings.config'))
    os.makedirs(out, exist_ok=True)
    one = d['solid'] if 'solid' in d.files else np.min(np.stack(list(fields.values())), 0)   # true surface, no seams at colour edges
    m = mesh(one, xs, ys, zs)
    m.export(os.path.join(out, 'bobby-panda-mini-single-colour.stl'))
    print('single colour', m.is_watertight, 'bodies', len(m.split(only_watertight=False)), 'size %.1f x %.1f x %.1f' % tuple(m.extents), len(m.faces), 'faces')
    # single-colour print project (for painting): one part, filament 1 = SUNLU PLA+ 2.0, 0.08 mm layers, organic tree supports, seam at the back
    s1 = json.loads(json.dumps(settings)); s1.update(SINGLE)
    for k, v in MINI_SPEEDS.items(): s1[k] = [v] * len(s1[k]) if isinstance(s1.get(k), list) else v
    set_filament(s1, 1, SUNLU_PLA_PLUS_2)
    if float(s1['nozzle_diameter'][0]) <= 0.25:                     # 0.2 mm nozzle: thin first layer, lower flow cap, 4 walls (0.22 mm lines)
        s1.update({'initial_layer_print_height': '0.1', 'wall_loops': '4'})
        set_filament(s1, 1, {'filament_max_volumetric_speed': '3'})
    write_3mf(os.path.join(out, 'bobby-panda-mini-single-colour.3mf'), [('Bobby Panda (single colour, for painting)', 1, m)], s1)
    if multi:
        parts = []
        for k, f in fields.items():
            pm = mesh(f, xs, ys, zs)
            print(f'{k:6s} faces {len(pm.faces):7d} watertight {pm.is_watertight} volume {pm.volume:7.1f} mm3')
            parts.append((NAMES[k][0], NAMES[k][1], pm))
        s2 = dict(settings); s2.update(SINGLE); s2.update({'layer_height': '0.1', 'flush_multiplier': ['1.0', '1.0'], 'enable_prime_tower': '1'})
        write_3mf(os.path.join(out, 'bobby-panda-mini.3mf'), parts, s2)
