import re,numpy as np,trimesh
from PIL import Image, ImageDraw, ImageFont
D='v5b'
o=open(f'{D}/3D/Objects/object_3048.model').read(); s=open(f'{D}/3D/3dmodel.model').read(); ms=open(f'{D}/Metadata/model_settings.config').read()
ob=s[s.find('<object id="5"'):]; ob=ob[:ob.find('</object>')]
comps=re.findall(r'objectid="(\d+)"[^>]*transform="([^"]*)"',ob)
sub=re.findall(r'<part id="\d+" subtype="(\w+)"[^>]*>\s*<metadata key="name" value="([^"]+)"',ms)
def mesh(cid,tr):
    i=o.find(f'<object id="{cid}"'); b=o[i:o.find('</object>',i)]
    v=np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',b),float)+list(map(float,tr.split()[9:12]))
    return trimesh.Trimesh(v,np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"',b),int),process=False)
P={n:mesh(c,tr) for (c,tr),(st,n) in zip(comps,sub) if st=='normal_part'}
fill=P.pop('Overhang fill'); model=list(P.values())
z0=min(m.bounds[0][2] for m in model)
for m in model+[fill]: m.apply_translation([0,0,-z0])
# pick trees: biggest fill blobs
blobs=sorted(fill.split(only_watertight=False),key=lambda b:-b.volume)
picks=[]
for b in blobs:
    c=b.centroid
    if all(np.hypot(c[0]-p[0],c[1]-p[1])>9 for p in picks): picks.append(c)
    if len(picks)==6: break
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
sc=22; W=int(16*sc); Hh=int(13*sc)
tiles=[]
for c in picks:
    row=[]
    for with_fill in (False,True):
        img=Image.new('RGB',(W,Hh),'white'); d=ImageDraw.Draw(img)
        for m,col in [(x,(120,120,120)) for x in model]+([(fill,(255,140,0))] if with_fill else []):
            sx=m.section([0,1,0],[0,c[1],0])
            if sx is None: continue
            for e in sx.discrete:
                e=np.asarray(e); pts=[((x-c[0]+8)*sc,Hh-8-z*sc) for x,_,z in e]
                if len(pts)>2: d.polygon(pts,fill=col)
        row.append(img)
    tiles.append(row)
out=Image.new('RGB',(2*W+30,len(tiles)*(Hh+10)+70),'white'); d=ImageDraw.Draw(out)
d.text((10,8),'Side cuts through 6 trees on forest v5 (same scale, 16 mm wide).',fill='black',font=F)
d.text((10,30),'Left: original model.   Right: with overhang fill (orange).',fill='black',font=F)
for i,(a,b) in enumerate(tiles):
    y=60+i*(Hh+10); out.paste(a,(0,y)); out.paste(b,(W+30,y))
out.save('/home/user/hello-git/catan-forest-v5-tree-cuts.png'); print(out.size, [np.round(p[:2],1) for p in picks])
