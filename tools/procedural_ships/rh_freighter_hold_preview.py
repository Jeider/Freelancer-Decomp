"""Matched, culled views of the exported narrow-hold assets."""
import json,sys
import numpy as np
from PIL import Image,ImageDraw
import rh_freighter_hold as h
from rh_freighter_final_preview import view
from preview import render
d=h.d;f=d.f;OUT=h.OUT

def culled(gs,mats,cam,center,radius,size):
    front=[]
    for g in gs:
        t=np.array(g['corners']);n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]);mask=n@np.array(cam)>1e-9
        if mask.any():front.append(dict(g,corners=t[mask]))
    return render(front,mats,np.array(center),radius,cam,size,'texture')

def main():
    mats=f.audit.material_table([d.MAT,d.ENV,d.ASSETS/'rh_pir_freighter_lods.mat'])
    _,old=d.tree(h.SOURCE);_,new=d.tree(OUT/'rh_pir_freighter.cmp')
    sheet=Image.new('RGB',(1600,1600),'#18202a');draw=ImageDraw.Draw(sheet)
    for row,(ns,folder,label) in enumerate([(old,d.ASSETS,'BEFORE'),(new,OUT,'DEEP CAVITY')]):
        world=d.world(ns,('Sc_extend wing',0));damaged={}
        for zone in ('port_side_panel','starboard_side_panel'):
            _,dn=d.tree(folder/('rh_pir_freighter_dmg_'+zone+'.3db'));gs=d.simple_geometry(dn)
            anchor=d.hardpoints(ns,('Sc_extend wing',0))['dprpf_'+zone]['position']
            for g in gs:g['corners'][...,:3]+=anchor
            damaged[zone]=gs
        removed={'rh_port_side_lod1','rh_star_side_lod1'}|{n for n in world if '_btn_' in n}
        gs=[g for n,v in world.items() if n not in removed for g in v]+[g for v in damaged.values() for g in v]
        for col,cam in enumerate([(-1,.55,1),(-1,-.45,.4),(1,.6,1),(1,0,.05)]):
            x=(col%2)*800;y=row*800+(col//2)*400
            sheet.paste(culled(gs,mats,cam,(0,1.3,3.7),8.2,800).resize((800,800)).crop((0,200,800,600)),(x,y))
            draw.text((x+12,y+12),label+' / '+['PORT ABOVE','PORT BELOW','STARBOARD ABOVE','STARBOARD SIDE'][col],fill='white')
    sheet.save(OUT/'damage_comparison.png')
    sheet=Image.new('RGB',(1800,600),'#18202a');draw=ImageDraw.Draw(sheet)
    for col,(pose,hidden,label) in enumerate([(('Sc_rh_freighter',1),False,'CARGO OPEN'),(('Sc_rh_freighter',1),True,'ROOF HIDDEN'),(('Sc_extend wing',0),False,'FLIGHT')]):
        w=d.world(new,pose);gs=[g for n,v in w.items() if not(hidden and n=='Baydoor_lod1') for g in v]
        sheet.paste(view(gs,mats,(1,1.4,.6) if col<2 else (1,.7,-1),600),(col*600,0));draw.text((col*600+12,12),label,fill='white')
    sheet.save(OUT/'hold_and_intact.png')
    # Matched before/after whole exterior to reveal accidental UV/silhouette damage.
    sheet=Image.new('RGB',(1400,1400),'#18202a');draw=ImageDraw.Draw(sheet)
    for col,(ns,label) in enumerate([(old,'BEFORE'),(new,'AFTER')]):
        gs=[g for v in d.world(ns,('Sc_extend wing',0)).values() for g in v]
        for row,cam in enumerate([(1,.6,-1),(-1,.7,1)]):
            sheet.paste(view(gs,mats,cam,700),(col*700,row*700));draw.text((col*700+12,row*700+12),label,fill='white')
    sheet.save(OUT/'exterior_comparison.png')
    print('MATCHED EXPORTED PREVIEWS READY',flush=True)

def lights():
    mats=f.audit.material_table([d.MAT,d.ENV]);_,ns=d.tree(OUT/'rh_pir_freighter.cmp')
    gs=[g for v in d.world(ns,('Sc_extend wing',0)).values() for g in v];p=d.points(gs)
    center=(p.min(0)+p.max(0))/2;radius=np.linalg.norm(p-center,axis=1).max()*1.03
    hp=json.loads((OUT/'geometry.json').read_text())['lights']
    sheet=Image.new('RGB',(1800,600),'#18202a');draw=ImageDraw.Draw(sheet)
    for col,cam in enumerate([(1,.7,-1),(-1,.65,1),(1,-.7,-.7)]):
        sheet.paste(culled(gs,mats,cam,center,radius,600),(600*col,0))
        forward=np.array(cam,float);forward/=np.linalg.norm(forward);right=np.cross([0,1,0],forward);right/=np.linalg.norm(right);up=np.cross(forward,right)
        for k,v in hp.items():
            co=np.array(v['after'])-center;x=col*600+300+co@right*600*.46/radius;y=300-co@up*600*.46/radius
            color='#60f6aa' if 'running' in k else '#ffc26b'
            draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
            draw.text((x+5,y-9),v['name'].replace('HpRunningLight','R').replace('HpDocklight','D').replace('HpHeadlight','Head'),fill=color)
    sheet.save(OUT/'lights.png')
    d.dump(OUT/'preview_manifest.json',dict(cmp_sha256=f.digest(OUT/'rh_pir_freighter.cmp'),
        images={p.name:f.digest(p) for p in OUT.glob('*.png')},renderer='Offline software, back-face culled',
        note='Geometry comparison rendered before final docklight placement; final mesh geometry identical. lights.png uses final light positions.'))

if __name__=='__main__' and '--lights' in sys.argv:lights()

if __name__=='__main__' and '--lights' not in sys.argv:main()
