"""Accepted F01 fighter -> offline production sources. Never writes to game DATA."""
import copy, json, math, secrets, shutil, struct
from pathlib import Path
import numpy as np
import rh_freighter_final as shared
import rh_concept_b_final as f
import rh_fighter_f01_uv3 as proto
import full_ship_audit as aa

ROOT=Path(__file__).resolve().parents[2]
TOPIC=ROOT/'out/ship_design/rh_fighter'
OUT=TOPIC/'rh_pir_fighter'
SOURCE=OUT/'source'
ASSETS=OUT/'assets'
PREVIOUS=TOPIC/'prototypes/f01_uv_03'
GAME=Path('D:/Games/FL_MOD')
MAT=GAME/'DATA/ships/rheinland/rh_pir_playerships.mat'
ENV=GAME/'DATA/fx/envmapbasic.mat'
ATLAS='rh_pir_fighter_f01_projection_lod'
PARTS={s+'_'+p:s+'_'+p+'_lod1' for s in ('port','starboard') for p in ('wing','engine')}
dump,tree,packed,points,world,hardpoints,set_hardpoints,simple_geometry=(getattr(shared,n) for n in ('dump','tree','packed','points','world','hardpoints','set_hardpoints','simple_geometry'))
def read(name):return json.loads((OUT/name).read_text(encoding='utf8'))
def s64(v):return v.encode().ljust(64,b'\0')
def rot(a):return proto.first.rot([0,0,1],a)

def runtime(nodes,time,script='Sc_extend wing'):
    flat={p.lower():n.blob for p,n in f.mesh.walk(nodes)}
    joints=aa.constructs(flat);channels=aa.channels(flat,joints)
    values={c['child'].lower():[float(np.interp(time,c['times'],np.array(c['values'])[:,0]))] for c in channels if c['script']==script.lower()}
    return aa.matrices(joints,values)

def new_hp(name,pos,owner='Root',kind='Fixed',orientation=None):
    r=np.eye(3) if orientation is None else np.array(orientation)
    return dict(name=name,position=np.array(pos),owner=owner,kind=kind,orientation=r,
        leaves={'Position':np.array(pos,'<f4').tobytes().hex(),'Orientation':np.array(r,'<f4').tobytes().hex()})

def surface_at(gs,position,axis):
    """Outermost triangle intersection, keeping the other two coordinates fixed."""
    axes=[a for a in range(3) if a!=axis];q=np.array(position)[axes];hits=[]
    for g in gs:
        for t in np.array(g['corners']):
            p=t[:,:3];a=p[0,axes];uv=np.column_stack((p[1,axes]-a,p[2,axes]-a))
            if abs(np.linalg.det(uv))<1e-9:continue
            u,v=np.linalg.solve(uv,q-a)
            if u>=-1e-6 and v>=-1e-6 and u+v<=1.000001:hits.append(p[0,axis]+u*(p[1,axis]-p[0,axis])+v*(p[2,axis]-p[0,axis]))
    assert hits,('HP does not project onto mesh',position,axis)
    return max(hits)

def neck_uv(entries):
    """One unmirrored pale panel across the accepted neck's central slope."""
    changes=0;entry=entries['Native_cabin_transition']
    for g in entry['groups']:
        for t in g['corners']:
            p=t[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
            if abs(n[0])>.01 or n[1]<.25 or p[:,1].min()<.19:continue
            t[:,6]=.525+(p[:,0]+.91)/1.82*.46
            t[:,7]=.510-(p[:,2]+4.70)/.45*.174
            changes+=1
    assert changes==6,changes
    # The same position across the old center seam now has exactly one UV.
    uv={}
    for g in entry['groups']:
        for t in g['corners']:
            p=t[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
            if abs(n[0])>.01 or n[1]<.25 or p[:,1].min()<.19:continue
            for v in t:
                key=tuple(v[:3].round(5))
                if key in uv:assert np.allclose(uv[key],v[6:],atol=1e-7)
                uv[key]=v[6:]
    return dict(object=entry['name'],triangles=changes,charts=1,mirrored=False,crop=[.525,.336,.985,.510],geometry_unchanged=True,center_seam_uv_continuous=True)

def prepare():
    assert shutil.disk_usage(ROOT).free>6*1024**3
    OUT.mkdir(parents=True,exist_ok=True);SOURCE.mkdir(exist_ok=True);ASSETS.mkdir(exist_ok=True)
    data=json.loads((PREVIOUS/'geometry.json').read_text(encoding='utf8'))
    for filename,sha in data['sources'].items():
        p=SOURCE/'original.cmp' if Path(filename)==Path(data['source']) and (SOURCE/'original.cmp').exists() else Path(filename)
        assert f.digest(p)==sha,filename
    for item in data['exports']:
        assert f.digest(Path(item['file']))==item['sha256'],'User edited prototype: import HP changes before rebuilding'
    native=Path(data['source'])
    for src,dst in ((native,SOURCE/'original.cmp'),(native.with_suffix('.sur'),SOURCE/'original.sur')):
        if not dst.exists():shutil.copy2(src,dst)
    assert f.digest(SOURCE/'original.cmp')==data['source_sha256']
    assert f.digest(SOURCE/'original.sur')=='4a8f706b773124abe671f1fb75cc75e3ce2eb13bdfdd6c5ca83d2f93a881948e'
    # The next user-edited extended CMP is authoritative for HPs. Keep it as
    # an authoring source before regenerating either production or review files.
    hp_source=SOURCE/'user_hardpoints.cmp';review=OUT/'rh_pir_fighter_review_open.cmp'
    if review.exists() and (OUT/'build.json').exists() and f.digest(review)!=read('build.json')['review_sha256']:
        shutil.copy2(review,hp_source)
        dump(OUT/'user_hardpoint_source.json',dict(file=str(hp_source),sha256=f.digest(hp_source),original_review=str(review),
             coordinate_origin=read('build.json').get('origin_offset',[0,0,0])))
    header,native_nodes=tree(SOURCE/'original.cmp')
    entries={o['name']:dict(o,groups=packed(o['groups'])) for o in data['objects']}
    uv_change=neck_uv(entries);dump(OUT/'neck_uv_check.json',uv_change)
    groups={'Root':[]};mapping={}
    for name,ob in entries.items():
        target='Root'
        if name=='glass_lod1':target=name
        if name.endswith('_BayDoor'):target=name.lower()+'_lod1'
        for label,s in [('Port','port'),('Starboard','starboard')]:
            for suffix,t in [('sculpted_engine',s+'_engine_lod1'),('swept_wing',s+'_wing_mesh'),('slide_carriage',s+'_wing_slide'),('slide_guide',s+'_wing_lod1')]:
                if name==label+'_'+suffix:target=t
        groups.setdefault(target,[]).extend(ob['groups']);mapping[name]=target
    cons=f.folder('Cons');cmpnd=f.folder('Cmpnd',cons)
    ns=[f.folder('\\',cmpnd,f.folder('VMeshLibrary'))];files={};fix=[];pris=[];rev=[]
    angle=math.radians(proto.LEVEL)
    for i,(name,gs) in enumerate(groups.items()):
        file='rhff_'+name+'.3db';files[name]=file
        cmpnd.children.append(f.folder('Root' if i==0 else 'Part_'+name,f.textnode('File name',file),f.mesh.Node('Index',struct.pack('<I',i)),f.textnode('Object name',name)))
        ns[0].children.append(f.folder(file,f.folder('MultiLevel')))
        if name=='Root':continue
        side=-1 if name.startswith('port') else 1
        if name.endswith('_wing_slide'):
            vals=np.r_[[-side*proto.RETRACT,0,0],np.zeros(3),np.eye(3).ravel(),[side,0,0],[0,proto.RETRACT]]
            pris.append(s64(name.replace('_slide','_lod1'))+s64(name)+vals.astype('<f4').tobytes())
        elif name.endswith('_wing_mesh'):
            pivot=np.array([side*1.77,-1.02,0])
            vals=np.r_[pivot,pivot,rot(side*angle).ravel(),[0,0,side],[-angle,0]]
            rev.append(s64(name.replace('_mesh','_slide'))+s64(name)+vals.astype('<f4').tobytes())
        elif '_baydoor_' in name:
            m=data['motion']['Port_BayDoor' if side<0 else 'Starboard_BayDoor'];axis=np.array(m['axis']);axis/=np.linalg.norm(axis)
            vals=np.r_[m['pivot'],m['pivot'],np.eye(3).ravel(),axis*(-side),[0,math.radians(98)]]
            rev.append(s64('Root')+s64(name)+vals.astype('<f4').tobytes())
        else:fix.append(s64('Root')+s64(name)+np.r_[np.zeros(3),np.eye(3).ravel()].astype('<f4').tobytes())
    cons.children=[f.mesh.Node('Fix',b''.join(fix)),f.mesh.Node('Pris',b''.join(pris)),f.mesh.Node('Rev',b''.join(rev))]
    scripts=f.folder('Script');ns[0].children.append(f.folder('Animation',scripts))
    for script in ('Sc_extend wing','Sc_launch extend','Sc_force extend','Sc_extend wing keep','Sc_open baydoor','Sc_end anim'):
        node=f.folder(script);scripts.children.append(node)
        if script=='Sc_launch extend':times=np.unique(np.r_[0,5,5+np.linspace(0,2,65)]);phases=1-np.clip((times-5)/2,0,1)
        elif script=='Sc_extend wing':times=np.unique(np.r_[np.linspace(0,2,101),.76]);phases=times/2
        elif script=='Sc_force extend':times=np.array([0,1e17]);phases=np.array([0,1])
        elif script=='Sc_extend wing keep':times=np.array([0,2]);phases=np.ones(2)
        else:times=np.linspace(0,2.1333333 if script=='Sc_open baydoor' else 1/30,65);phases=times/times[-1] if script=='Sc_open baydoor' else 1-times/times[-1]
        for side,label in [(-1,'port'),(1,'starboard')]:
            if script in ('Sc_open baydoor','Sc_end anim'):
                smooth=phases**2*(3-2*phases);channels=[(label+'_baydoor_lod1','Root',math.radians(98)*smooth)]
            else:
                turn=np.clip(phases/.38,0,1);turn=turn**2*(3-2*turn)
                slide=np.clip((phases-.38)/.62,0,1);slide=slide**2*(3-2*slide)
                channels=[(label+'_wing_slide',label+'_wing_lod1',proto.RETRACT*(1-slide)),(label+'_wing_mesh',label+'_wing_slide',angle*(turn-1))]
            for child,parent,vals in channels:
                node.children.append(f.folder('Joint map '+str(len(node.children)),f.textnode('Parent name',parent),f.textnode('Child name',child),
                    f.folder('Channel',f.mesh.Node('Header',struct.pack('<IfI',len(times),-1,1)),f.mesh.Node('Frames',np.column_stack((times,vals)).astype('<f4').tobytes()))))
    f.write_geometry(ns,[{files[n]:gs for n,gs in groups.items()}])
    # Authored aircraft HP positions: retain native cockpit and hidden equipment;
    # attach visible equipment to real surfaces, matching each animated owner.
    hps=hardpoints(native_nodes,('Sc_extend wing',0));old=copy.deepcopy(hps)
    hps={k:h for k,h in hps.items() if not k.startswith('dp')}
    for h in hps.values():h['owner']='Root'
    targets={'hpengine01':('port_engine_lod1',[-proto.model.ENGINE_X,proto.prev.ENGINE_Y,4.11]),
        'hpengineglow':('Root',[0,proto.prev.ENGINE_Y,4.11]),'hpmass01':('Root',[0,0,0]),
        'hprunninglight01':('Root',[0,2.947,2.9]),'hprunninglight02':('Root',[0,-2.49,3.31]),
        'hpc m01':('Root',[1.03,-1.65,3.455]),'hpmine01':('Root',[-1.03,-1.65,3.455]),
        'hpthruster01':('Root',[-.68,-1.96,3.455]),'hpthruster02':('Root',[.68,-1.96,3.455]),
        'hpdocklight01':('Root',[-1.26,1.55,-3.62]),'hpdocklight02':('Root',[1.26,1.55,-3.62]),
        'hprunninglight05':('Root',[1.62,1.44,.4]),'hprunninglight06':('Root',[-1.62,1.44,.4]),
        'hpweapon01':('Root',[-1.50,1.47,-2.1]),'hpweapon02':('Root',[1.50,1.47,-2.1]),
        'hpmount':('Root',[0,-2.5,0]),'hpcontrail03':('Root',[-2.35,.59,2.95]),'hpcontrail04':('Root',[2.35,.59,2.95])}
    targets['hpcm01']=targets.pop('hpc m01')
    for side,label,gun,light,trail in [(-1,'port','03','03','02'),(1,'starboard','04','04','01')]:
        for key,x,z in [('hpweapon'+gun,4.61,-2.55),('hprunninglight'+light,5.14,-3.19),('hpcontrail'+trail,4.98,-3.13)]:
            y=-1.02-.285*(x-1.77)
            targets[key]=(label+'_wing_mesh',[side*x,y+.025,z])
    for key,(owner,pos) in targets.items():hps[key].update(owner=owner,position=np.array(pos))
    for key in ('hpweapon01','hpweapon02','hpweapon03','hpweapon04'):
        h=hps[key];h['position'][1]=surface_at(groups[h['owner']],h['position'],1)+.008
    for key in ('hpcm01','hpmine01','hpthruster01','hpthruster02'):
        h=hps[key];h['position'][2]=surface_at(groups['Root'],h['position'],2)+.008
    hps['hpengine02']=copy.deepcopy(hps['hpengine01']);hps['hpengine02'].update(name='HpEngine02',owner='starboard_engine_lod1',position=np.array([proto.model.ENGINE_X,proto.prev.ENGINE_Y,4.11]))
    _,opened=tree(PREVIOUS/'rh_pir_fighter_f01_uv3_open.cmp')
    for key,h in hardpoints(opened).items():h['owner']=mapping[h['owner']];hps[key]=h
    # Point the six dorsal weapons and shield normal out of the upper skin.
    for key in ('hpweapon01','hpweapon02'):
        h=hps[key];p=np.array(h['position']);left=p.copy();right=p.copy();left[0]-=.01;right[0]+=.01
        slope=(surface_at(groups['Root'],right,1)-surface_at(groups['Root'],left,1))/.02
        h['orientation']=rot(math.atan(slope))@np.array(hps['hpweapon05']['orientation'])
    for side,label in [(-1,'port'),(1,'starboard')]:
        key='hpweapon'+('03' if side<0 else '04');hps[key]['orientation']=rot(-side*math.atan(.285))@np.array(hps['hpweapon05']['orientation'])
    for zone,part in PARTS.items():
        label='Port' if zone.startswith('port') else 'Starboard'
        anchor=np.array([(-1 if label=='Port' else 1)*1.77,-1.02,0]) if 'wing' in zone else np.array([(-1 if label=='Port' else 1)*proto.model.ENGINE_X,proto.prev.ENGINE_Y,1.76])
        h=new_hp('DpRHF_'+zone,anchor);hps[h['name'].lower()]=h
    hps['hphardware01']=new_hp('HpHardware01',[0,0,0])
    if hp_source.exists():
        _,edited=tree(hp_source);hps=hardpoints(edited)
        source_origin=np.array(read('user_hardpoint_source.json').get('coordinate_origin',[0,0,0]))
        for h in hps.values():h['position']+=source_origin
        assert all(h['owner'] in groups for h in hps.values())
        assert all(('dprhf_'+zone) in hps for zone in PARTS),'Edited CMP lost required unique damage anchors'
    import rh_fighter_final_mounts
    rh_fighter_final_mounts.patch(entries,groups,hps)
    import rh_fighter_final_origin as origin_tools
    origin=origin_tools.rebase(entries,groups,hps,ns)
    f.write_geometry(ns,[{files[n]:gs for n,gs in groups.items()}])
    set_hardpoints(ns,hps)
    (OUT/'authoring_animated.cmp').write_bytes(f.mesh.write_tree(header,ns))
    errors=[]
    for time in np.linspace(0,2,61):
        mats=runtime(ns,time)
        for label in ('Port','Starboard'):
            for suffix in ('swept_wing','slide_carriage'):
                name=label+'_'+suffix;expected=origin_tools.transform(proto.motion_transform(data['motion'][name],time/2),origin);actual=mats[mapping[name].lower()]
                errors.append(max(np.max(abs(expected[0]-actual[0])),np.max(abs(expected[1]-actual[1]))))
    assert max(errors)<.0006,max(errors)
    # Zero pose must be exactly the accepted folded endpoint.
    tr,_=f.audit.transforms(ns)
    for label in ('Port','Starboard'):
        for suffix in ('swept_wing','slide_carriage'):
            name=label+'_'+suffix;r,t=origin_tools.transform(proto.motion_transform(data['motion'][name],1),origin);rr,tt=tr[files[mapping[name]].lower()]
            assert np.allclose(r,rr,atol=2e-6) and np.allclose(t,tt,atol=2e-6)
    dump(OUT/'rig_check.json',dict(origin_offset=origin,samples=61,max_motion_matrix_error=max(errors),zero_pose='accepted folded',flight='Sc_extend wing at t=0; launch 5s delay + 2s unfold',part_map=mapping,hardpoints=hps,source_hardpoints=old,triangles=sum(len(g['corners']) for gs in groups.values() for g in gs),installed=False))
    mats=f.audit.material_table([MAT,ENV]);used={g['material'] for gs in groups.values() for g in gs}|{f.mesh.crc(n) for n in ('pir_r_dmg3','Equip_genD','debris')}
    textures=OUT/'textures';textures.mkdir(exist_ok=True);images={}
    for mid in used:
        m=mats[mid];entry={k:v for k,v in m.items() if k!='image'}
        if m['image'] is not None:
            path=textures/(m['texture'].rsplit('.',1)[0]+'.png')
            if not path.exists():m['image'].save(path)
            entry['image_path']=str(path)
        images[mid]=entry
    dump(OUT/'blender_input.json',dict(origin_offset=origin,objects=[dict(name=n,groups=gs) for n,gs in groups.items()],materials=images,original_objects=list(entries.values()),damage_material=f.mesh.crc('pir_r_dmg3'),equipment_material=f.mesh.crc('Equip_genD'),source_hash=f.digest(PREVIOUS/'geometry.json'),neck_uv=uv_change))
    print('RIG READY',len(groups),'parts;',len(hps),'HP; motion error',max(errors),flush=True)

if __name__=='__main__':prepare()
