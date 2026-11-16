"""v2 rules legend + stand: board from legend_v2, feet with a hexagon cut-out and a lead-in chamfer on the slot.
Writes catan-rules-legend-with-stand-v2.3mf (v1 file kept)."""
import os, sys, pickle, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'special'))
import design as D, build as B, glyphs as G
from shapely.geometry import Polygon
from shapely import affinity
res, H = pickle.load(open(os.path.join(HERE, 'legend_v2.pkl'), 'rb'))
W = 240.0; BOARD_T = D.BOARD_T
HEX_R = 3.6            # cut-out: point-up hexagon (60-degree sides print without supports), 7.2 mm tall
HEX_C = (37.0, 7.5)    # behind the slot, in the foot's deepest part (walls >= 3.5 mm all round)
CHAMFER = 1.2          # lead-in on both top edges of the slot

def stand_profile_v2():
    p = D.stand_profile()
    a = np.radians(D.LEAN); top = 15.0
    yc = 19.0 + (top - 4.0) * np.tan(a); w = D.SLOT / np.cos(a)                     # slot centre and width where it meets the top
    lead = Polygon([(yc - w / 2 - CHAMFER, top + 0.5), (yc + w / 2 + CHAMFER, top + 0.5), (yc + w / 2, top - CHAMFER), (yc - w / 2, top - CHAMFER)])
    hexa = Polygon([(HEX_C[0] + HEX_R * np.sin(np.radians(t)), HEX_C[1] + HEX_R * np.cos(np.radians(t))) for t in range(0, 360, 60)])
    return p.difference(lead).difference(hexa).buffer(0), hexa, lead

if __name__ == '__main__':
    prof, hexa, lead = stand_profile_v2()
    parts = [('Board', 1, B.extrude(G.rr(-W / 2, -H / 2, W / 2, H / 2, 4), 0.0, BOARD_T), {})]
    for slot, g in sorted(res.items()):
        g = B.mirror(g)
        parts.append((f'Legend colour {slot}', slot, B.extrude(g, *B.FACE), {}))
        parts.append((f'Legend backing colour {slot}', slot, B.extrude(g, *B.BACKING), {}))
    foot = trimesh.creation.extrude_polygon(prof, D.FOOT_W)
    foot.apply_transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    foot.apply_translation([-D.FOOT_W / 2, -27.0, 0])
    if foot.volume < 0: foot.invert()
    assert foot.is_watertight
    objs = [dict(name='Rules legend v2', plate=1, x=128.0, y=128.0, parts=parts),
            dict(name='Legend stand left', plate=2, x=98.0, y=128.0, parts=[('Stand foot', 1, foot, {})]),
            dict(name='Legend stand right', plate=2, x=158.0, y=128.0, parts=[('Stand foot', 1, foot.copy(), {})])]
    out = '/home/user/hello-git/catan-rules-legend-with-stand-v2.3mf'
    B.write_project(out, objs, ['Rules legend v2', 'Legend stand (2 feet)'])
    b = prof.bounds; walls = prof.exterior.distance(hexa.exterior) if False else None
    print('written', out, 'board %.0f x %.1f' % (W, H), '| foot %.0f x %.0f x %.0f' % (b[2]-b[0], b[3]-b[1], D.FOOT_W))
    # wall thickness around the hexagon, and around the slot
    body = D.stand_profile().buffer(0)
    print('thinnest wall round the hexagon: %.2f mm' % min(hexa.exterior.distance(Polygon(body.exterior).exterior), min((hexa.distance(Polygon(i)) for i in body.interiors), default=99),
                                                          hexa.distance(body.symmetric_difference(Polygon(body.exterior)))))
