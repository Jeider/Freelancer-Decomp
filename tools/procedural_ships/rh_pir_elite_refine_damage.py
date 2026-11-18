"""Offline RH pirate revision: static part-owned wire and native-style broken engines.

Reads the user's current CMP. Never writes game DATA or Pythonlancer sources.
"""
import copy
import json
from pathlib import Path
import secrets
import struct as S
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rh_pir_elite_build as b
import rh_concept_b_final_damage as damage
from rh_concept_b_damage_reference import groups
from ship_collision_audit import sur_parts, surface
from preview import render

f = b.f
GAME = Path('D:/Games/FL_MOD')
SOURCE = GAME/'DATA/ships/rheinland/rh_pir_elite'
ORIGINAL = GAME/'DATA/ships/rheinland/rh_elite'
OUT = b.OUT/'damage_refinement'
ASSETS = OUT/'assets'
EXPECTED = 'efea2269657f364a8925379a5c566bd5f1f19a0c71e7d565f33106c4e8d26cd0'


def save(path, data):
    path.write_text(json.dumps(data, default=b.v.hp.serial, ensure_ascii=False, indent=2), encoding='utf8')


def string64(s):
    raw=s.encode(); assert len(raw)<64
    return raw.ljust(64,b'\0')


def cap_in_engine(model, cap, side):
    ns=f.mesh.read_tree(model.read_bytes())[1]
    names=f.component_map(ns); tr,_=f.audit.transforms(ns)
    file=next(k for k,v in names.items() if v==f'Rh_{side}_engine_lod1')
    r,t=tr[file.lower()]; hp=f.hp_world(ns)[f'dp{side}_engine']
    cn=f.mesh.read_tree(cap.read_bytes())[1]
    leaves={p.lower():n.blob for p,n in f.mesh.walk(cn)}
    ct=np.frombuffer(next(v for p,v in leaves.items() if p.endswith('/dpconnect/position')),'<f4')
    cr=np.frombuffer(next(v for p,v in leaves.items() if p.endswith('/dpconnect/orientation')),'<f4').reshape(3,3)
    hr=np.array(hp['orientation']);ht=np.array(hp['position'])
    world=f.base.world(groups(cap),hr@cr.T,ht-hr@cr.T@ct)
    return f.base.world(world,r.T,-r.T@t),f.local_geometry(ns)[file]


def static_wings(nodes):
    names=f.component_map(nodes); unfolded,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    local=f.local_geometry(nodes)
    cmpnd=f.mesh.child(nodes[0],'Cmpnd');cons=f.mesh.child(cmpnd,'Cons')
    rev=f.mesh.child(cons,'Rev');fix=f.mesh.child(cons,'Fix')
    raw=bytearray(rev.blob);fixed=bytearray(fix.blob)
    library=f.mesh.child(nodes[0],'VMeshLibrary')
    index=max(S.unpack_from('<I',f.mesh.child(n,'Index').blob)[0] for n in cmpnd.children if n.name!='Cons')
    result={}
    for side in ('port','starboard'):
        owner=f'Rh_{side}_wing_lod1';moving=f'Rh_{side}_wing_mesh'
        file=next(k for k,v in names.items() if v==owner)
        entry=next(n for n in cmpnd.children if n.name!='Cons' and f.mesh.string(f.mesh.child(n,'Object name').blob)==owner)
        part=f.mesh.child(nodes[0],file);child=copy.deepcopy(part);child.name=moving+'.3db'
        nodes[0].children.append(child)
        newentry=copy.deepcopy(entry);newentry.name='Part_'+moving;index+=1
        f.mesh.child(newentry,'Object name').blob=moving.encode()+b'\0'
        f.mesh.child(newentry,'File name').blob=child.name.encode()+b'\0'
        f.mesh.child(newentry,'Index').blob=S.pack('<I',index)
        cmpnd.children.append(newentry)
        ur,ut=unfolded[file.lower()]
        # Parent keeps the unfolded frame used by the existing local SUR/wire.
        fixed+=string64('Root')+string64(owner)+np.r_[ut,ur.ravel()].astype('<f4').tobytes()
        for at in range(0,len(raw),208):
            if f.mesh.string(raw[at+64:at+128])!=owner:continue
            vals=np.frombuffer(raw,'<f4',20,at+128)
            pivot=vals[3:6].copy()
            vals[:3]=ur.T@(vals[:3]-ut)
            vals[6:15]=(ur.T@vals[6:15].reshape(3,3)).ravel()
            vals[15:18]=ur.T@vals[15:18]
            raw[at:at+64]=string64(owner);raw[at+64:at+128]=string64(moving)
            break
        else:raise AssertionError('Missing wing Rev')
        # A tiny valid hidden triangle follows the proven rh_alt_elite convention.
        # No full wing is duplicated here. All original meshes and HPs stay on child.
        tri=np.zeros((1,3,8));tri[0,:,:3]=pivot+np.array([[0,0,0],[.002,0,0],[0,.002,0]])
        tri[0,:,5]=1
        blob,verts=f.mesh.pack([dict(material=local[file][0]['material'],corners=tri,unused=204)])
        vname=moving+'_proxy.vms';library.children.append(f.folder(vname,f.mesh.Node('VMeshData',blob)))
        ml=copy.deepcopy(f.mesh.child(part,'MultiLevel'))
        for level in ml.children:
            if level.name.startswith('Level'):
                f.mesh.child(f.mesh.child(level,'VMeshPart'),'VMeshRef').blob=f.fresh_ref(vname,blob,verts)
        part.children=[ml,copy.deepcopy(f.mesh.child(part,'VMeshWire'))]
        # Explicitly empty child wire suppresses IMesh fallback in both HUD paths.
        ref=f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(child,'MultiLevel'),'Level0'),'VMeshPart'),'VMeshRef')
        crc=S.unpack_from('<I',ref.blob,4)[0]
        f.mesh.child(f.mesh.child(child,'VMeshWire'),'VWireData').blob=S.pack('<II4H',16,crc,0,0,0,0)
        changed=0
        for script in f.mesh.child(f.mesh.child(nodes[0],'Animation'),'Script').children:
            for joint in script.children:
                node=f.mesh.child(joint,'Child name')
                if f.mesh.string(node.blob)!=owner:continue
                node.blob=moving.encode()+b'\0'
                f.mesh.child(joint,'Parent name').blob=owner.encode()+b'\0';changed+=1
        result[owner]=dict(moving=moving,static_rotation=ur,static_position=ut,animation_channels=changed)
    rev.blob=bytes(raw);fix.blob=bytes(fixed)
    return result


def broken_engines(nodes):
    # The copied retail wounds were rejected: their holes fit another assembly.
    # Author fractures from our current intact cylinder and actual support.
    from rh_pir_engine_damage_closed import make_engine, ray_checks
    damage.OUT=OUT
    names=f.component_map(nodes);tr,_=f.audit.transforms(nodes);hp=f.hp_world(nodes)
    report={};geometry={}
    for side in ('port','starboard'):
        file=next(k for k,v in names.items() if v==f'Rh_{side}_engine_lod1')
        current=f.local_geometry(nodes)[file]
        gs,checks=make_engine(current,side);checks.update(ray_checks(gs))
        # Neutral DpConnect; encode the whole broken cylinder in its receiving HP frame.
        hr=np.array(hp[f'dp{side}_engine']['orientation']);ht=np.array(hp[f'dp{side}_engine']['position'])
        r,t=tr[file.lower()];world=f.base.world(gs,r,t)
        cap=f.base.world(world,hr.T,-hr.T@ht)
        info=damage.write_simple(f'rh_pir_elite_dmg_{side}_engine',cap)
        info.update(source='current intact engine',checks=checks,
                    support_triangles=12,materials=[hex(g['material']) for g in gs])
        report[side]=info;geometry[side]=dict(healthy=current,damaged=gs,world=world)
    return report,geometry


def transforms_at(nodes,script,phase):
    ns=copy.deepcopy(nodes)
    sc=f.mesh.child(f.mesh.child(f.mesh.child(ns[0],'Animation'),'Script'),script)
    for joint in sc.children:
        channel=f.mesh.child(joint,'Channel');head=f.mesh.child(channel,'Header').blob
        count,interval,kind=S.unpack('<IfI',head);assert interval==-1 and kind==1
        node=f.mesh.child(channel,'Frames');frames=np.frombuffer(node.blob,'<f4').reshape(-1,2).copy()
        frames[0,1]=np.interp(frames[0,0]+phase*(frames[-1,0]-frames[0,0]),frames[:,0],frames[:,1])
        node.blob=frames.tobytes()
    return f.audit.transforms(ns,(script,0))[0]


def decoded_wire(nodes,tr):
    lib={f.mesh.crc(p.split('/')[-2]):f.audit.decode(n.blob)[0] for p,n in f.mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    out={}
    for file,name in f.component_map(nodes).items():
        raw=f.mesh.child(f.mesh.child(f.mesh.child(nodes[0],file),'VMeshWire'),'VWireData').blob
        size,crc,bias,nv,ni,total=S.unpack_from('<II4H',raw);ids=np.frombuffer(raw,'<u2',offset=16)
        assert size==16 and ni==len(ids) and nv==len(set(ids))==total
        r,t=tr[file.lower()]
        out[name]=(lib[crc][bias+ids,:3]@r.T+t).reshape(-1,2,3)
    return out


def validate(before,after,owners,matmap):
    names=f.component_map(before);newnames=f.component_map(after);newfiles={v:k for k,v in newnames.items()}
    points={};hpnames=set()
    for file,gs in f.local_geometry(before).items():
        points[file]=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs])
    # HP subtrees are byte-identical, including user's two newly moved engine points.
    for file,name in names.items():
        target=newfiles[owners.get(name,{}).get('moving',name)]
        old={p.split('/Hardpoints/',1)[1]:n.blob for p,n in f.mesh.walk([f.mesh.child(before[0],file)]) if '/Hardpoints/' in p}
        new={p.split('/Hardpoints/',1)[1]:n.blob for p,n in f.mesh.walk([f.mesh.child(after[0],target)]) if '/Hardpoints/' in p}
        assert old==new,('Changed HP',name)
        hpnames.update(p for p in old if p.endswith('/Position'))
    counts=[]
    for lv in range(3):
        old=f.local_geometry(before,lv);new=f.local_geometry(after,lv);count=0
        for file,name in names.items():
            target=newfiles[owners.get(name,{}).get('moving',name)]
            assert len(old[file])==len(new[target])
            for a,c in zip(old[file],new[target]):
                assert matmap.get(a['material'],a['material'])==c['material']
                assert np.array_equal(a['corners'],c['corners']),name
                count+=len(c['corners'])
        counts.append(count+2)
    poses=[(None,None)]+[(s.name,t) for s in f.mesh.child(f.mesh.child(before[0],'Animation'),'Script').children for t in (0,.25,.5,.75,1)]
    max_error=0.;reference=None
    for script,phase in poses:
        a=f.audit.transforms(before)[0] if script is None else transforms_at(before,script,phase)
        c=f.audit.transforms(after)[0] if script is None else transforms_at(after,script,phase)
        for file,name in names.items():
            target=newfiles[owners.get(name,{}).get('moving',name)]
            r,t=a[file.lower()];nr,nt=c[target.lower()]
            error=np.max(abs(points[file]@r.T+t-(points[file]@nr.T+nt)));max_error=max(max_error,float(error))
            assert error<1e-5,(script,phase,name,error)
            # Equal complete frames imply every local HP keeps its world transform.
            assert np.allclose(r,nr,atol=1e-6) and np.allclose(t,nt,atol=1e-6)
        wires=decoded_wire(after,c)
        if reference is None:reference=wires
        for owner,info in owners.items():
            assert len(wires[owner])==6 and not len(wires[info['moving']])
            assert np.allclose(wires[owner],reference[owner],atol=1e-6)
    # The static parent is the exact old unfolded frame; existing SUR stays valid.
    ut=f.audit.transforms(before,('Sc_extend wing',0))[0];rt=f.audit.transforms(after)[0]
    for file,name in names.items():
        target=newfiles[name]
        if name in owners:
            for x,y in zip(ut[file.lower()],rt[target.lower()]):assert np.allclose(x,y,atol=1e-6)
    rootkeys={tuple(sorted((b.key(a),b.key(c)))) for a,c in reference['Root']}
    for name in b.v.ZONES:
        assert not rootkeys&{tuple(sorted((b.key(a),b.key(c)))) for a,c in reference[name]}
    return dict(animation_pose_checks=len(poses),max_world_error=max_error,lod_triangles=counts,
                hardpoints=len(hpnames),hardpoint_payloads_unchanged=True,
                static_wire=True,unfolded_sur_frames_preserved=True),reference


def previews(geo,wires,nodes):
    mats=f.audit.material_table([GAME/'DATA/ships/rheinland/rh_pir_playerships.mat'])
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
    sheet=Image.new('RGB',(1400,1450),'#14222b');draw=ImageDraw.Draw(sheet)
    for row,side in enumerate(('port','starboard')):
        pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for state in ('healthy','damaged') for g in geo[side][state]])
        center=(pts.min(0)+pts.max(0))*.5;radius=np.linalg.norm(pts-center,axis=1).max()*1.13
        for col,state in enumerate(('healthy','damaged')):
            im=render(geo[side][state],mats,center,radius,(-1,-.6,1),size=700,mode='texture')
            sheet.paste(im,(700*col,725*row+45));draw.text((700*col+15,725*row+10),side+' / '+state,font=font,fill='white')
    sheet.save(OUT/'engine_preview.png')
    im=Image.new('RGB',(1500,1100),'#0b1a24');draw=ImageDraw.Draw(im)
    cases=[('Сложенная модель — раскрытый HUD',None),('Левое крыло выделено','selected'),
           ('Левое крыло разрушено','port'),('Правое крыло разрушено','starboard')]
    ps=np.concatenate([x[..., [0,2]].reshape(-1,2) for x in wires.values() if len(x)])
    center=(ps.min(0)+ps.max(0))*.5;scale=min(620/np.ptp(ps[:,0]),400/np.ptp(ps[:,1]))
    for i,(label,case) in enumerate(cases):
        offset=np.array([375+(i%2)*750,300+(i//2)*550])
        draw.text((offset[0]-350,offset[1]-245),label,font=font,fill='white')
        for name,lines in wires.items():
            if case in ('port','starboard') and name==f'Rh_{case}_wing_lod1':continue
            color='#ffda3a' if case=='selected' and name=='Rh_port_wing_lod1' else '#8edce8'
            for line in lines:
                xy=(line[:,[0,2]]-center)*scale+offset
                draw.line([tuple(p) for p in xy],fill=color,width=3 if color=='#ffda3a' else 2)
    im.save(OUT/'wire_preview.png')
    # In-context damage view: attach the exported stump at its actual receiver.
    tr,_=f.audit.transforms(nodes,('Sc_extend wing',0));names=f.component_map(nodes)
    scene=[g for file,gs in f.local_geometry(nodes).items() if '_engine_' not in names[file].lower() for g in f.base.world(gs,*tr[file.lower()])]
    for side in ('port','starboard'):scene+=geo[side]['world']
    ps=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene]);center=(ps.min(0)+ps.max(0))*.5
    render(scene,mats,center,np.linalg.norm(ps-center,axis=1).max(),(-1,.55,1),size=1100,mode='texture').save(OUT/'ship_damaged.png')


def main():
    OUT.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(exist_ok=True)
    source=SOURCE/'rh_pir_elite.cmp';assert f.digest(source)==EXPECTED,'Preserve newer user edits; review before updating baseline'
    baseline={p.name:f.digest(p) for p in SOURCE.iterdir() if p.suffix.lower() in ('.cmp','.sur','.mat','.3db')}
    header,nodes=f.mesh.read_tree(source.read_bytes());before=copy.deepcopy(nodes)
    owners=static_wings(nodes);engines,geometry=broken_engines(nodes)
    salt=secrets.token_hex(6)
    # The user merged this atlas into their shared MAT. Its identity is now
    # shared, so preserve it instead of salting and shipping another private MAT.
    mh,mn=f.mesh.read_tree((SOURCE/'rh_pir_elite_lods.mat').read_bytes())
    material=f.mesh.child(mn[0],'Material library').children[0];texture=f.mesh.child(mn[0],'Texture library').children[0]
    shared_path=GAME/'DATA/ships/rheinland/rh_pir_playerships.mat'
    shared=f.mesh.read_tree(shared_path.read_bytes())[1]
    target_mat=f.mesh.child(f.mesh.child(shared[0],'Material library'),'rh_b_projection_lod')
    target_tex=f.mesh.child(f.mesh.child(shared[0],'Texture library'),'rh_b_projection_lod.tga')
    assert [(n.name,n.blob) for n in texture.children]==[(n.name,n.blob) for n in target_tex.children]
    assert [(n.name,n.blob) for n in material.children if n.name!='Dt_name']==[(n.name,n.blob) for n in target_mat.children if n.name!='Dt_name']
    matmap={f.mesh.crc(material.name):f.mesh.crc(target_mat.name)}
    # Retain one local reference outside the deliverable assets directory.
    reference=OUT/'reference_lod_mat';reference.mkdir(exist_ok=True)
    (reference/'rh_pir_elite_lods.mat').write_bytes((SOURCE/'rh_pir_elite_lods.mat').read_bytes())
    obsolete=ASSETS/'rh_pir_elite_lods.mat'
    assert obsolete.resolve().parent==ASSETS.resolve()
    obsolete.unlink(missing_ok=True)
    resources=b.salt_tree(nodes,salt,matmap)
    target=ASSETS/'rh_pir_elite.cmp';target.write_bytes(f.mesh.write_tree(header,nodes))
    (ASSETS/'rh_pir_elite.sur').write_bytes((SOURCE/'rh_pir_elite.sur').read_bytes())
    for i,zone in enumerate(('port_wing','starboard_wing','port_engine','starboard_engine','tail')):
        name='rh_pir_elite_dmg_'+zone
        path=(OUT/'damage' if 'engine' in zone else SOURCE)/(name+'.3db')
        h,ns=f.mesh.read_tree(path.read_bytes());resources[name]=b.salt_tree(ns,salt+'d'+str(i))
        (ASSETS/path.name).write_bytes(f.mesh.write_tree(h,ns))
        (ASSETS/(name+'.sur')).write_bytes(path.with_suffix('.sur').read_bytes())
        if 'engine' in zone:
            item=engines[zone.split('_',1)[0]]
            item['file']='assets/'+path.name
            item['sha256']=f.digest(ASSETS/path.name)
            item['sur_sha256']=f.digest(ASSETS/(name+'.sur'))
    reopened=f.mesh.read_tree(target.read_bytes())[1]
    checks,wires=validate(before,reopened,owners,matmap)
    mats=f.audit.material_table([shared_path])
    for path in ASSETS.iterdir():
        if path.suffix in ('.cmp','.3db'):
            ns=f.mesh.read_tree(path.read_bytes())[1]
            assert not any(n.name.lower() in ('material library','texture library') for n in ns[0].children)
            for p,n in f.mesh.walk(ns):
                if not p.lower().endswith('/vmeshdata'):continue
                verts,gs,ids=f.audit.decode(n.blob)
                assert np.isfinite(verts).all() and len(verts)<65536 and len(ids)<65536
                assert all(g[0] in mats for g in gs),path
        elif path.suffix=='.sur':
            for pid,chunks in sur_parts(path.read_bytes()):
                for tag,raw in chunks:
                    if tag==b'surf':surface(raw)
    previews(geometry,wires,reopened)
    assert baseline=={name:f.digest(SOURCE/name) for name in baseline},'Game files changed during preparation'
    manifest=dict(source_cmp=str(source),source_sha256=EXPECTED,salt=salt,resources=resources,owners=owners,
        engines=engines,checks=checks,game_assets_unchanged=True,installed=False,
        shared_mat=str(shared_path),shared_mat_sha256=f.digest(shared_path),lod_material=target_mat.name,
        separate_lod_mat_required=False,
        sur_sha256=f.digest(ASSETS/'rh_pir_elite.sur'),
        files={p.name:dict(sha256=f.digest(p),bytes=p.stat().st_size) for p in ASSETS.iterdir() if p.suffix in ('.cmp','.sur','.mat','.3db')})
    assert len(manifest['files'])==12
    save(OUT/'build.json',manifest)
    save(ASSETS/'manifest.json',manifest)
    print(json.dumps(checks,indent=2));print('OFFLINE ASSETS',ASSETS)


if __name__=='__main__':main()
