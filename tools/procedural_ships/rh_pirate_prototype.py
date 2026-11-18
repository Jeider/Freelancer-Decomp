"""Separate animated RH pirate silhouette prototype; never installs or launches the game."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct as S
import subprocess
import shutil
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import style_audit as audit
import li_elite as mesh
from preview import export_obj
from rh_redesign_paths import PROTOTYPE_V1

OUT=PROTOTYPE_V1
# This is the live archetype, whose model path changes after an approved install.
# Authentic-original references are recorded separately in the final assembly.
ROW=next(r for r in audit.inventory()[0] if 'rh_elite_pir' in r['aliases'])
SOURCE=audit.DATA/ROW['model']
DEST=OUT/'rh_pir_elite_raider.cmp'


def world(groups,rotation,offset):
    result=copy.deepcopy(groups)
    for g in result:
        g['corners'][...,:3]=g['corners'][...,:3]@rotation.T+offset
        g['corners'][...,3:6]=g['corners'][...,3:6]@rotation.T
    return result


def wedge(outline,bottom,top,material,side=1):
    """Closed beveled armour plate, authored in the ship's rest coordinates."""
    polygon=np.array(outline,float)
    center=polygon.mean(axis=0)
    inset=center+(polygon-center)*.82
    points=np.array([[side*x,bottom,z] for x,z in polygon]+[[side*x,top,z] for x,z in inset])
    n=len(polygon);faces=[]
    for i in range(1,n-1):faces += [(0,i+1,i),(n,n+i,n+i+1)]
    for i in range(n):
        j=(i+1)%n;faces += [(i,j,n+j),(i,n+j,n+i)]
    triangles=[]
    center3=points.mean(axis=0)
    for face in faces:
        p=points[list(face)].copy();normal=np.cross(p[1]-p[0],p[2]-p[0])
        if np.dot(normal,p.mean(axis=0)-center3)<0:p=p[[0,2,1]];normal=-normal
        normal=mesh.unit(normal)
        uv=np.column_stack(((abs(p[:,0])-polygon[:,0].min())/max(np.ptp(polygon[:,0]),.01),
                            (p[:,2]-polygon[:,1].min())/max(np.ptp(polygon[:,1]),.01)))
        # A quiet metal region; reuse the authored atlas rather than bake new textures.
        uv=uv*.3+.15
        triangles.append(np.concatenate((p,np.tile(normal,(3,1)),uv),axis=1))
    return dict(material=material,unused=204,corners=np.array(triangles))


def alter(groups,part,hardpoints,detail):
    result=copy.deepcopy(groups)
    if '_wing_' in part.lower():
        for g in result:
            old=g['corners'].copy();p=old[...,:3];s=np.sign(p[...,0]);x=abs(p[...,0])
            fade=np.clip((x-3.4)/3.9,0,1)
            if len(hardpoints):
                distance=np.linalg.norm(p[...,None,:]-hardpoints,axis=-1).min(axis=-1)
                fade*=np.clip((distance-.72)/.65,0,1)
            # Rearward sweep grows towards the tip. Gun/contrail mounting islands
            # and the hinge root remain fixed in the authored component frame.
            g['corners'][...,2]+=1.45*fade
            g['corners'][...,0]+=s*.30*fade
            before=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
            q=g['corners'][...,:3]
            after=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0])
            sign=np.sign(np.sum(before*old[...,3:6].mean(axis=1),axis=1))
            delta=(mesh.unit(after)-mesh.unit(before))*sign[:,None]
            g['corners'][...,3:6]=mesh.unit(old[...,3:6]+delta[:,None,:])
        if detail:
            side=-1 if 'port_' in part.lower() else 1
            # Short root shield leaves the original gun pad clear outboard.
            result.append(wedge([(3.05,2.2),(3.65,2.15),(4.25,3.65),(3.1,3.4)],-1.98,-1.65,mesh.crc('pir_r_panel02_256'),side))
            # Follow and overlap the actual swept trailing edge. The plate must
            # remain seated in the wing, including when the component rotates.
            result.append(wedge([(3.6,4.0),(7.35,2.99),(7.65,3.20),(3.80,4.62)],-2.10,-1.85,mesh.crc('metal03D'),side))
    elif '_engine_' in part.lower() and detail:
        side=-1 if 'port_' in part.lower() else 1
        # Engine shoulder guards, attached to the existing engine component.
        result.append(wedge([(1.3,2.25),(1.65,1.95),(2.32,2.25),(2.35,4.15),(1.3,4.5)],-1.35,-1.10,mesh.crc('metal03DK'),side))
        result.append(wedge([(1.42,2.45),(1.75,2.25),(2.13,2.45),(2.14,3.72),(1.42,3.95)],-1.09,-1.02,mesh.crc('pir_r_panel02_256'),side))
    for g in result:g.setdefault('unused',204)
    return result


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    source=SOURCE.read_bytes();header,nodes=mesh.read_tree(source)
    original={p:n.blob for p,n in mesh.walk(nodes)}
    transform,_=audit.transforms(nodes)
    library=mesh.child(nodes[0],'VMeshLibrary')
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    changes={};report=[]
    for p,node in list(mesh.walk(nodes)):
        if not p.lower().endswith('/vmeshref'):continue
        part=p.split('/')[2]
        if not any(k in part.lower() for k in ('_wing_','_engine_')):continue
        detail='/level0/' in p.lower()
        if '_engine_' in part.lower() and not detail:continue
        r,t=transform[part.lower()]
        local=audit.extract(node.blob,libs)
        points=np.array([np.frombuffer(n.blob,'<f4') for hp,n in mesh.walk(nodes)
                         if '/'+part+'/' in hp and '/hardpoints/' in hp.lower() and hp.lower().endswith('/position')])
        hp=points@r.T+t if len(points) else np.empty((0,3))
        modified=alter(world(local,r,t),part,hp,detail)
        modified=world(modified,r.T,-r.T@t)
        blob,verts=mesh.pack(modified)
        name='rh_raider_'+hashlib.sha256((p+hashlib.sha256(blob).hexdigest()).encode()).hexdigest()[:16]+'.vms'
        item=mesh.Node(name);item.children=[mesh.Node('VMeshData',blob)];library.children.append(item)
        node.blob=mesh.make_ref(node.blob,name,blob,verts);changes[p]=node.blob
        report.append(dict(part=part,lod=p.split('/')[-3] if '/MultiLevel/' in p else 'direct',
                           triangles_before=sum(len(g['corners']) for g in local),triangles_after=sum(len(g['corners']) for g in modified)))
    output=mesh.write_tree(header,nodes);DEST.write_bytes(output)
    _,decoded=mesh.read_tree(output);after={p:n.blob for p,n in mesh.walk(decoded)}
    assert set(original)<=set(after)
    assert all(after[p]==changes.get(p,blob) for p,blob in original.items())
    protected=[p for p in original if '/hardpoints/' in p.lower() or '/animation/' in p.lower() or '/cmpnd/' in p.lower()]
    assert all(original[p]==after[p] for p in protected)
    # Every original library is retained, so cockpit geometry, glass, all other
    # parts and the HUD wireframe continue referring to identical vertex data.
    dl={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(decoded) if p.lower().endswith('/vmeshdata')}
    for p,n in mesh.walk(decoded):
        if p.lower().endswith('/vmeshref'):
            gs=audit.extract(n.blob,dl)
            assert all(np.isfinite(g['corners']).all() for g in gs)
        if p in changes:
            verts=np.concatenate([g['corners'].reshape(-1,8) for g in gs])
            assert np.allclose(np.linalg.norm(verts[:,3:6],axis=1),1,atol=.002)
    assert hashlib.sha256(SOURCE.read_bytes()).digest()==hashlib.sha256(source).digest()
    data=dict(source=str(SOURCE),prototype=str(DEST),source_sha256=hashlib.sha256(source).hexdigest(),
              output_sha256=hashlib.sha256(output).hexdigest(),modified=report,
              protected_leaves=len(protected),original_libraries_retained=True,
              unchanged=['cockpit and complete root hull','glass','cockpit/pilot hardpoints','all hardpoints',
                         'all animation channels','all constructs','bay doors','round tail','original HUD wire'],
              limitations=['offline prototype, not installed','SUR and damage caps not updated',
                           'HUD wire retains source silhouette','offline pose review is not an in-game collision test'])
    (OUT/'checks.json').write_text(json.dumps(data,indent=2))
    print('PASS source preserved, complete cockpit/root/glass preserved, all constructs/animations/hardpoints byte-identical',flush=True)
    return nodes


def scene(nodes,phase=1):
    # Interpolate the existing two-key scalar wing channel for preview only.
    posed=copy.deepcopy(nodes)
    for p,n in mesh.walk(posed):
        if '/sc_extend wing/' in p.lower() and p.lower().endswith('/channel/frames'):
            frames=np.frombuffer(n.blob,'<f4').reshape(-1,2).copy()
            frames[0,1]=frames[0,1]*(1-phase)+frames[-1,1]*phase
            n.blob=frames.astype('<f4').tobytes()
    trans,_=audit.transforms(posed,('Sc_extend wing',0))
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(posed) if p.lower().endswith('/vmeshdata')}
    out=[]
    for p,n in mesh.walk(posed):
        if not p.lower().endswith('/vmeshref') or ('/multilevel/' in p.lower() and '/level0/' not in p.lower()):continue
        part=p.split('/')[2];r,t=trans[part.lower()]
        for g in world(audit.extract(n.blob,libs),r,t):g['part']=part;out.append(g)
    return out


def previews(nodes,video=False):
    _,base=mesh.read_tree(SOURCE.read_bytes())
    mats=audit.material_table([audit.DATA/p for p in ROW['materials']]+[SOURCE])
    # Sample both endpoints and intermediate poses of the existing wing channel.
    old,new=scene(base),scene(nodes)
    sample=[scene(nodes,float(t)) for t in np.linspace(0,1,25)]
    allpoints=np.concatenate([g['corners'][...,:3].reshape(-1,3) for s in [old]+sample for g in s])
    assert np.isfinite(allpoints).all()
    bounds=(allpoints.min(axis=0),allpoints.max(axis=0))
    center=(bounds[0]+bounds[1])/2
    radius=np.linalg.norm(allpoints-center,axis=1).max()
    def render(sc,cam,size,mode='texture'):
        return audit.render(sc,mats,center,radius,cam,size,mode)
    size=680;font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
    sheet=Image.new('RGB',(size*2,3*(size+35)+65),(24,29,37));d=ImageDraw.Draw(sheet)
    for col,(label,sc) in enumerate((('SOURCE / rh_elite_pir',old),('PROTOTYPE / Raider',new))):
        d.text((col*size+16,10),label,font=font,fill='white')
        for row,cam in enumerate(((1,.85,-1.4),(0,1,.001),(-1,.6,1.4))):
            sheet.paste(render(sc,cam,size),(col*size,45+row*(size+35)))
    d.text((16,sheet.height-30),'Offline mesh preview / same camera, scale, materials / cockpit unchanged',font=font,fill='white')
    sheet.save(OUT/'comparison.jpg',quality=94)
    # First/last frames and clay view make the geometric and mechanical changes inspectable.
    poses=Image.new('RGB',(size*2,size*2+95),(24,29,37));d=ImageDraw.Draw(poses)
    for col,phase in enumerate((0,1)):
        d.text((col*size+16,8),f'PROTOTYPE / wing channel {phase}',font=font,fill='white')
        for row,mode in enumerate(('texture','clay')):
            poses.paste(render(scene(nodes,phase),(1,.65,-1.3),size,mode),(col*size,40+row*(size+20)))
    poses.save(OUT/'poses.jpg',quality=94)
    export_obj(OUT/'rh_raider.obj',new,mats)
    export_obj(OUT/'rh_source.obj',old,mats)
    stats=json.loads((OUT/'checks.json').read_text());stats['triangles_before']=sum(len(g['corners']) for g in old)
    stats['triangles_after']=sum(len(g['corners']) for g in new);stats['sampled_wing_poses']=25
    (OUT/'checks.json').write_text(json.dumps(stats,indent=2))
    if video:
        ffmpeg=shutil.which('ffmpeg')
        if not ffmpeg:
            import imageio_ffmpeg
            ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
        side=420;fps=12;count=72
        proc=subprocess.Popen([ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{side*2}x{side+40}',
            '-r',str(fps),'-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'animation.mp4')],stdin=subprocess.PIPE)
        for frame in range(count):
            phase=(1-math.cos(2*math.pi*frame/(count-1)))/2
            pic=Image.new('RGB',(side*2,side+40),(24,29,37));d=ImageDraw.Draw(pic)
            for col,(ns,label) in enumerate(((base,'SOURCE'),(nodes,'RAIDER / cockpit unchanged'))):
                d.text((col*side+10,5),label,font=font,fill='white')
                pic.paste(render(scene(ns,phase),(1,.7,-1.3),side),(col*side,40))
            proc.stdin.write(pic.tobytes())
            if frame%12==0:print('Animation frame',frame,'/',count,flush=True)
        proc.stdin.close();assert proc.wait()==0
    (OUT/'README.txt').write_text('RH pirate Raider — отдельный геометрический прототип.\n'
        'Сравнение: comparison.jpg; крайние позы и clay: poses.jpg; движение: animation.mp4.\n'
        'rh_pir_elite_raider.cmp использует библиотеки исходного rh_elite_pir.\n'
        'Оригинальная кабина RH, весь основной корпус, стекло, hardpoints, constructs и анимации сохранены.\n'
        'Крылья сдвинуты назад к законцовкам с защитой зон оружейных точек; добавлена броня корней и кожухи двигателей.\n'
        'Изменены силуэты нижних LOD крыльев; мелкие накладки есть только в LOD0.\n'
        'Это НЕ готовая замена в игре: SUR и damage caps требуют отдельной доработки, HUD wire пока исходный.\n'
        'Видеоролик проигрывает существующий канал крыла туда и обратно, а не воспроизводит игровые триггеры.\n'
        'Рабочая игра не запускалась и не изменялась.\n',encoding='utf-8')
    with zipfile.ZipFile(OUT/'rh_raider_prototype.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in OUT.iterdir():
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    print('Prototype ready:',OUT,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--video',action='store_true')
    args=parser.parse_args();previews(build(),args.video)
