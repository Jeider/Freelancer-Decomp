"""Offline pose strips for representative source mechanisms, using decoded native keys."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import full_ship_audit as a

CASES=[
 ('rheinland/rh_elite/rh_elite.cmp','sc_extend wing'),
 ('rheinland/rh_elite/rh_alt_elite.cmp','sc_extend wing'),
 ('rheinland/rh_pir_elite/rh_pir_elite.cmp','sc_open baydoor'),
 ('liberty/li_elite/li_elite.cmp','sc_extend wing'),
 ('order/or_elite/or_elite.cmp','sc_extend wing'),
 ('bretonia/br_elite/br_elite.cmp','sc_extend wing'),
 ('kusari/ku_elite/ku_elite.cmp','sc_extend wing'),
 ('kusari/ku_fighter/ku_fighter.cmp','sc_extend wing'),
 ('kusari/ku_freighter/ku_freighter.cmp','sc_extend wing'),
 ('border_world/bw_vheavy_fighter/bw_vheavy_fighter.cmp','sc_extend wing'),
 ('bounty_hunter/bh_vheavy_fighter/bh_vheavy_fighter.cmp','sc_extend wing'),
 ('civilian/cv_starflier/cv_starflier.cmp','sc_extend wing'),
 ('corsair/co_elite/co_elite.cmp','sc_extend wing'),
 ('utility/mining/mining_with_panels.cmp','sc_loop'),
 ('utility/repair/repair_beta.cmp','sc_weld')]

def scene_at(r,scene,time,script):
    old=a.matrices(r['constructs']);values={}
    for ch in r['channels']:
        if ch['script']!=script or not ch['native_size_valid'] or not ch['bound_joint'] or ch.get('parent_mismatch'):continue
        ar=np.array(ch['values'])
        values[ch['child'].lower()]=[np.interp(time,ch['times'],ar[:,i]) for i in range(ar.shape[1])]
    new=a.matrices(r['constructs'],values)
    _,nodes=a.m.read_tree((a.DATA/r['path']).read_bytes())
    flat={p.lower():n.blob for p,n in a.m.walk(nodes)};names={}
    for p,b in flat.items():
        if '/cmpnd/' in p and p.endswith('/file name'):names[a.m.string(b).lower()]=a.m.string(flat[p.rsplit('/',1)[0]+'/object name']).lower()
    out=[]
    for g in scene:
        name=names.get(g['part'],'root');ro,to=old.get(name,(np.eye(3),np.zeros(3)));rn,tn=new.get(name,(np.eye(3),np.zeros(3)))
        c=g['corners'].copy();c[...,:3]=((c[...,:3]-to)@ro)@rn.T+tn;c[...,3:6]=(c[...,3:6]@ro)@rn.T
        out.append(dict(g,corners=c))
    return out

def main():
    config=a.configuration();materials=a.material_index(config)
    out=a.OUT/'motion';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',17);links=[]
    for rel,script in CASES:
        r,rest=a.read_model(a.DATA/'ships'/rel,config,materials)
        tracks=[c for c in r['channels'] if c['script']==script];assert tracks,(rel,script)
        duration=max(c['duration'] for c in tracks);frames=[scene_at(r,rest,duration*p,script) for p in (0,1/3,2/3,1)]
        pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for s in frames for g in s]);center=(pts.min(0)+pts.max(0))/2
        radius=np.linalg.norm(pts-center,axis=1).max()
        mats={g['material']:dict(image=None,colour=np.ones(3),name='clay') for g in rest}
        sheet=Image.new('RGB',(1440,780),(24,29,37));d=ImageDraw.Draw(sheet)
        for row,cam in enumerate(((1,.65,-1.3),(.01,1.,.005))):
            for col,s in enumerate(frames):
                d.text((col*360+6,row*390+6),f'{Path(rel).stem}  t={duration*col/3:.2f}',font=font,fill='white')
                sheet.paste(a.a.render(s,mats,center,radius,cam,360,'clay'),(col*360,row*390+30))
        name=r['key']+'_'+script.replace(' ','_')+'.jpg';sheet.save(out/name,quality=92)
        links.append(f'## {rel} / {script}\n\n![Фазы и вид сверху]({name})\n')
        print(rel,script,flush=True)
    (out/'README.md').write_text('# Разбор движения на исходной геометрии\n\nЧетыре фазы, общая камера и масштаб внутри каждого листа. Это офлайн-реконструкция по ключам, не запись игры. Привязки с неверным размером или родителем исключены. Между quaternion-ключами применяется нормализованная линейная интерполяция, а не побитовое воспроизведение движка.\n\n'+'\n'.join(links),encoding='utf8')

if __name__=='__main__':main()
