import re,sys,numpy as np,trimesh
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry import Polygon
D,oid=sys.argv[1],sys.argv[2]
S=open(f'{D}/3D/3dmodel.model').read()
def mesh(fn,cid):
    o=open(f'{D}/3D/Objects/{fn}').read(); i=o.find(f'<object id="{cid}"'); b=o[i:o.find('</object>',i)]
    v=np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',b),float); t=np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',b),int); return trimesh.Trimesh(v,t,process=False)
ob=S[S.find(f'<object id="{oid}"'):]; ob=ob[:ob.find('</object>')]
ms=[]
for path,cid,tr in re.findall(r'<component p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]*)"',ob):
    m=mesh(path.split('/')[-1],cid); m.apply_translation(list(map(float,tr.split()[9:12]))); ms.append((cid,m))
z0=min(m.bounds[0][2] for _,m in ms)
for _,m in ms: m.apply_translation([0,0,-z0])
def sec(m,z):
    S_=m.section([0,0,1],[0,0,z])
    if S_ is None: return None
    q,T=S_.to_2D(); return affinity.affine_transform(unary_union(q.polygons_full),[T[0,0],T[0,1],T[1,0],T[1,1],T[0,3],T[1,3]])
zall=np.unique(np.concatenate([m.vertices[:,2] for _,m in ms]))
def safe_z(z):
    for _ in range(40):
        i=np.searchsorted(zall,z); d=min(abs(zall[i-1]-z) if i>0 else 1, abs(zall[i]-z) if i<len(zall) else 1)
        if d>4e-5: return z
        z+=1.3e-4
    return z
H=0.08; reach=H*np.tan(np.radians(55)); zt=max(m.bounds[1][2] for _,m in ms)
prev=None; tot=0; worst=[]
for z in np.arange(H/2,zt,H):
    g=unary_union([x for _,m in ms for dz in (-0.013,0.011) for x in [sec(m,safe_z(z+dz))] if x is not None]).buffer(0)
    if prev is not None:
        u=g.difference(prev.buffer(reach)).buffer(-0.03).buffer(0.03)
        a=sum(p.area for p in (u.geoms if hasattr(u,'geoms') else [u]) if p.area>0.05); tot+=a
        if a>1: worst.append((round(z,2),round(a,1),round(g.area,1),round(prev.area,1)))
    prev=g
print(f'object {oid}: total {tot:.1f} mm2; layers with >1 mm2:',worst[:12])
