import pickle, numpy as np, trimesh, sys, re, uuid, xml.dom.minidom as xm
from shapely.ops import unary_union
D = sys.argv[1]; d = pickle.load(open(f'{D}/../overhang_55.pkl', 'rb'))
zs, L, reach, it = d['zs'], d['L'], d['reach'], d['it']; H = 0.08
def clean(g, a=0.05):
    g = g.buffer(-0.03).buffer(0.03); gs = list(g.geoms) if hasattr(g, 'geoms') else [g]
    return unary_union([x for x in gs if x.area > a])
F = [None] * len(zs); F[-1] = L[-1]
for k in range(len(zs) - 2, -1, -1):
    F[k] = L[k].union(F[k + 1].buffer(-reach)).buffer(0)
fill = [clean(F[k].difference(L[k]).buffer(0.02).intersection(F[k])) for k in range(len(zs))]   # small overlap into the model so it fuses
slabs = []
for k, g in enumerate(fill):
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        if p.is_empty or p.area < 0.05: continue
        e = trimesh.creation.extrude_polygon(p.simplify(0.01), H + 0.002); e.vertices[:, 2] += zs[k] - H / 2 - 0.001; slabs.append(e)
print(f'fill: {sum(g.area for g in fill) * H:.1f} mm3 in {len(slabs)} slabs over {sum(1 for g in fill if g.area > 0)} layers')
m = trimesh.boolean.union(slabs, engine='manifold') if len(slabs) > 1 else slabs[0]
print('fill mesh watertight', m.is_watertight, 'faces', len(m.faces), 'z %.2f..%.2f' % (m.bounds[0][2], m.bounds[1][2]))
pickle.dump({'fill': fill, 'zs': zs}, open(f'{D}/../fill_layers.pkl', 'wb'))
# add as a part of the tile (filament 1), in object-local coordinates
m.vertices[:, 2] -= it[11]
p = f'{D}/3D/Objects/object_3048.model'; o = open(p).read(); s = open(f'{D}/3D/3dmodel.model').read(); ms = open(f'{D}/Metadata/model_settings.config').read()
nid = '6'; assert f'<object id="{nid}"' not in o
vx = ''.join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in m.vertices); tx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in m.faces)
o = o.replace('</resources>', f' <object id="{nid}" p:UUID="{uuid.uuid4()}" type="model">\n  <mesh>\n   <vertices>\n{vx}   </vertices>\n   <triangles>\n{tx}   </triangles>\n  </mesh>\n </object>\n</resources>', 1)
open(p, 'w').write(o)
# insert the component before the modifier so solid parts come first
s = re.sub(r'(<component p:path="/3D/Objects/object_3048.model" objectid="5")', f'<component p:path="/3D/Objects/object_3048.model" objectid="{nid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n    \\1', s, count=1)
open(f'{D}/3D/3dmodel.model', 'w').write(s)
part = (f'    <part id="6" subtype="normal_part" uuid="{uuid.uuid4()}">\n      <metadata key="name" value="Overhang fill"/>\n'
        '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n      <metadata key="extruder" value="1"/>\n'
        f'      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n')
ms = ms.replace('    <part id="5" subtype="modifier_part"', part + '    <part id="5" subtype="modifier_part"', 1)
# assemble volumes follow part order: fill becomes volume 4, modifier volume 5
ms = ms.replace('<assemble_item object_id="5" volume_id="4" transform="1 0 0 0 1 0 0 0 1 0 0 0" />', '<assemble_item object_id="5" volume_id="4" transform="1 0 0 0 1 0 0 0 1 0 0 0" />\n   <assemble_item object_id="5" volume_id="5" transform="1 0 0 0 1 0 0 0 1 0 0 0" />', 1)
ms = ms.replace('value="Forest tile X2D test v3"', 'value="Forest tile X2D v4 (repaired, overhangs filled)"')
open(f'{D}/Metadata/model_settings.config', 'w').write(ms)
for f in ['3D/3dmodel.model', 'Metadata/model_settings.config', '3D/Objects/object_3048.model']: xm.parse(f'{D}/{f}')
print('parts:', re.findall(r'<part id="(\d+)" subtype="(\w+)">\s*<metadata key="name" value="([^"]+)"', ms))
