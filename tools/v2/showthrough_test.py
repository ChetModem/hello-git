"""Show-through test: Knight v2 and Victory Point v2 on the original development back,
at 0.5 mm (as v1) and at 0.6 mm with one hidden black layer between the colour and the back logo."""
import sys, os, pickle, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); SPD = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SPD, 'special'))
import cards_v2 as C
import build as B
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity
body_mesh = B.template_mesh(11)
s = body_mesh.section([0, 0, 1], [0, 0, 0.25]); q, T = s.to_2D()
OUTLINE = affinity.affine_transform(unary_union(q.polygons_full), [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]]).buffer(0)
def card_parts_t(face, corner, back, thick):
    """Same parts as the other cards; for thick > 0.5 the card body runs to `thick` and the back logo moves up,
    so a black layer sits between the colour (to 0.3 mm) and the white logo."""
    parts = [('Card', 1, B.extrude(OUTLINE, 0.0, thick), {})]
    for k, cid in enumerate((12, 13, 14, 15)): parts.append((f'Corner hex {k + 1}', corner, B.template_mesh(cid), {}))
    for k, cid in enumerate((18, 19, 20, 21)): parts.append((f'Corner hex backing {k + 1}', corner, B.template_mesh(cid), {}))
    for slot, g in sorted(face.items()):
        g = B.mirror(g)
        parts.append((f'Icon colour {slot}', slot, B.extrude(g, *B.FACE), {}))
        parts.append((f'Icon backing colour {slot}', slot, B.extrude(g, *B.BACKING), {}))
    parts.append(('Rear logo', 2, B.extrude(B.mirror(back), thick - 0.2, thick), {'top_surface_pattern': 'monotonicline'}))
    return parts
back = C.back_dev_v1()
objs = []
for (name, f), x in zip([('Knight', C.knight), ('Victory Point', C.victory_point)], (46.5, 101.5)):
    face, corner = f()
    objs.append(dict(name=f'{name} 0.5 mm', plate=1, x=x, y=131.5, parts=card_parts_t(face, corner, back, 0.5)))
    objs.append(dict(name=f'{name} 0.6 mm', plate=1, x=x + 110, y=131.5, parts=card_parts_t(face, corner, back, 0.6)))
B.write_project('/home/user/hello-git/catan-backs-showthrough-test.3mf', objs, ['Show-through: 0.5 mm (left pair) vs 0.6 mm (right pair)'])
print('written')
