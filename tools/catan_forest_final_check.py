import re,sys,numpy as np,trimesh
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry import Point
D=sys.argv[1]
s=open(f'{D}/3D/3dmodel.model').read(); o=open(f'{D}/3D/Objects/object_3048.model').read(); ms=open(f'{D}/Metadata/model_settings.config').read()
it=np.array(list(map(float,re.search(r'<item objectid="5"[^>]*transform="([^"]*)"',s).group(1).split())))
M=np.eye(4); M[:3,:3]=it[:9].reshape(3,3).T if False else np.array([[it[0],it[3],it[6]],[it[1],it[4],it[7]],[it[2],it[5],it[8]]]); M[:3,3]=it[9:12]
ob=s[s.find('<object id="5"'):]; ob=ob[:ob.find('</object>')]
comps=re.findall(r'objectid="(\d+)"[^>]*transform="([^"]*)"',ob)
sub=re.findall(r'<part id="\d+" subtype="(\w+)"[^>]*>\s*<metadata key="name" value="([^"]+)"',ms)
def mesh(cid,tr,world=True):
    i=o.find(f'<object id="{cid}"'); b=o[i:o.find('</object>',i)]
    v=np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',b),float)+list(map(float,tr.split()[9:12]))
    m=trimesh.Trimesh(v,np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',b),int),process=False)
    if world: m.apply_transform(M)
    return m
P={n:mesh(c,tr) for (c,tr),(st,n) in zip(comps,sub)}
model=[P[n] for n in P if n.startswith('wood')]; fill=P['Overhang fill']; mod=P['Recess ironing']
allm=trimesh.util.concatenate(model+[fill]); b=allm.bounds
print('1. world bounds x %.2f-%.2f y %.2f-%.2f z %.3f-%.3f (bed 0-256, height limit 261)'%(b[0][0],b[1][0],b[0][1],b[1][1],b[0][2],b[1][2]))
print('   part z-min:',{n:round(P[n].bounds[0][2],3) for n in P})
zall=np.unique(np.concatenate([m.vertices[:,2] for m in model+[fill]]))
def safe(z):
    for _ in range(40):
        i=np.searchsorted(zall,z); d=min(abs(zall[i-1]-z) if i>0 else 1,abs(zall[i]-z) if i<len(zall) else 1)
        if d>4e-5: return z
        z+=1.3e-4
    return z
def L(ms_,z):
    gs=[]
    for m in ms_:
        S_=m.section([0,0,1],[0,0,safe(z)])
        if S_ is None: continue
        q,T=S_.to_2D(); gs.append(affinity.affine_transform(unary_union(q.polygons_full),[T[0,0],T[0,1],T[1,0],T[1,1],T[0,3],T[1,3]]))
    return unary_union(gs).buffer(0) if gs else Point(0,0).buffer(0)
# 2. fill never forms a visible top surface: fill area at z not covered by (model+fill) at z+0.08
zs=np.arange(0.24,b[1][2],0.08); worst=0; exposed=[]
for z in zs:
    f=L([fill],z)
    if f.is_empty: continue
    up=L(model+[fill],z+0.08)
    e=f.difference(up).buffer(-0.05).buffer(0.05)   # ignore numerical hairlines
    if e.area>0.05: exposed.append((round(z,2),round(e.area,2)))
print('2. fill exposed on top (z, mm2):',exposed[:15],'... total layers',len(exposed))
# 3. fill touching the recess / the outside edge of the tile
base=L(model,1.0); rc=Point(*np.array([47,48])).buffer(14.2)
c=M@np.array([47,48,0,1]); rcw=Point(c[0],c[1]).buffer(14.2)
fz=[ (round(z,2),round(L([fill],z).intersection(rcw).area,2)) for z in np.arange(2.3,4.0,0.08)]
print('3. fill inside the recess circle:',[x for x in fz if x[1]>0.01] or 'none')
fo=max(L([fill],z).difference(base.buffer(0.01)).area for z in np.arange(0.24,b[1][2],0.4))
print('   fill outside tile footprint (mm2, max over heights):',round(fo,3))
# 4. top-surface heights by ray casting on a 0.25 mm grid
from trimesh.ray.ray_triangle import RayMeshIntersector
R=RayMeshIntersector(allm)
def top(xy):
    org=np.c_[xy,np.full(len(xy),b[1][2]+5)]; loc,ri,tri=R.intersects_location(org,np.tile([0,0,-1],(len(xy),1)),multiple_hits=False)
    h=np.full(len(xy),np.nan); h[ri]=loc[:,2]; n=np.full((len(xy),3),np.nan); n[ri]=allm.face_normals[tri]; return h,n
g=np.mgrid[c[0]-13.5:c[0]+13.5:0.25,c[1]-13.5:c[1]+13.5:0.25].reshape(2,-1).T
g=g[np.hypot(g[:,0]-c[0],g[:,1]-c[1])<13.3]; h,n=top(g)
print('4. recess floor heights: min %.3f max %.3f, points not at 2.400: %d of %d'%(np.nanmin(h),np.nanmax(h),(abs(h-2.4)>0.005).sum(),len(h)))
# 5. what the ironing modifier covers: heights and slopes of top surfaces inside it
mm=L([mod],2.7); gb=mm.bounds; g2=np.mgrid[gb[0]:gb[2]:0.25,gb[1]:gb[3]:0.25].reshape(2,-1).T
from shapely import contains_xy
g2=g2[contains_xy(mm,g2[:,0],g2[:,1])]; h2,n2=top(g2); ang=np.degrees(np.arccos(np.clip(n2[:,2],-1,1)))
print('5. ironing area: %d sample points; top surface z %.2f-%.2f; tilt >2 deg at %d points (%.1f%%); topmost hit above 3.3 (outside modifier, not ironed): %d'%(len(g2),np.nanmin(h2),np.nanmax(h2),(ang>2).sum(),100*(ang>2).mean(),(h2>3.3).sum()))
inr=(h2>2.5)&(h2<=3.3); print('   flat-ground part: z values',np.round(np.percentile(h2[inr],[0,5,50,95,100]),3),'tilt pct>2deg',round(100*(ang[inr]>2).mean(),1))
# 6. hut: what is under its roof
print('6. modifier z range %.2f-%.2f'%(mod.bounds[0][2],mod.bounds[1][2]))
inmod=h2<=2.8
print('7. top surfaces actually inside the ironing modifier: %d points, heights %s, tilted >0.5 deg: %d'%(inmod.sum(),np.unique(np.round(h2[inmod],3)),(ang[inmod]>0.5).sum()))
