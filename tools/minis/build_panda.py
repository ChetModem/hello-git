"""Write the panda mini as a multi-colour Bambu project (X2D, AMS) and a single-colour STL."""
import os, sys, json, pickle, zipfile, shutil, subprocess, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'special'))
import build as B
P = pickle.load(open(os.path.join(HERE, 'panda_parts.pkl'), 'rb'))
names = {'base': 'Stone base (grey)', 'white': 'Body (white)', 'black': 'Limbs, ears, eye patches, strap (black)', 'green': 'Bamboo staff (green)'}
parts = [(names[k], slot, trimesh.Trimesh(v, f, process=True), {}) for k, (slot, (v, f)) in P.items()]
for n, s, m, _ in parts: assert m.is_watertight, n
OUT = '/home/user/hello-git/minis/panda-adventurer-mini.3mf'
d = B.write_project(OUT, [dict(name='Panda adventurer mini', plate=1, x=128.0, y=128.0, parts=parts)], ['Panda adventurer mini'])
# print settings for a small figure: supports on (tree, auto) for the head and arms, 3 walls, 20% infill
c = json.load(open(f'{d}/Metadata/project_settings.config'))
c.update({'enable_support': '1', 'support_type': 'tree(auto)', 'support_threshold_angle': '30', 'wall_loops': '3', 'sparse_infill_density': '20%'})
json.dump(c, open(f'{d}/Metadata/project_settings.config', 'w'), indent=4)
os.remove(OUT); subprocess.run(f"cd '{d}' && zip -q -X '{OUT}' '[Content_Types].xml' && zip -q -r -X '{OUT}' . -x '[Content_Types].xml'", shell=True, check=True)
one = trimesh.boolean.union([m for _, _, m, _ in parts], engine='manifold'); one.export('/home/user/hello-git/minis/panda-adventurer-mini-single-colour.stl')
print('written', OUT, '| single colour STL', one.is_watertight, 'size %.1f x %.1f x %.1f' % tuple(one.extents))
