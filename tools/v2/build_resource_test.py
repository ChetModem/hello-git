"""v2 resource test plate: one card of each resource (locked gold-standard icons), 0.5 mm, resource back."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); SPD = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SPD, 'special'))
import cards_v2 as C
import build as B
back = C.back_resource()
pos = [(68, 175), (128, 175), (188, 175), (98, 85), (158, 85)]
objs = []
for (name, n), (x, y) in zip([('Brick', 'brick'), ('Wood', 'wood'), ('Sheep', 'sheep'), ('Wheat', 'wheat'), ('Ore', 'ore')], pos):
    face, corner = C.resource(n)()
    objs.append(dict(name=f'{name} v2', plate=1, x=x, y=y, parts=B.card_parts(face, corner, back=back)))
OUT = '/home/user/hello-git/catan-resource-cards-v2-test.3mf'
B.write_project(OUT, objs, ['v2 resource test - one of each'])
print('written', OUT)
