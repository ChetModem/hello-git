import sys, os, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); SPD = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SPD, 'special'))
import cards_v2 as C
import build as B            # the special-cards builder (same template, same print settings)
dev_back = pickle.load(open(os.path.join(SPD, 'dev_shapes.pkl'), 'rb'))['knight']['logo']   # v1 three-ring development back
objs = []
for name, f, (x, y) in [('Knight v2 on v1 back', C.knight, (101.5, 131.5)), ('Victory Point on v1 back', C.victory_point, (156.5, 131.5))]:
    face, corner = f()
    objs.append(dict(name=name, plate=1, x=x, y=y, parts=B.card_parts(face, corner, corners=True, back=dev_back)))
B.write_project('/home/user/hello-git/catan-backs-showthrough-test.3mf', objs, ['Show-through test (2 cards)'])
print('written')
