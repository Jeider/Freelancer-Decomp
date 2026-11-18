"""Manually reviewed structural contours, in 512px texture-image coordinates.

This is authored feature selection, not automatic image recognition. The mesh
builder discovers each UV placement and transfers BOTH UV sets automatically.
"""
import math
from rheinland_audit import *
from PIL import Image,ImageDraw

def rect(x0,y0,x1,y1):return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
def rounded(x0,y0,x1,y1,r=5,segments=4):
    pts=[]
    for x,y,t in [(x1-r,y0+r,-90),(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180)]:
        pts.extend([[x+r*math.cos(math.radians(a)),y+r*math.sin(math.radians(a))] for a in np.linspace(t,t+90,segments+1)])
    return pts
def circle(x,y,r,n=80):return [[x+r*math.cos(t),y+r*math.sin(t)] for t in np.linspace(0,2*math.pi,n,endpoint=False)]

def definitions():
    all_features={}
    def valleys(model,prefix,box,axis=0,distance=8):
        # Image measurements inside an explicitly authored louvre/radiator ROI.
        # This locates repeated painted shadow gaps, not arbitrary global edges.
        from scipy.ndimage import gaussian_filter1d
        from scipy.signal import find_peaks
        data=json.loads((BATCH/model/'source_scene.json').read_text())
        m=next(m for m in data['materials'].values() if m['name'].lower().startswith(prefix))
        im=np.asarray(Image.open(m['textures']['Dt_name']['path']).convert('L').resize((512,512)),float)/255
        x0,y0,x1,y1=box;roi=im[y0:y1,x0:x1]
        line=gaussian_filter1d(roi.mean(axis=1 if axis==0 else 0),.7)
        peaks,_=find_peaks(-line,distance=distance,prominence=max(.004,float(np.ptp(line))*.07))
        return [int(p)+(y0 if axis==0 else x0) for p in peaks if 3<p<len(line)-3]
    def select(model,prefix):
        data=json.loads((BATCH/model/'source_scene.json').read_text())
        m=next(m for m in data['materials'].values() if m['name'].lower().startswith(prefix))
        target=all_features.setdefault(model,{}).setdefault(m['name'],dict(texture_sha256=m['textures']['Dt_name']['sha256'],features=[]))
        def add(label,poly,depth=-.008,inset=.94):
            p=np.asarray(poly,float)/512
            if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<0:p=p[::-1]
            target['features'].append(dict(label=label,uv=p.tolist(),depth_uv=depth,inset=inset))
        return add
    a=select('rh_battleship_bar','rhsh_b_05')
    for box in [(15,19,130,238),(171,18,240,236),(279,18,434,237)]:a('Upper wall panel field',rounded(*box,6),-.009)
    for box in [(18,274,127,479),(281,274,432,479)]:a('Lower wall panel field',rounded(*box,6),-.009)
    a=select('rh_battleship_bar','rhsh_b_12')
    a('Round ventilation recess',circle(182,316,39),-.014,.9)
    for y in [52,104,144,195,247,291,343,397,455]:a('Side cabinet folded edge',rect(378,y,480,y+3),.003,.8)
    a=select('rh_battleship_bar','rhsh_b_01')
    a('Long recessed socket',rounded(325,198,471,230,8),-.014,.9)
    a('Ventilation mouth',circle(192,247,27),-.012,.9)

    a=select('rh_berlin_bar','rhinebar#3-24')
    # Only the large grille's clearly vertical ribs; the surrounding segmented
    # circular frame is already geometry in this model and stays untouched.
    for x,y0,y1 in [(175,143,389),(205,129,403),(236,126,410),(270,126,407),(302,134,398),(335,147,383)]:
        a('Grille vertical rib',rounded(x,y0,x+9,y1,3),.010,.78)
    a=select('rh_berlin_bar','rhinebar#3-23')
    for box in [(28,241,87,390),(121,242,180,390),(28,190,87,224),(121,190,180,224),(28,413,87,445),(121,413,180,445)]:a('Cabinet inset field',rounded(*box,5),-.010,.92)
    for box in [(29,26,86,56),(124,26,183,56)]:a('Cabinet top vent recess',rect(*box),-.012,.9)
    a('Side service door',rect(218,206,309,343),-.008,.96)
    a=select('rh_berlin_bar','rhinebar#3-22')
    a('Grille frame inner opening',rect(83,96,425,406),-.012,.98)

    a=select('rh_bremen_station_bar','rhin_10')
    for cx in [51,241]:a('Round louvre recess',circle(cx,173,20),-.008,.9)
    a=select('rh_bremen_station_bar','rhin_05')
    for y0,y1,x0,x1 in [(92,141,168,183),(151,198,186,203),(208,254,205,224),(265,315,227,247),(326,373,250,271),(385,438,274,296)]:
        a('Trapezoid wall inset',[[57,y0],[x0,y0],[x1,y1],[57,y1]],-.009,.95)
    a=select('rh_bremen_station_bar','rhin_03')
    for cx in [37,96,155,212,269,328,382]:
        for cy in ([64] if cx in [155,269] else [64,177,289]):
            a('Triangular truss opening',[[cx-15,cy-25],[cx+12,cy],[cx-15,cy+25]],-.010,.88)
    a=select('rh_bremen_station_bar','rhin_11')
    for cx in [40,224,359]:a('Adjacent round louvre recess',circle(cx,168,20),-.008,.9)

    a=select('rh_stuttgart_bar','rh_b#2_26')
    for x0,x1 in [(34,117),(151,235),(269,352),(386,472)]:
        for y0,y1 in [(34,109),(160,234),(280,352),(403,475)]:a('Square wall pocket',rect(x0,y0,x1,y1),-.016,.92)
    a=select('rh_stuttgart_bar','rh_b#2_02')
    for box in [(108,29,299,204),(156,260,313,432)]:a('Machinery panel recess',rounded(*box,12),-.010,.95)
    a=select('rh_stuttgart_bar','rh_b#2_30')
    a('Round duct mouth',circle(411,75,45),-.018,.92)
    a('Long upper duct',rounded(36,57,223,97,18),-.014,.9)
    for x in [224,375]:a('Lower sheet seam',rect(x,183,x+3,483),-.003,.65)
    a=select('rh_stuttgart_bar','rh_b#2_03')
    a('Wide upper machined slot',rounded(109,29,309,81,10),-.012,.94)
    for x0,x1 in [(42,68),(339,356),(388,406),(438,463)]:a('Upper vertical socket',rounded(x0,33,x1,79,6),-.010,.86)
    a=select('rh_stuttgart_bar','rh_b#2_18')
    for x in [39,59,79,115,136,155]:a('Cooling aperture',rect(x,14,x+6,80),-.005,.8)
    for cx,cy,r in [(266,394,30),(371,396,32)]:a('Lower circular port',circle(cx,cy,r),-.014,.9)

    a=select('rh_bizmark_equip','rh_eq_18')
    a('Large recessed service panel',rect(119,70,387,432),-.012,.97)
    a=select('rh_bizmark_equip','rh_eq_06')
    for box in [(48,328,138,485),(379,327,473,484)]:a('Mesh grille opening',rect(*box),-.010,.95)
    for y in valleys('rh_bizmark_equip','rh_eq_06',(202,321,304,491),distance=10):a('Horizontal louvre shadow gap',rounded(180,y-2,326,y+2,1),-.004,.8)
    a=select('rh_bizmark_equip','rh_eq_07')
    for box in [(238,39,282,228),(238,281,282,479),(322,55,476,134),(321,389,476,465)]:a('Ventilation mesh recess',rect(*box),-.009,.95)
    for x in valleys('rh_bizmark_equip','rh_eq_07',(315,201,487,306),axis=1,distance=10):a('Radiator valley',rounded(x-2,184,x+2,323,1),-.004,.8)
    a=select('rh_bizmark_equip','rh_eq_23')
    for cx,cy,r in [(402,80,31),(309,433,28)]:a('Circular louvre mouth',circle(cx,cy,r),-.012,.9)
    a=select('rh_bizmark_equip','rh_eq_24')
    for cx in [113,377]:a('Door round service socket',circle(cx,375,19),-.010,.9)

    a=select('rh_berlin_equip','rhine_equip_#3-07')
    for x0,x1 in [(0,74),(169,250),(334,421)]:
        a('Lower cabinet face',rounded(x0+5,376,x1-5,457,6),-.007,.95)
        a('Cabinet lower service recess',rounded(x0+8,460,x1-8,479,5),-.007,.88)
    a=select('rh_berlin_equip','rhine_equip_#3-08')
    a('Upper circular grille mouth',circle(88,80,51),-.012,.93)
    for x in [29,454]:
        for dx in [0,11,22]:a('Three-slot vent',rounded(x+dx,349,x+dx+6,375,2),-.005,.78)
    a=select('rh_berlin_equip','rhine_equip_#3-18')
    a('Central diamond mesh inset',rect(155,180,361,356),-.012,.97)
    for x in [46,163,279,397]:
        for y in [63,395]:a('Studded plate field',rounded(x,y,x+85,y+81,7),.005,.97)
    a=select('rh_berlin_equip','rhine_equip_#3-14')
    for y in valleys('rh_berlin_equip','rhine_equip_#3-14',(224,218,282,268),distance=6):a('Arch support ventilation groove',rect(221,y-1,299,y+1),-.004,.75)
    a=select('rh_berlin_equip','rhine_equip_#3-03')
    a('Service field above display',rounded(91,278,423,332,8),-.008,.96)

    a=select('rh_stuttgart_equip','rh_eq2_17')
    for box in [(26,288,77,421),(101,288,152,421),(346,288,401,421),(428,288,478,421)]:
        a('Side louvre cavity',rect(*box),-.010,.94)
    for y in valleys('rh_stuttgart_equip','rh_eq2_17',(206,286,302,427),distance=10):a('Central louvre gap',rounded(187,y-2,314,y+2,1),-.004,.8)
    for box in [(219,161,281,207),(173,231,334,274)]:a('Upper service inset',rect(*box),-.007,.92)
    a=select('rh_stuttgart_equip','rh_eq2_01')
    for x in [22,124,225,328,431]:a('Lower framed display recess',rect(x,444,x+57,470),-.008,.9)
    for x in [65,285]:
        for y in [94,245]:a('Small machined vent',rounded(x,y,x+40,y+16,4),-.007,.86)
    a=select('rh_stuttgart_equip','rh_eq2_23')
    for x in [177,247,317]:
        a('Tall service plate',rect(x,91,x+47,256),-.008,.96)
        a('Small top vent',rect(x+3,42,x+45,78),-.008,.9)
    for x in valleys('rh_stuttgart_equip','rh_eq2_23',(401,28,494,140),axis=1,distance=10):a('Long radiator shadow valley',rect(x-2,18,x+2,149),-.004,.8)
    a=select('rh_stuttgart_equip','rh_eq2_02')
    for box in [(93,220,132,363),(350,220,389,363)]:a('Door side cavity',rect(*box),-.012,.94)
    a=select('rh_stuttgart_equip','rh_eq2_06')
    for x0,x1 in [(131,172),(193,234)]:
        a('Companion tall service field',rect(x0,93,x1,257),-.008,.96)
        a('Companion upper vent',rect(x0,43,x1,77),-.008,.9)
    a('Lower grille well',rect(399,299,472,372),-.010,.94)
    a=select('rh_stuttgart_equip','rh_eq2_05')
    for cx,cy,r in [(373,79,29),(324,434,27)]:a('Round equipment vent',circle(cx,cy,r),-.012,.9)
    return all_features

def main():
    from PIL import ImageOps
    defs=definitions();dump(BATCH/'authored_features.json',defs)
    for model,materials in defs.items():
        data=json.loads((BATCH/model/'source_scene.json').read_text());rows=[]
        for name,definition in materials.items():
            m=next(m for m in data['materials'].values() if m['name']==name)
            im=Image.open(m['textures']['Dt_name']['path']).convert('RGB').resize((512,512))
            im=ImageOps.autocontrast(im,cutoff=1).point([int(255*(v/255)**.65) for v in range(256)]*3)
            draw=ImageDraw.Draw(im)
            for f in definition['features']:
                p=[tuple(v*512 for v in uv) for uv in f['uv']];draw.line(p+[p[0]],fill=(255,165,15),width=2)
            rows.append((name,im))
        sheet=Image.new('RGB',(1536,544*((len(rows)+2)//3)),(25,28,33));draw=ImageDraw.Draw(sheet)
        for i,(name,im) in enumerate(rows):
            x=i%3*512;y=i//3*544;sheet.paste(im,(x,y));draw.text((x+4,y+519),name,fill='white')
        sheet.save(BATCH/model/'contour_review.jpg')
    print('Authored feature overlays written for',len(defs),'models.')
if __name__=='__main__':main()
