"""Offline RH pirate elite: narrow persistent frame and removable tail shell."""
import collections
import copy
import json
import shutil
import secrets
import struct
import sys
from pathlib import Path
import numpy as np

sys.dont_write_bytecode = True
import rh_pir_elite_build as b
f = b.f
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/ship_design/rh_elite/rh_pir_elite/tail_rim'
GAME = Path('D:/Games/FL_MOD')
LIVE = GAME/'DATA/ships/rheinland/rh_pir_elite/rh_pir_elite.cmp'
NATIVE = GAME/'DATA/ships/rheinland/rh_elite/rh_elite.cmp'
MAT = GAME/'DATA/ships/rheinland/rh_pir_playerships.mat'
NATIVE_MAT = GAME/'DATA/ships/rheinland/rh_playerships.mat'
ENV = GAME/'DATA/fx/envmapbasic.mat'
PALE=f.mesh.crc('pir_r_panel01_256')
RED=f.mesh.crc('pir_r_panel02_256')
BROWN=f.mesh.crc('pir_r_panel01_256D')
RIM_HALF=.52


def face(builder,p,mid,uvbox,normal,uv=None):
    # Explicit charts avoid the older generic nearest-source-triangle mapper.
    builder.explicit(np.asarray(p,float),mid,uvbox,normal,uv)


def prism(poly,x0,x1,outer_mid=PALE):
    builder=f.b.Builder();p=np.asarray(poly,float)
    for x,n in ((x0,[-1,0,0]),(x1,[1,0,0])):
        q=np.column_stack((np.full(len(p),x),p))
        uv=(p-p.min(0))/np.ptp(p,axis=0)
        face(builder,q,outer_mid,(.505,.258,.997,.854),n,uv[:,::-1])
    area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
    for a,c in zip(p,np.roll(p,-1,axis=0)):
        delta=c-a;length=np.linalg.norm(delta)
        q=np.array([[x0,*a],[x1,*a],[x1,*c],[x0,*c]])
        n=np.r_[0,np.array([delta[1],-delta[0]])*np.sign(area)]
        face(builder,q,PALE,(.52,.103,.99,.164),n)
    return builder.groups()


def cheek(poly,side):
    builder=f.b.Builder();p=np.asarray(poly,float);hole=f.b.prev.inset(p,.14)
    outer=side*1.32;floor=side*1.265;inner=side*.56
    face(builder,np.column_stack((np.full(len(p),inner),p)),PALE,(.505,.258,.997,.854),[-side,0,0])
    center=p.mean(0)
    for i,j in [(i,(i+1)%len(p)) for i in range(len(p))]:
        a,c=p[i],p[j];ha,hc=hole[i],hole[j]
        face(builder,[[outer,*a],[outer,*c],[outer,*hc],[outer,*ha]],PALE,(.52,.103,.99,.164),[side,0,0])
        d=c-a;n=np.r_[0,np.array([d[1],-d[0]])*np.sign(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))]
        face(builder,[[inner,*a],[inner,*c],[outer,*c],[outer,*a]],PALE,(.52,.103,.99,.164),n)
        face(builder,[[outer,*ha],[outer,*hc],[floor,*hc],[floor,*ha]],BROWN,(.505,.258,.997,.854),np.r_[0,center-(ha+hc)/2])
    # Two whole upright red panels, each fitted across the inset's width.
    def clip(poly,bound,above):
        q=[]
        for a,c in zip(poly,np.roll(poly,-1,axis=0)):
            ia=(a[0]>=bound) if above else (a[0]<=bound);ic=(c[0]>=bound) if above else (c[0]<=bound)
            if ia:q.append(a)
            if ia!=ic:q.append(a+(c-a)*(bound-a[0])/(c[0]-a[0]))
        return np.array(q)
    for above in (False,True):
        q=clip(hole,1.22,above);uv=(q-q.min(0))/np.ptp(q,axis=0)
        face(builder,np.column_stack((np.full(len(q),floor),q)),RED,(.337,.321,.663,.498),[side,0,0],uv)
    return builder.groups()


def flatten_groups(gs):
    return [dict(g,corners=np.asarray(g['corners'],float)) for g in gs]


def narrow_frame(gs):
    result=[]
    cuts=np.array([f.TAIL_CUT,f.TAIL_TOP])+np.array(json.loads((b.v.OUT/'build.json').read_text())['center_shift_native'])[1]
    for g in gs:
        a=np.array(g['corners'],copy=True);p=a[...,:3].copy()
        # Remove the old caps at the two now-obsolete tail separation planes.
        internal=np.any(np.max(abs(p[:,:,1,None]-cuts),axis=1)<2e-5,axis=1)
        a=a[~internal];p=p[~internal]
        for t,old in zip(a,p):
            t[:,0]*=RIM_HALF/1.32
            # Preserve physical UV density across the newly narrow top/end skins.
            duv=t[1:,6:8]-t[0,6:8]
            grad=np.linalg.pinv(old[1:]-old[0])@duv
            t[:,6:8]+=(t[:,:3]-old)@grad
            n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);t[:,3:6]=n/np.linalg.norm(n)
        if len(a):result.append(dict(g,corners=a))
    return result


def geometry():
    ns=load(OUT/'user_source.cmp')[1];w=world(ns);old=copy.deepcopy(w)
    frames=[];kept={};removed={}
    for part in ('Root','Rh_tail_lod1'):
        kept[part]=[];removed[part]=0
        for g in w[part]:
            a=g['corners'];mask=frame_mask(a);removed[part]+=int(mask.sum())
            if mask.any():frames.append(dict(g,corners=a[mask]))
            if (~mask).any():kept[part].append(dict(g,corners=a[~mask]))
    assert removed=={'Root':425,'Rh_tail_lod1':214},removed
    rim=narrow_frame(frames)
    root=kept['Root']
    # Two former outside ties taper inward to meet the narrow carrier, while
    # the actual drum and all three central supports remain byte-for-byte.
    for component in components(root):
        lo,hi=np.array(component['bounds'])
        if component['triangles']==16 and lo[2]>5.6 and hi[2]<8.01 and lo[1]>.8:
            for gi,ti in component['indices']:
                tri=root[gi]['corners'][ti]
                u=np.clip((tri[:,2]-6.3)/(7.847-6.3),0,1)
                tri[:,0]*=(1-u)*(.97/1.32)+u*(RIM_HALF/1.32)
                n=np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]);tri[:,3:6]=n/np.linalg.norm(n)
    tail_parts=components(kept['Rh_tail_lod1']);pylons=[];hatch=[]
    for comp in tail_parts:
        target=hatch if comp['triangles']==28 else pylons
        assert comp['triangles'] in (14,28)
        by=collections.defaultdict(list)
        for gi,ti in comp['indices']:by[gi].append(ti)
        for gi,ids in by.items():target.append(dict(kept['Rh_tail_lod1'][gi],corners=kept['Rh_tail_lod1'][gi]['corners'][ids].copy()))
    for g in hatch:
        a=g['corners'];a[:,:,2]=8.995+(a[:,:,2]-8.652)*.80
        for t in a:
            n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);t[:,3:6]=n/np.linalg.norm(n)
    shell_profile=np.array([[2.80,7.18],[3.30,8.98],[-.78,8.98],[-.36,7.18]])
    cheeks=[]
    for side in (-1,1):
        cheeks+=cheek(shell_profile,side)
    # Rear bridge joins both cheeks behind the surviving frame; hatch seats on it.
    bridge=prism([[-.78,8.74],[-.78,8.98],[3.30,8.98],[3.30,8.74]],-.56,.56)
    shell=cheeks+bridge
    w['Root']=f.merge(root+rim);w['Rh_tail_lod1']=f.merge(shell+hatch+pylons)
    save(OUT/'geometry.json',dict(parts=w,frame=rim,tail_shell=shell,tail_hatch=hatch,tail_pylons=pylons,
         shell_profile=shell_profile,source_sha256=f.digest(OUT/'user_source.cmp'),
         original_frame_width=2.64,native_frame_width=.9399,prototype_frame_width=2*RIM_HALF,
         frame_triangles_moved_to_root=removed))
    print('GEOMETRY READY',[(k,sum(len(g['corners']) for g in w[k])) for k in ('Root','Rh_tail_lod1')])


def damaged_shell(data):
    result=[]
    # Fracture the actual current shell into surviving top/bottom sheets. The
    # unequal saw-tooth cuts are authored from that shell, not copied retail caps.
    for side in (-1,1):
        z=np.array([7.18,7.39,7.63,7.91,8.19,8.48,8.73,8.98])
        upper=2.80+(z-7.18)*(.50/1.80)
        lower=-.36-(z-7.18)*(.42/1.80)
        u=np.array([2.49,2.60,2.21,2.43,2.12,2.37,2.52,2.46])+(0 if side==1 else -.16)
        l=np.array([-.08,.11,-.18,.20,-.09,.32,.02,-.18])+(0 if side==1 else .16)
        for top in (True,False):
            q=np.column_stack((np.r_[upper if top else lower,(u if top else l)[::-1]],np.r_[z,z[::-1]]))
            gs=prism(q,*sorted((side*.56,side*1.32)))
            for g in gs:
                for t in g['corners']:
                    n=t[:,3:6].mean(0)
                    if abs(n[0])>.95:
                        # Follow the same native pale panel projection as intact.
                        t[:,6]=.505+(t[:,2]-7.18)/1.80*.492
                        t[:,7]=.258+(t[:,1]+.78)/4.08*.596
            result+=gs
    # Narrow backing remnants; the center opens to the full, live carrier.
    result+=prism([[2.62,8.74],[2.62,8.98],[3.30,8.98],[3.30,8.74]],-.56,.56)
    result+=prism([[-.78,8.74],[-.78,8.98],[-.34,8.98],[-.34,8.74]],-.56,.56)
    # Bent strips grow from the broken cheek edges. Both sides and thickness are
    # present; no caps are authored for flying detached debris.
    for side in (-1,1):
        for offset,top in ((0,True),(.22,False)):
            p=np.array([[2.46,8.40],[2.57,8.62],[1.91,8.79],[1.66,8.64]]) if top else np.array([[.07,7.64],[.15,7.86],[.73,7.75],[.90,7.56]])
            gs=prism(p,*sorted((side*1.25,side*1.32)))
            for g in gs:
                a=g['corners'];taper=np.clip((2.46-a[:,:,1])/.8,0,1) if top else np.clip((a[:,:,1]-.15)/.75,0,1)
                a[:,:,0]+=side*(.22+offset)*taper
                g['material']=f.mesh.crc('pir_r_dmg3')
                for t in a:
                    n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);t[:,3:6]=n/np.linalg.norm(n)
            result+=gs
    return f.merge(result)


def hp_bytes(ns):
    result={}
    for file,name in f.component_map(ns).items():
        part=f.mesh.child(ns[0],file)
        for p,node in f.mesh.walk([part]):
            if '/hardpoints/' in p.lower() and node.blob:
                result[name+'/'+p.split('/Hardpoints/',1)[1]]=node.blob.hex()
    return result


def update_wire(ns):
    from rh_pir_elite_refine_damage import decoded_wire
    tr,_=f.audit.transforms(ns,('Sc_extend wing',0));lines=decoded_wire(ns,tr)
    transferred=[];root=[]
    for a,c in lines['Root']:
        line=np.array([a,c]);yz=line[:,1:3]
        if inside_polygon(np.r_[yz,yz.mean(0)[None,:]],frame_profile()).all():line[:,0]*=RIM_HALF/1.32
        root.append(line)
    for line in lines['Rh_tail_lod1']:
        line=line.copy();line[:,0]*=RIM_HALF/1.32;transferred.append(line)
    root+=transferred
    poly=np.array(json.loads((OUT/'geometry.json').read_text())['shell_profile'])
    tail=[]
    rings=[np.column_stack((np.full(len(poly),x),poly)) for x in (-1.32,1.32)]
    for ring in rings:tail.extend(zip(ring,np.roll(ring,-1,axis=0)))
    for a,c in zip(*rings):tail.append([a,c])
    lib=f.mesh.child(ns[0],'VMeshLibrary');names=f.component_map(ns)
    for owner,world_lines in [('Root',b.clean(root)),('Rh_tail_lod1',b.clean(tail))]:
        file=next(k for k,v in names.items() if v==owner);r,t=tr[file.lower()]
        local=(np.array(world_lines)-t)@r
        ps={b.key(q):q for q in local.reshape(-1,3)};keys=sorted(ps);lookup={k:i for i,k in enumerate(keys)}
        ref=f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'MultiLevel'),'Level0'),'VMeshPart')
        # Use the established tiny-triangle plus wire-only vertex-pool format.
        triangle=np.zeros((1,3,8));triangle[0,:,:3]=[[0,0,0],[.001,0,0],[0,.001,0]];triangle[0,:,5]=1
        blob,v=f.mesh.pack([dict(material=PALE,corners=triangle,unused=204)])
        raw=bytearray(blob);base=len(v)
        verts=np.zeros((len(keys),8));verts[:,:3]=np.array([ps[k] for k in keys]);verts[:,5]=1
        struct.pack_into('<H',raw,14,base+len(keys));raw+=verts.astype('<f4').tobytes()
        vn='tail_rim_wire_'+owner+'.vms';lib.children.append(f.folder(vn,f.mesh.Node('VMeshData',bytes(raw))))
        ids=[lookup[b.key(q)] for line in local for q in line]
        payload=struct.pack('<II4H',16,f.mesh.crc(vn),base,len(keys),len(ids),len(keys))+np.array(ids,'<u2').tobytes()
        f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'VMeshWire'),'VWireData').blob=payload
    return {'Root':len(root),'Rh_tail_lod1':len(tail),'retained_frame_owner':'Root'}


def export():
    data=json.loads((OUT/'geometry.json').read_text());header,source=load(OUT/'user_source.cmp')
    assert f.digest(LIVE)==data['source_sha256'],'New live user edits must be preserved'
    ns=copy.deepcopy(source);names=f.component_map(ns);tr,_=f.audit.transforms(ns,('Sc_extend wing',0))
    lib=f.mesh.child(ns[0],'VMeshLibrary')
    for file,name in names.items():
        ml=f.mesh.child(f.mesh.child(ns[0],file),'MultiLevel')
        ml.children=[n for n in ml.children if not n.name.startswith('Level') or n.name=='Level0']
        f.mesh.child(ml,'Switch2').blob=np.array([0,10000],'<f4').tobytes()
        if name not in ('Root','Rh_tail_lod1'):continue
        r,t=tr[file.lower()];gs=f.base.world(flatten_groups(data['parts'][name]),r.T,-r.T@t)
        blob,verts=f.mesh.pack(f.merge(gs));vn='tail_rim_'+name+'.vms'
        lib.children.append(f.folder(vn,f.mesh.Node('VMeshData',blob)))
        ref=f.mesh.child(f.mesh.child(f.mesh.child(ml,'Level0'),'VMeshPart'),'VMeshRef')
        ref.blob=f.fresh_ref(vn,blob,verts)
    wire=update_wire(ns)
    used={struct.unpack_from('<I',n.blob,4)[0] for p,n in f.mesh.walk(ns) if p.lower().endswith(('/vmeshref','/vwiredata'))}
    lib.children=[n for n in lib.children if f.mesh.crc(n.name) in used]
    salt=secrets.token_hex(6);mapping=b.salt_tree(ns,salt)
    target=OUT/'rh_pir_elite_tail_rim.cmp';target.write_bytes(f.mesh.write_tree(header,ns))
    ns=load(target)[1];assert hp_bytes(source)==hp_bytes(ns)
    for tag in ('Animation','Cons'):
        get=lambda a:f.mesh.child(a[0],tag) if tag=='Animation' else f.mesh.child(f.mesh.child(a[0],'Cmpnd'),tag)
        assert {p:n.blob for p,n in f.mesh.walk([get(source)])}=={p:n.blob for p,n in f.mesh.walk([get(ns)])}
    after=world(ns);before=world(source)
    for part in before:
        if part in ('Root','Rh_tail_lod1'):continue
        assert len(before[part])==len(after[part])
        for a,c in zip(before[part],after[part]):assert a['material']==c['material'] and np.allclose(a['corners'],c['corners'],atol=3e-6),part
    # The three connected drum meshes (shell and two inset faces) are untouched.
    drum=[]
    for comp in components(before['Root']):
        if comp['triangles'] in (160,138) and comp['bounds'][0][2]>2.5 and comp['bounds'][1][2]<6.6:
            drum += [(before['Root'][gi]['material'],before['Root'][gi]['corners'][ti]) for gi,ti in comp['indices']]
    assert len(drum)==436
    def key(mid,t):return (mid,tuple(np.round(t,5).ravel()))
    available=collections.Counter(key(g['material'],t) for g in after['Root'] for t in g['corners'])
    for mid,t in drum:assert available[key(mid,t)],'Drum changed'
    mats=f.audit.material_table([MAT,ENV]);limits=[]
    for p,n in f.mesh.walk(ns):
        assert n.name.lower() not in ('material library','texture library')
        if p.lower().endswith('/vmeshdata'):
            verts,groups,indices=f.audit.decode(n.blob)
            assert len(verts)<65536 and len(indices)<65536 and np.isfinite(verts).all()
            for mid,lo,hi,num,_ in groups:assert mid in mats and num%3==0 and 0<=lo<=hi<len(verts)
            limits.append(dict(vertices=len(verts),indices=len(indices)))
    # Static extended editor variant; native animated CMP above retains its rig.
    opened=copy.deepcopy(ns);tr,_=f.audit.transforms(opened,('Sc_extend wing',0));fixed=b''
    s64=lambda s:s.encode().ljust(64,b'\0')
    for file,name in f.component_map(opened).items():
        if name=='Root':continue
        r,t=tr[file.lower()];fixed+=s64('Root')+s64(name)+np.r_[t,r.ravel()].astype('<f4').tobytes()
    cons=f.mesh.child(f.mesh.child(opened[0],'Cmpnd'),'Cons');cons.children=[f.mesh.Node('Fix',fixed)]
    opened[0].children=[n for n in opened[0].children if n.name!='Animation']
    open_salt=secrets.token_hex(6);open_mapping=b.salt_tree(opened,open_salt)
    open_path=OUT/'rh_pir_elite_tail_rim_open.cmp';open_path.write_bytes(f.mesh.write_tree(header,opened))
    # Surviving-shell damage 3DB uses the existing receiving DpTail frame.
    damaged=damaged_shell(data);hp=f.hp_world(ns)['dptail'];hr=np.array(hp['orientation']);ht=np.array(hp['position'])
    cap=f.base.world(damaged,hr.T,-hr.T@ht);blob,verts=f.mesh.pack(cap)
    dh,dn=load(OUT/'native_tail_damage.3db');root=dn[0];damage_salt=secrets.token_hex(6);vn='rh_pir_tail_damage_'+damage_salt+'.vms'
    ref=f.fresh_ref(vn,blob,verts)
    root.children=[f.folder('VMeshLibrary',f.folder(vn,f.mesh.Node('VMeshData',blob))),
        f.folder('MultiLevel',f.mesh.Node('Switch2',np.array([0,10000],'<f4').tobytes()),f.folder('Level0',f.folder('VMeshPart',f.mesh.Node('VMeshRef',ref)))),
        f.folder('Hardpoints',f.folder('Fixed',f.folder('DpConnect',f.mesh.Node('Position',np.zeros(3,dtype='<f4').tobytes()),f.mesh.Node('Orientation',np.eye(3,dtype='<f4').tobytes()))))]
    cap_path=OUT/'rh_pir_elite_dmg_tail.3db';cap_path.write_bytes(f.mesh.write_tree(dh,dn))
    save(OUT/'review_data.json',dict(parts=after,damage=damaged,hardpoints=f.hp_world(load(open_path)[1]),
         cmp_sha256=f.digest(target),open_cmp_sha256=f.digest(open_path),damage_sha256=f.digest(cap_path)))
    save(OUT/'validation.json',dict(cmp_sha256=f.digest(target),open_cmp_sha256=f.digest(open_path),damage_sha256=f.digest(cap_path),
         source_sha256=f.digest(LIVE),hardpoint_records_preserved=len(f.hp_world(ns)),all_hp_bytes_preserved=True,
         drum_triangles_unchanged=len(drum),native_rig_bytes_unchanged=True,private_salt=salt,resources=mapping,
         open_salt=open_salt,open_resources=open_mapping,damage_salt=damage_salt,damage_private_resource=vn,
         wire=wire,mesh_limits=limits,triangles=sum(len(g['corners']) for gs in after.values() for g in gs),
         prototype_only=True,levels=1,main_sur_not_generated=True,installed=False))
    print('EXPORTED: animated and open prototype CMP; surviving tail damage 3DB; 436 drum triangles and all HP preserved')


def previews():
    from PIL import Image,ImageDraw
    from preview import render
    data=json.loads((OUT/'geometry.json').read_text());new={k:flatten_groups(v) for k,v in data['parts'].items()}
    old=world(load(OUT/'user_source.cmp')[1]);mats=f.audit.material_table([MAT,ENV])
    def pic(parts,cam,center,radius,size=720):
        front=[]
        for gs in parts.values():
            for g in gs:
                a=g['corners'];n=np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3]);keep=n@np.array(cam)>1e-9
                if keep.any():front.append(dict(g,corners=a[keep]))
        return render(front,mats,np.asarray(center),radius,cam,size,'texture')
    sheet=Image.new('RGB',(2160,1440),'#181d25');draw=ImageDraw.Draw(sheet)
    for row,(parts,label) in enumerate([(old,'BEFORE'),(new,'PROTOTYPE')]):
        for col,cam in enumerate([(1,0,0),(0,0,1),(1,.6,1)]):
            sheet.paste(pic(parts,cam,(0,1.1,6.2),4.65),(col*720,row*720));draw.text((col*720+15,row*720+15),label,fill='white')
    sheet.save(OUT/'comparison.png')
    pic(new,(-1,.55,1),(0,1,0),10.8,1200).save(OUT/'overview.png')
    if (OUT/'review_data.json').exists():
        review=json.loads((OUT/'review_data.json').read_text());new={k:flatten_groups(v) for k,v in review['parts'].items()}
        broken={k:v for k,v in new.items() if k!='Rh_tail_lod1'};broken['Damage']=flatten_groups(review['damage'])
        sheet=Image.new('RGB',(2160,1440),'#181d25');draw=ImageDraw.Draw(sheet)
        for row,(parts,label) in enumerate([(new,'INTACT TAIL'),(broken,'DAMAGED TAIL / FRAME SURVIVES')]):
            for col,cam in enumerate([(1,0,0),(0,0,1),(1,.6,1)]):
                sheet.paste(pic(parts,cam,(0,1.1,6.2),4.65),(col*720,row*720));draw.text((col*720+15,row*720+15),label,fill='white')
        sheet.save(OUT/'damage_comparison.png')


def handoff():
    report=json.loads((OUT/'validation.json').read_text());data=json.loads((OUT/'review_data.json').read_text())
    assert f.digest(OUT/'rh_pir_elite_tail_rim.cmp')==report['cmp_sha256']==data['cmp_sha256']
    assert f.digest(OUT/'rh_pir_elite_tail_rim_open.cmp')==report['open_cmp_sha256']
    assert f.digest(LIVE)==report['source_sha256']
    mats=f.audit.material_table([MAT,ENV]);used={g['material'] for gs in data['parts'].values() for g in gs}|{g['material'] for g in data['damage']}
    folder=OUT/'textures';folder.mkdir(exist_ok=True);material_info={}
    for mid in used:
        m=mats[mid];path=folder/(m['name']+'.png')
        if m['image'] is not None:m['image'].save(path)
        material_info[mid]=dict(name=m['name'],colour=np.asarray(m['colour'])[:3],
            image=str(path) if m['image'] is not None else None,texture=m['texture'])
    save(OUT/'materials.json',material_info)
    references=OUT/'references';references.mkdir(exist_ok=True);refs={}
    for i,name in enumerate(['H4wiM5','dmwPr7','quV8oC','1cLry6'],1):
        source=Path('C:/Users/Freel/AppData/Local/Temp')/('codex-clipboard-'+name+'.png')
        dest=references/('user_'+str(i)+'.png')
        if not dest.exists():dest.write_bytes(source.read_bytes())
        assert f.digest(dest)==f.digest(source);refs[dest.name]=dict(source=str(source),sha256=f.digest(dest))
    save(references/'manifest.json',refs)
    # The damage 3DB must reconstruct the reviewed surviving geometry at DpTail.
    from rh_concept_b_damage_reference import groups
    ns=load(OUT/'rh_pir_elite_tail_rim.cmp')[1];hp=f.hp_world(ns)['dptail']
    assembled=f.base.world(groups(OUT/'rh_pir_elite_dmg_tail.3db'),np.array(hp['orientation']),np.array(hp['position']))
    expected=f.merge(flatten_groups(data['damage']))
    for a,c in zip(assembled,expected):assert a['material']==c['material'] and np.allclose(a['corners'],c['corners'],atol=3e-6)
    for g in assembled:
        assert 'metal' not in mats[g['material']]['name'].lower()
        assert 'metal' not in mats[g['material']]['texture'].lower()
        a=g['corners'];uv=a[:,:,6:8];area=abs((uv[:,1,0]-uv[:,0,0])*(uv[:,2,1]-uv[:,0,1])-(uv[:,1,1]-uv[:,0,1])*(uv[:,2,0]-uv[:,0,0]))
        assert np.min(area)>1e-9,(mats[g['material']]['name'],float(np.min(area)))
    report.update(damage_anchor_verified=True,damage_external_materials_verified=True,source_still_unchanged=True,
                  preview_hashes={p.name:f.digest(p) for p in OUT.glob('*.png')})
    save(OUT/'validation.json',report)
    print('HANDOFF: external material references, source images and damage anchor verified')


def check():
    from rh_pir_elite_refine_damage import decoded_wire
    report=json.loads((OUT/'validation.json').read_text());blend=json.loads((OUT/'blender_check.json').read_text())
    assert blend['reopened'] and blend['cmp_sha256']==report['cmp_sha256']
    assert f.digest(OUT/'rh_pir_elite_tail_rim.blend')==blend['blend_sha256']
    assert f.digest(LIVE)==report['source_sha256']
    source=json.loads((OUT/'source_audit.json').read_text())
    for filename,expected in source['materials'].items():assert f.digest(Path(filename))==expected
    animated=load(OUT/'rh_pir_elite_tail_rim.cmp')[1];opened=load(OUT/'rh_pir_elite_tail_rim_open.cmp')[1]
    a=world(animated);c=world(opened,None)
    for name in a:
        for x,y in zip(a[name],c[name]):assert x['material']==y['material'] and np.allclose(x['corners'],y['corners'],atol=3e-6),name
    for ns in (animated,opened,load(OUT/'rh_pir_elite_dmg_tail.3db')[1]):
        for p,node in f.mesh.walk(ns):
            assert node.name.lower() not in ('material library','texture library')
            if p.lower().endswith('/vmeshdata'):
                v,gs,ids=f.audit.decode(node.blob);at=0
                for _,lo,hi,num,_ in gs:
                    indices=ids[at:at+num]+lo;at+=num
                    assert num%3==0 and indices.min()>=lo and indices.max()<=hi<len(v)
                assert at==len(ids)
    tr,_=f.audit.transforms(animated);wire=decoded_wire(animated,tr)
    assert len(wire['Root']) and len(wire['Rh_tail_lod1'])
    for name,digest in report['preview_hashes'].items():assert f.digest(OUT/name)==digest
    report.update(static_open_matches_animated_flight=True,index_ranges_valid=True,wire_indices_valid=True,
                  shared_mats_unchanged=True,blend_reopened=True)
    save(OUT/'validation.json',report)
    print('CHECKED: opened Blender, static/animated pose agreement, indices, wire ownership, external MATs, unchanged live CMP')


def save(path, data):
    path.write_text(json.dumps(data, default=b.v.hp.serial, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def load(path):
    return f.mesh.read_tree(path.read_bytes())


def world(ns, pose=('Sc_extend wing',0), level=0):
    names = f.component_map(ns)
    tr,_ = f.audit.transforms(ns,pose)
    return {names[k]:f.base.world(v,*tr[k.lower()]) for k,v in f.local_geometry(ns,level).items()}


def points(gs):
    return np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs])


def frame_profile():
    shift=np.array(json.loads((b.v.OUT/'build.json').read_text())['center_shift_native'])
    drop=json.loads((b.v.OUT.parent/'revision_07/checks.json').read_text())['tail_translation'][1]
    p=f.b.old.yz([[214,16],[148,16],[95,48],[95,124],[123,153],[207,153],
                  [207,133],[140,133],[116,112],[116,59],[154,36],[214,36]])
    p[:,0]+=drop
    return p+shift[1:]


def inside_polygon(q, poly, tolerance=1e-4):
    q=np.asarray(q);inside=np.zeros(q.shape[:-1],bool);edge=inside.copy()
    for a,c in zip(poly,np.roll(poly,-1,axis=0)):
        v=c-a;u=q-a;along=np.clip((u@v)/(v@v),0,1)
        edge |= np.linalg.norm(u-along[...,None]*v,axis=-1)<tolerance
        if abs(v[1])>1e-12:
            inside ^= ((a[1]>q[...,1])!=(c[1]>q[...,1])) & (q[...,0] < a[0]+v[0]*(q[...,1]-a[1])/v[1])
    return inside|edge


def frame_mask(ts):
    p=ts[...,:3];yz=p[...,1:3]
    samples=np.concatenate([yz,(yz+np.roll(yz,1,axis=1))/2,yz.mean(1)[:,None,:]],axis=1)
    return inside_polygon(samples,frame_profile()).all(1)&(np.max(abs(p[...,0]),axis=1)<1.321)


def selection():
    from PIL import Image,ImageDraw
    from preview import render
    ns=load(OUT/'user_source.cmp')[1];w=world(ns)
    mats=f.audit.material_table([MAT,ENV]);mats[1]=dict(name='selected',image=Image.new('RGB',(2,2),'#20eded'),colour=np.ones(3));mats[2]=dict(name='retained',image=Image.new('RGB',(2,2),'#777777'),colour=np.ones(3))
    gs=[];report={}
    for part,groups in w.items():
        report[part]=0
        for g in groups:
            a=g['corners'];mask=frame_mask(a) if part in ('Root','Rh_tail_lod1') else np.zeros(len(a),bool)
            report[part]+=int(mask.sum())
            for take,mid in [(mask,1),(~mask,2)]:
                if take.any():gs.append(dict(g,corners=a[take],material=mid))
    sheet=Image.new('RGB',(1800,600),'#181d25')
    for i,cam in enumerate([(1,0,0),(0,1,.001),(1,.6,1)]):sheet.paste(render(gs,mats,np.array([0,1,5.5]),5.5,cam,600,'texture'),(i*600,0))
    sheet.save(OUT/'frame_selection.png');print(report)
    save(OUT/'frame_selection.json',report)


def components(gs):
    tris = [(i,j,t) for i,g in enumerate(gs) for j,t in enumerate(g['corners'])]
    parent = list(range(len(tris)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    owners = {}
    for k,(_,_,t) in enumerate(tris):
        for p in t[:,:3]:
            key = tuple(p.round(4))
            if key in owners:parent[root(k)] = root(owners[key])
            else:owners[key]=k
    sets=collections.defaultdict(list)
    for i,entry in enumerate(tris):sets[root(i)].append(entry)
    result=[]
    for entries in sets.values():
        p=np.concatenate([t[:,:3] for _,_,t in entries])
        result.append(dict(triangles=len(entries),bounds=[p.min(0),p.max(0)],
                           indices=[[i,j] for i,j,_ in entries]))
    return sorted(result,key=lambda c:-c['triangles'])


def audit():
    OUT.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(ROOT).free>256*1024*1024
    sources = {'user_source.cmp':LIVE, 'native_rh_elite.cmp':NATIVE,
               'native_tail_damage.3db':NATIVE.with_name('rh_elite_dmg_tail.3db')}
    report={'sources':{},'models':{}}
    for name,src in sources.items():
        dst=OUT/name
        if dst.exists():assert f.digest(dst)==f.digest(src), ('Changed source',str(src))
        else:dst.write_bytes(src.read_bytes())
        report['sources'][name]=dict(path=str(src),sha256=f.digest(src))
    for label,name in [('current','user_source.cmp'),('native','native_rh_elite.cmp')]:
        ns=load(OUT/name)[1];parts=world(ns);entry={}
        for part,gs in parts.items():
            p=points(gs);entry[part]=dict(triangles=sum(len(g['corners']) for g in gs),bounds=[p.min(0),p.max(0)])
            if part in ('Root','Rh_tail_lod1'):
                entry[part]['components']=components(gs)
                print(label,part,[(c['triangles'],np.round(c['bounds'],3).tolist()) for c in entry[part]['components']],flush=True)
        report['models'][label]=entry
    report['materials']={str(p):f.digest(p) for p in (MAT,NATIVE_MAT,ENV) if p.exists()}
    save(OUT/'source_audit.json',report)
    print('PINNED',report['sources'],flush=True)


def reference():
    from PIL import Image, ImageDraw
    from preview import render
    from rh_concept_b_damage_reference import groups
    mats=f.audit.material_table([MAT,NATIVE_MAT,ENV])
    sheet=Image.new('RGB',(1800,1200),'#181d25');draw=ImageDraw.Draw(sheet)
    ns=load(OUT/'native_rh_elite.cmp')[1];w=world(ns)
    hp=f.hp_world(ns)['dptail'];cap=load(OUT/'native_tail_damage.3db')[1]
    leaves={p.lower():n.blob for p,n in f.mesh.walk(cap)}
    ct=np.frombuffer(next(v for p,v in leaves.items() if p.endswith('/dpconnect/position')),'<f4')
    cr=np.frombuffer(next(v for p,v in leaves.items() if p.endswith('/dpconnect/orientation')),'<f4').reshape(3,3)
    hr=np.array(hp['orientation']);ht=np.array(hp['position'])
    damage=f.base.world(groups(OUT/'native_tail_damage.3db'),hr@cr.T,ht-hr@cr.T@ct)
    for row,(parts,label) in enumerate([(w,'NATIVE INTACT'),({k:v for k,v in w.items() if k!='Rh_tail_lod1'}|{'Damage':damage},'NATIVE DAMAGED')]):
        gs=[g for v in parts.values() for g in v]
        for col,cam in enumerate([(1,0,0),(0,0,1),(1,.5,1)]):
            front=[]
            for g in gs:
                t=g['corners'];n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]);mask=n@np.array(cam)>1e-9
                if mask.any():front.append(dict(g,corners=t[mask]))
            sheet.paste(render(front,mats,np.array([0,1.6,4.5]),4.5,cam,600,'texture'),(col*600,row*600))
            draw.text((col*600+12,row*600+12),label,fill='white')
    sheet.save(OUT/'native_construction.png')
    for name,gs in w.items():
        if name not in ('Root','Rh_tail_lod1'):continue
        p=points(gs);mask=(p[:,1]>3.6)&(p[:,2]>1.0)
        print(name,'upper frame X',np.unique(np.round(p[mask,0],4)).tolist())
    print('MATERIALS',[(hex(k),v['name']) for k,v in mats.items() if k in {g['material'] for gs in world(load(OUT/'user_source.cmp')[1]).values() for g in gs}])
    save(OUT/'native_damage_world.json',damage)


if __name__=='__main__':
    if '--geometry' in sys.argv:geometry();previews()
    elif '--export' in sys.argv:export();previews()
    elif '--handoff' in sys.argv:handoff()
    elif '--check' in sys.argv:check()
    elif '--selection' in sys.argv:selection()
    elif '--reference' in sys.argv:reference()
    else:audit()
