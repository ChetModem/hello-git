"""For every item with an Overhang fill: on a 0.25 mm grid over each separate fill blob, is the fill ever the topmost surface?"""
import re,glob,os,sys,numpy as np,trimesh
from trimesh.ray.ray_triangle import RayMeshIntersector as RMI
D=sys.argv[1]
FILES={os.path.basename(f):open(f).read() for f in glob.glob(f'{D}/3D/Objects/*.model')}
S=open(f'{D}/3D/3dmodel.model').read(); MS=open(f'{D}/Metadata/model_settings.config').read()
def mat(tr):
    a=list(map(float,tr.split())); M=np.eye(4); M[:3,:3]=np.array(a[:9]).reshape(3,3).T; M[:3,3]=a[9:12]; return M
def mesh(fn,cid):
    o=FILES[fn]; i=o.find(f'<object id="{cid}"'); b=o[i:o.find('</object>',i)]
    return trimesh.Trimesh(np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',b),float),np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',b),int),process=False)
seen={}; bad_total=0
for oid,tr in re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"',S):
    mo=re.search(rf'<object id="{oid}">.*?</object>',MS,re.S).group(0)
    parts=re.findall(r'<part id="\d+" subtype="(\w+)"[^>]*>\s*<metadata key="name" value="([^"]+)"',mo)
    if not any(n=='Overhang fill' for _,n in parts): continue
    oname=re.search(r'<metadata key="name" value="([^"]+)"',mo).group(1)
    ob=S[S.find(f'<object id="{oid}"'):]; ob=ob[:ob.find('</object>')]
    comps=re.findall(r'p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]*)"',ob)
    sig=tuple((c[1],c[2]) for c in comps)
    if sig in seen: continue
    seen[sig]=oid; M=mat(tr); model=[]
    for (path,cid,ctr),(st,n) in zip(comps,parts):
        if st!='normal_part': continue
        m=mesh(path.split('/')[-1],cid); m.apply_transform(M@mat(ctr))
        (model.append(m) if n!='Overhang fill' else None)
        if n=='Overhang fill': fill=m
    am=trimesh.util.concatenate(model); R=RMI(am); top=am.bounds[1][2]+5
    worst=0; nbad=0; area=0
    for b in fill.split(only_watertight=False):
        c=b.bounds; g=np.mgrid[c[0][0]:c[1][0]+0.25:0.25,c[0][1]:c[1][1]+0.25:0.25].reshape(2,-1).T
        org=np.c_[g,np.full(len(g),top)]; dn=np.tile([0,0,-1.],(len(g),1))
        lf,rf,_=RMI(b).intersects_location(org,dn,multiple_hits=False)
        if not len(rf): continue
        hf=np.full(len(g),np.nan); hf[rf]=lf[:,2]
        lm,rm,_=R.intersects_location(org,dn,multiple_hits=False); hm=np.full(len(g),-1.); hm[rm]=lm[:,2]
        d=hf-hm; up=~np.isnan(hf)&(d>0.02)
        if up.any(): nbad+=1; worst=max(worst,np.nanmax(d[up])); area+=up.sum()*0.0625
    bad_total+=nbad
    print(f'{oname} #{oid}: fill blobs {len(fill.split(only_watertight=False))}, blobs that show on top: {nbad}, area {area:.1f} mm2, highest {worst:.2f} mm')
print('RESULT:', 'CLEAN' if bad_total==0 else f'{bad_total} exposed blobs')
