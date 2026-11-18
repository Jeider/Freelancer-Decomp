"""Culled close-ups from the exported CMP, before and after the surround repair."""
import json
import numpy as np
from PIL import Image,ImageDraw
import rh_freighter_hold_repair as h
from rh_freighter_hold_preview import culled
from rh_freighter_final_preview import view
d=h.d;f=d.f;OUT=h.OUT

def main():
    mats=f.audit.material_table([d.MAT,d.ENV])
    _,old=d.tree(OUT/'user_source.cmp');_,new=d.tree(OUT/'rh_pir_freighter.cmp')
    sheet=Image.new('RGB',(1800,1800),'#18202a');draw=ImageDraw.Draw(sheet)
    for col,(ns,label) in enumerate([(old,'BEFORE'),(new,'AFTER')]):
        w=d.world(ns,('Sc_rh_freighter',1))
        for row,cam in enumerate([(0,1,.001),(1,1.8,.5)]):
            gs=[g for n,v in w.items() if n!='Baydoor_lod1' for g in v]
            pic=culled(gs,mats,cam,(0,2,.9),5.7,900)
            sheet.paste(pic,(col*900,row*900));draw.text((col*900+15,row*900+15),label+' / ROOF HIDDEN',fill='white')
    sheet.save(OUT/'cargo_comparison.png')
    sheet=Image.new('RGB',(1800,1200),'#18202a');draw=ImageDraw.Draw(sheet)
    for i,(pose,cam,label) in enumerate([
        (('Sc_rh_freighter',1),(1,1.7,.5),'OPEN CARGO'),
        (('Sc_rh_freighter',1),(-1,1.7,-.5),'OPEN REVERSE'),
        (('Sc_extend wing',0),(1,.7,-1),'FLIGHT'),
        (('Sc_extend wing',0),(-1,-.6,1),'BELLY'),
        (None,(1,.4,-1),'FOLDED'),
        (('Sc_extend wing',0),(1,0,0),'SIDE')]):
        gs=[g for v in d.world(new,pose).values() for g in v]
        x=(i%3)*600;y=(i//3)*600
        sheet.paste(view(gs,mats,cam,600),(x,y));draw.text((x+10,y+10),label,fill='white')
    sheet.save(OUT/'complete_assembly.png')
    sheet=Image.new('RGB',(1500,1000),'#18202a');draw=ImageDraw.Draw(sheet)
    for lv in range(3):
        w=d.world(new,('Sc_extend wing',0),lv);gs=[g for v in w.values() for g in v]
        sheet.paste(view(gs,mats,(1,.7,-1),500),(lv*500,0));draw.text((lv*500+10,10),'LOD '+str(lv),fill='white')
        w=d.world(new,('Sc_rh_freighter',1),lv);gs=[g for n,v in w.items() if n!='Baydoor_lod1' for g in v]
        sheet.paste(culled(gs,mats,(0,1,.001),(0,2,.9),6,500),(lv*500,500))
    sheet.save(OUT/'lod_check.png')
    w=d.world(new,('Sc_extend wing',0));damage=[]
    for zone in ('port_side_panel','starboard_side_panel'):
        _,dn=d.tree(h.CANON/('rh_pir_freighter_dmg_'+zone+'.3db'));gs=d.simple_geometry(dn)
        anchor=d.hardpoints(new,('Sc_extend wing',0))['dprpf_'+zone]['position']
        for g in gs:g['corners'][...,:3]+=anchor
        damage+=gs
    removed={'rh_port_side_lod1','rh_star_side_lod1'}|{n for n in w if '_btn_' in n}
    gs=[g for n,v in w.items() if n not in removed for g in v]+damage
    sheet=Image.new('RGB',(1600,800),'#18202a')
    for i,cam in enumerate([(-1,.6,.5),(1,.6,-.5)]):
        sheet.paste(culled(gs,mats,cam,(0,1.3,2),8.2,800),(i*800,0))
    sheet.save(OUT/'damage_check.png')
    world=d.world(new,('Sc_extend wing',0));sheet=Image.new('RGB',(1800,1200),'#18202a');draw=ImageDraw.Draw(sheet)
    if (OUT/'seams_before.png').exists():sheet.paste(Image.open(OUT/'seams_before.png'),(0,0))
    for i,(cam,center,radius,hidden) in enumerate([
        ((0,1,-.6),(0,3.8,-3.7),3.6,False),((0,1,.6),(0,3.8,5.5),3.6,False),((-1,1,.4),(1.05,3.5,.8),1.5,True)]):
        gs=[g for n,v in world.items() if not(hidden and n=='Baydoor_lod1') for g in v]
        sheet.paste(culled(gs,mats,cam,center,radius,600),(i*600,600));draw.text((i*600+10,610),'AFTER',fill='white')
    sheet.save(OUT/'seams_comparison.png')
    fpath=OUT/'preview_manifest.json'
    d.dump(fpath,dict(cmp_sha256=f.digest(OUT/'rh_pir_freighter.cmp'),renderer='Offline, back-face culled',
         images={p.name:f.digest(p) for p in OUT.glob('*.png')}))
    print('EXPORTED CMP PREVIEWS READY',flush=True)

if __name__=='__main__':main()
