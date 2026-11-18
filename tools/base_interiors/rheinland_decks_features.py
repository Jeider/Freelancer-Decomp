"""Authored wall contours for the Rheinland depot and battleship deck."""
from rheinland_features import rect,rounded as rounded_base,circle
from rheinland_audit import *
from PIL import Image,ImageDraw,ImageOps
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

DECKS=['rh_depot_deck','rh_battleship_deck']

def rounded(x0,y0,x1,y1,r=5):
    return rounded_base(x0,y0,x1,y1,r,segments=12)

def definitions():
    result={}
    def select(model,needle):
        data=json.loads((BATCH/model/'source_scene.json').read_text())
        m=next(m for m in data['materials'].values() if needle.lower() in m['name'].lower())
        definition=dict(texture_sha256=m['textures']['Dt_name']['sha256'],features=[])
        result.setdefault(model,{})[m['name']]=definition
        lum=np.asarray(Image.open(m['textures']['Dt_name']['path']).convert('L').resize((512,512)),float)/255
        def add(label,p,depth=-.008,inset=.93):
            p=np.asarray(p,float)/512
            if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<0:p=p[::-1]
            definition['features'].append(dict(label=label,uv=p.tolist(),depth_uv=depth,inset=inset))
        def grooves(label,box,axis=0,distance=10,half=1.4):
            x0,y0,x1,y1=box;roi=lum[y0:y1,x0:x1]
            line=gaussian_filter1d(roi.mean(axis=1 if axis==0 else 0),.7)
            indices,_=find_peaks(-line,distance=distance,prominence=max(.0003,float(np.ptp(line))*.035))
            for q in indices:
                if not 3<q<len(line)-3:continue
                k=q+(y0 if axis==0 else x0)
                poly=rect(x0,k-half,x1,k+half) if axis==0 else rect(k-half,y0,k+half,y1)
                add(label,poly,-.0035,.72)
        return add,grooves
    depot='rh_depot_deck'
    a,g=select(depot,'room-15.')
    a('Tall service opening',rounded(183,167,219,277,3),-.012,.88)
    g('Right cooling louvre gap',(419,286,489,350),distance=10)
    g('Adjacent cooling louvre gap',(313,315,380,358),distance=9)
    a,g=select(depot,'room-23.')
    for x in [84,109,134,159,184,209]:a('Upper vertical machined slot',rounded(x,88,x+8,150,3),-.006,.8)
    a,g=select(depot,'room-04.')
    for box in [(19,46,160,57),(19,121,158,132)]:a('Service panel folded edge',rect(*box),.003,.8)
    a,g=select(depot,'room-14.')
    for box in [(291,368,417,441),(291,447,417,489)]:a('Paired mesh grille well',rect(*box),-.010,.95)
    a,g=select(depot,'room-03.')
    # Clear triangular openings between the repeating diagonal truss braces.
    for i,x in enumerate([10,80,148,218,288,357,427]):
        if i%2==0:
            pockets=[[[x+3,14],[x+41,14],[x+3,48]],[[x+14,57],[x+50,23],[x+50,57]]]
        else:
            pockets=[[[x+13,14],[x+50,14],[x+50,48]],[[x+3,25],[x+39,57],[x+3,57]]]
        for p in pockets:a('Truss triangular pocket',p,-.008,.9)
    a,g=select(depot,'room-17.')
    g('Small service louvre gap',(114,136,164,175),distance=10,half=2)
    a,g=select(depot,'room-12.')
    a('Upper brace recess',[[322,48],[399,48],[399,119],[322,185]],-.010,.95)
    a('Upper brace lower recess',[[322,211],[400,143],[400,211]],-.010,.94)
    a,g=select(depot,'room-24.')
    for x in [57,178]:a('Circular maintenance cover',circle(x,153,45),.007,.95)

    deck='rh_battleship_deck'
    a,g=select(deck,'rh_shbar_06.')
    for y0,y1 in [(58,110),(189,242),(319,370),(443,491)]:g('Repeated wall radiator valley',(391,y0,487,y1),axis=1,distance=9)
    a,g=select(deck,'rh_shbar_12.')
    for x0,x1 in [(11,60),(71,110),(132,171),(181,223),(259,300),(314,354),(389,433),(446,493)]:a('Upper wall cornice pocket',rect(x0,34,x1,63),-.007,.9)
    a,g=select(deck,'rh_shbar_03.')
    a('Round ventilation mouth',circle(182,315,39),-.012,.9)
    a('Lower vertical service slot',rounded(170,405,191,491,10),-.009,.85)
    a,g=select(deck,'rh_shbar_13.')
    g('Broad lower louvre gap',(234,188,316,438),distance=9,half=2)
    g('Narrow lower louvre gap',(183,188,215,438),distance=9,half=2)
    a,g=select(deck,'rh_shbar_14.')
    a('Horizontal service socket',rounded(224,247,274,269,10),-.010,.84)
    a,g=select(deck,'rh_shbar_15.')
    a('Companion horizontal service socket',rounded(241,246,291,269,10),-.010,.84)
    a('Tall inset grille',rect(67,78,108,440),-.009,.96)
    a,g=select(deck,'detailmap_rh_shbar_17')
    for box in [(273,62,315,91),(273,226,315,249),(273,267,315,285),(273,422,315,445),(303,101,316,210),(303,297,316,410)]:a('Tall companion grille well',rect(*box),-.008,.94)
    a,g=select(deck,'rh_shbar_01.')
    a('Broad diamond grille well',rect(140,218,430,286),-.010,.96)
    return result

def main():
    defs=definitions();path=BATCH/'authored_features.json';all_=json.loads(path.read_text());all_.update(defs);dump(path,all_)
    for model,materials in defs.items():
        data=json.loads((BATCH/model/'source_scene.json').read_text());sheet=Image.new('RGB',(1536,544*((len(materials)+2)//3)),(20,27,34));draw=ImageDraw.Draw(sheet)
        for i,(name,definition) in enumerate(materials.items()):
            m=next(m for m in data['materials'].values() if m['name']==name)
            im=Image.open(m['textures']['Dt_name']['path']).convert('RGB').resize((512,512))
            im=ImageOps.autocontrast(im,cutoff=1).point([int(255*(v/255)**.65) for v in range(256)]*3);dr=ImageDraw.Draw(im)
            for f in definition['features']:
                p=[tuple(v*512 for v in uv) for uv in f['uv']];dr.line(p+[p[0]],fill=(255,165,15),width=2)
            x=i%3*512;y=i//3*544;sheet.paste(im,(x,y));draw.text((x+4,y+517),name,fill='white')
        sheet.save(BATCH/model/'contour_review.jpg',quality=95)
    print('Deck contours:',sum(len(m) for m in defs.values()),'materials.')

if __name__=='__main__':main()
