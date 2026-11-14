import sys,re,numpy as np,trimesh
src=open('/home/user/hello-git/tools/catan_overhang_probe.py').read()
# reuse the probe's loading + layer code, then test its overhang points against the real solid
head=src.split('def safe_z')[0]
exec(head.replace("sys.argv[1],sys.argv[2]","sys.argv[1],sys.argv[2]"))
exec('def safe_z'+src.split('def safe_z')[1].split('\n\n')[0])
from shapely.ops import unary_union
H=0.08; REACH=H*np.tan(np.radians(55))
def L(z): return unary_union([g for _,m in ms for dz in (-0.013,0.011) for g in [sec(m,safe_z(z+dz))] if g is not None]).buffer(0)
for z in map(float,sys.argv[3:]):
    o=L(z).difference(L(z-H).buffer(REACH)).buffer(-0.03).buffer(0.03)
    pts=[]
    for p in (o.geoms if hasattr(o,'geoms') else [o]):
        if p.area<0.05: continue
        for _ in range(20):
            q=p.representative_point() if not pts or _==0 else None
            x0,y0,x1,y1=p.bounds; r=np.random.default_rng(len(pts)).uniform([x0,y0],[x1,y1])
            from shapely.geometry import Point
            if p.contains(Point(*r)): pts.append((r[0],r[1],p.area))
        rp=p.representative_point(); pts.append((rp.x,rp.y,p.area))
    pts=np.array(pts)
    if not len(pts): print(z,'no overhang'); continue
    P=np.c_[pts[:,:2],np.full(len(pts),z)]
    ins=np.zeros(len(P),bool)
    for _,m in ms: ins|=m.contains(P)
    print(f'z {z}: overhang area {o.area:.2f} mm2, sample points really inside solid: {ins.sum()} of {len(P)}')
