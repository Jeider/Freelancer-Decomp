"""Back-face-culled software inspection of actual decoded ship assets."""
import argparse
import numpy as np
from PIL import Image,ImageDraw
import rh_freighter_final as d
from preview import render

def view(gs,mats,camera,size=650):
    p=d.points(gs);center=(p.min(0)+p.max(0))/2;radius=np.linalg.norm(p-center,axis=1).max()*1.03
    direction=np.array(camera,float);front=[]
    for g in gs:
        t=np.array(g['corners']);n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]);mask=n@direction>1e-9
        if mask.any():front.append(dict(g,corners=t[mask]))
    return render(front,mats,center,radius,camera,size=size,mode='texture')

def reference():
    mats=d.f.audit.material_table([d.MAT,d.ENV]);entries=d.read('native_damage_reference.json')
    sheet=Image.new('RGB',(1800,1260),'#18202a');draw=ImageDraw.Draw(sheet)
    for row,e in enumerate(entries):
        gs=d.packed(e['groups']);side=-1 if e['zone'].startswith('port') else 1
        for col,cam in enumerate([(side,.4,1),(side,-.5,1),(side,0,.05)]):
            im=view(gs,mats,cam,300);sheet.paste(im,(col*600,row*315));draw.text((col*600+310,row*315+20),e['zone']+'\n'+str(e['materials']),fill='white')
    dest=d.OUT/'previews';dest.mkdir(exist_ok=True);sheet.save(dest/'native_damage_reference.png')
    _,ns=d.tree(d.OUT/'authoring_animated.cmp')
    for part,gs in d.world(ns,('Sc_extend wing',0)).items():
        print(part,sum(len(g['corners']) for g in gs),d.points(gs).min(0).round(2),d.points(gs).max(0).round(2))

def damaged():
    mats=d.f.audit.material_table([d.MAT,d.ENV]);entries=d.read('damage_world.json')
    dest=d.OUT/'previews';dest.mkdir(exist_ok=True)
    sheet=Image.new('RGB',(1600,1600),'#18202a');draw=ImageDraw.Draw(sheet)
    for row,(name,gs) in enumerate(entries.items()):
        side=-1 if name.startswith('port') else 1
        for col,cam in enumerate([(side,.7,1.2),(side,-.6,1.1),(side,.1,.05),(side*.2,.6,1.6)]):
            sheet.paste(view(d.packed(gs),mats,cam,400),(col*400,row*400));draw.text((col*400+12,row*400+12),name,fill='white')
    sheet.save(dest/'damage_parts.png')
    _,ns=d.tree(d.OUT/'authoring_animated.cmp');w=d.world(ns,('Sc_extend wing',0));removed=set(d.PARTS.values())|{n for n in w if '_btn_' in n}
    gs=[g for name,groups in w.items() if name not in removed for g in groups]+[g for groups in entries.values() for g in d.packed(groups)]
    for label,cam in [('damage_ship_above',(-1,.7,1)),('damage_ship_below',(1,-.7,1))]:view(gs,mats,cam,1200).save(dest/(label+'.png'))

def final():
    mats=d.f.audit.material_table([d.MAT,d.ENV,d.ASSETS/'rh_pir_freighter_lods.mat']);_,ns=d.tree(d.ASSETS/'rh_pir_freighter.cmp')
    dest=d.OUT/'previews';sheet=Image.new('RGB',(1800,1200),'#18202a');draw=ImageDraw.Draw(sheet)
    for lv in range(3):
        gs=[g for groups in d.world(ns,('Sc_extend wing',0),lv).values() for g in groups]
        for row,cam in enumerate([(1,.65,-1),(1,-.7,1)]):
            im=view(gs,mats,cam,600);sheet.paste(im,(lv*600,row*600));draw.text((lv*600+15,row*600+12),'LOD '+str(lv),fill='white')
    sheet.save(dest/'lod_comparison.png')
    wire=d.read('wire.json')['parts'];sheet=Image.new('RGB',(1500,600),'#18202a');draw=ImageDraw.Draw(sheet)
    colors={'Root':'#b9d5dd','port_engine_lod1':'#ffb567','starboard_engine_lod1':'#ffb567','rh_port_side_lod1':'#73d899','rh_star_side_lod1':'#73d899'}
    allp=np.concatenate([np.array(g['world']).reshape(-1,3) for g in wire.values() if g['edges']]);center=(allp.min(0)+allp.max(0))/2
    for col,cam in enumerate([(1,0,0),(.01,1,0),(1,.65,-1)]):
        forward=np.array(cam,float);forward/=np.linalg.norm(forward);right=np.cross([0,1,0],forward);right/=np.linalg.norm(right);up=np.cross(forward,right)
        for part,g in wire.items():
            if not g['edges']:continue
            p=np.array(g['world'])-center;xy=np.stack((p@right,-p@up),axis=-1)*18+[col*500+250,300]
            for a,b in xy:draw.line([tuple(a),tuple(b)],fill=colors.get(part,'white'),width=1)
        draw.text((col*500+15,15),['SIDE','TOP / EXTENDED','PERSPECTIVE'][col],fill='white')
    sheet.save(dest/'wire_review.png')

if __name__=='__main__':
    import sys
    final() if '--final' in sys.argv else damaged() if '--damage' in sys.argv else reference()
