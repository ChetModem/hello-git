import re,glob,os,sys,numpy as np,trimesh
D=sys.argv[1]
FILES={os.path.basename(f):open(f).read() for f in glob.glob(f'{D}/3D/Objects/*.model')}
S=open(f'{D}/3D/3dmodel.model').read(); MS=open(f'{D}/Metadata/model_settings.config').read()
def mesh(fn,cid):
    o=FILES[fn]; i=o.find(f'<object id="{cid}"'); b=o[i:o.find('</object>',i)]
    return trimesh.Trimesh(np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',b),float),np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',b),int),process=False)
seen=set()
for oid,tr in re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"',S):
    mo=re.search(rf'<object id="{oid}">.*?</object>',MS,re.S).group(0)
    parts=re.findall(r'<part id="\d+" subtype="(\w+)"[^>]*>\s*<metadata key="name" value="([^"]+)"',mo)
    if not any(n=='Overhang fill' for _,n in parts): continue
    ob=S[S.find(f'<object id="{oid}"'):]; ob=ob[:ob.find('</object>')]
    comps=re.findall(r'p:path="([^"]+)" objectid="(\d+)"[^>]*transform="([^"]*)"',ob)
    sig=tuple(c[1] for c in comps)
    if sig in seen: continue
    seen.add(sig); model=[]
    for (path,cid,ctr),(st,n) in zip(comps,parts):
        if st!='normal_part': continue
        m=mesh(path.split('/')[-1],cid); m.apply_translation(list(map(float,ctr.split()[9:12])))
        if n=='Overhang fill': fill=m
        else: model.append(m)
    u=trimesh.boolean.union(model,engine='manifold'); out=trimesh.boolean.difference([fill,u],engine='manifold')
    name=re.search(r'<metadata key="name" value="([^"]+)"',mo).group(1)
    print(f'#{oid} {name}: fill {fill.volume:.1f} mm3, of which outside the original model (real added material) {out.volume:.1f} mm3')
