"""Hand-authored counter profiles plus seeded tracing of painted grille gaps."""
import json
import numpy as np
from PIL import Image,ImageDraw
from forbes_counter_audit import OUT
from native_common import dump

FRONT='l_bar#2_09.tga021204165939'
BACK='l_bar#2_18.tga021204165939'


def simplify(points,eps):
    if len(points)<3:return points
    a=np.array(points[0]);b=np.array(points[-1]);p=np.array(points);ab=b-a
    if ab@ab==0:d=np.linalg.norm(p-a,axis=1)
    else:d=np.linalg.norm(p-a-np.clip((p-a)@ab/(ab@ab),0,1)[:,None]*ab,axis=1)
    i=int(np.argmax(d))
    return simplify(points[:i+1],eps)[:-1]+simplify(points[i:],eps) if d[i]>eps else [points[0],points[-1]]


def traced_gap(gray,x0,x1,y0,y1,seed_y):
    # Seeds are selected in the two authored grille rows. Restrict each flood
    # fill to its own narrow painted opening so neighbouring ornaments cannot
    # merge with it. This traces image darkness, not automatic feature semantics.
    left=max(0,x0-2);right=min(768,x1+2);cx=(x0+x1)//2
    mask=gray[y0:y1,left:right]<62
    seed=(seed_y-y0,cx-left)
    if not mask[seed]:return None
    seen={seed};stack=[seed]
    while stack:
        y,x=stack.pop()
        for q in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            yy,xx=q
            if 0<=yy<mask.shape[0] and 0<=xx<mask.shape[1] and mask[q] and q not in seen:seen.add(q);stack.append(q)
    if len(seen)<25:return None
    edges={}
    for y,x in seen:
        for neighbour,a,b in [((y-1,x),(x,y),(x+1,y)),((y,x+1),(x+1,y),(x+1,y+1)),
                               ((y+1,x),(x+1,y+1),(x,y+1)),((y,x-1),(x,y+1),(x,y))]:
            if neighbour not in seen:edges[a]=b
    loops=[]
    while edges:
        start=next(iter(edges));q=start;loop=[]
        while q in edges:
            loop.append(q);q=edges.pop(q)
            if q==start:break
        if len(loop)>3:loops.append(loop)
    if not loops:return None
    loop=max(loops,key=len);half=len(loop)//2
    p=simplify(loop[:half+1],1.0)[:-1]+simplify(loop[half:]+[loop[0]],1.0)[:-1]
    return [[x+left,y+y0] for x,y in p]


def main():
    build=OUT/'modeled';surfaces=json.loads((OUT/'surfaces.json').read_text());features=[]
    def add(mat,label,points,depth,bevel=1.5,method='manually authored'):
        p=np.asarray(points,float)
        if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<0:p=p[::-1]
        features.append(dict(id=f'counter_{len(features):03d}',material=mat,label=label,points_px=p.tolist(),
            depth_world=depth,bevel_px=bevel,authoring=method))
    def rect(mat,label,x0,y0,x1,y1,d,b=1.5):add(mat,label,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],d,b)
    # Main external fascia: panel fields, continuous double mouldings and joints.
    for i,(x0,x1) in enumerate([(8,102),(117,215),(230,335),(352,459),(479,588)]):
        rect(FRONT,f'Main fascia recessed field {i+1}',x0,365,x1,645,-.012,2)
    for i,(y0,y1) in enumerate([(468,485),(536,552)]):
        rect(FRONT,f'Continuous horizontal moulding {i+1}',5,y0,594,y1,.013,1.8)
    for i,(x0,x1) in enumerate([(105,114),(217,226),(339,348),(464,475),(592,603)]):
        rect(FRONT,f'Panel upright {i+1}',x0,359,x1,650,.014,1.5)
    for i,(y0,y1) in enumerate([(653,662),(704,714),(753,761)]):
        rect(FRONT,f'Grille continuous rail {i+1}',5,y0,747,y1,.017,1.4)
    # Three framed relief fields around the existing eagle and small ornaments.
    for i,(y0,y1) in enumerate([(378,443),(447,565),(570,646)]):
        rect(FRONT,f'Central ornament frame {i+1}',635,y0,742,y1,.014,1.8)
        rect(FRONT,f'Central ornament inset {i+1}',643,y0+8,734,y1-8,-.027,1.7)
    # Small apertures traced from the source artwork, not evenly spaced guesses.
    front_key=next(k for k,m in surfaces['materials'].items() if m['name']==FRONT)
    gray=np.asarray(Image.open(OUT/f'textures/review_{front_key}.jpg').convert('L'))
    for seed_y,y0,y1 in [(680,665,703),(725,717,752)]:
        mask=gray[seed_y-3:seed_y+4,:680].mean(0)<50
        runs=np.flatnonzero(np.diff(np.r_[False,mask,False])).reshape(-1,2)
        for x0,x1 in runs:
            if x1-x0<4 or x0<15:continue
            end_y=735 if seed_y==725 and x0<485 else y1
            points=traced_gap(gray,int(x0),int(x1),y0,end_y,seed_y)
            if points is not None:add(FRONT,f'Grille opening row {seed_y} seed {x0}',points,-.018,.65,'Seeded dark-opening edge trace; individually reviewed overlay')
    # The repeat behind the bartender uses only the atlas's lower-right pair.
    for i,dx in enumerate((0,191)):
        add(BACK,f'Back bar raised octagonal frame {i+1}',[(409+dx,396),(430+dx,373),(516+dx,373),(541+dx,396),
            (541+dx,696),(520+dx,719),(431+dx,719),(409+dx,697)],.018,2)
        add(BACK,f'Back bar inset panel {i+1}',[(431+dx,407),(446+dx,394),(506+dx,394),(520+dx,408),
            (520+dx,680),(507+dx,696),(444+dx,696),(431+dx,682)],-.034,2)
    for i,(y0,y1) in enumerate([(412,437),(463,486),(516,540)]):
        rect(BACK,f'Back bar central clasp {i+1}',552,y0,594,y1,.022,1.8)
    dump(build/'features.json',dict(coordinate_size=768,features=features,
        source_groups={'BAR_08':[22,23,26,27]+list(range(30,50)),'Back Bar Illum_00':list(range(8))+[12,13,14,15]},
        scope='Outer counter fascia and back-bar panel frames only; no stools, unrelated walls, floor, roof or tabletop changes.',
        displacement='Continuous source-normal field across the selected curved strips; no flat per-sector displacement.'))
    for mat in (FRONT,BACK):
        key=next(k for k,m in surfaces['materials'].items() if m['name']==mat)
        im=Image.open(OUT/f'textures/review_{key}.jpg').convert('RGB');d=ImageDraw.Draw(im)
        for f in features:
            if f['material']!=mat:continue
            p=[tuple(q) for q in f['points_px']];d.line(p+[p[0]],fill=(50,240,255) if f['depth_world']>0 else (255,170,35),width=1)
        im.save(build/('front_contours.png' if mat==FRONT else 'back_contours.png'))
    print('AUTHORED',len(features),'profiles; two selected material groups')


if __name__=='__main__':main()
