"""Offline fighter LODs, per-part static wire, survivor assets and fresh salts."""
import copy,json,secrets,struct,sys
import numpy as np
from scipy.spatial import ConvexHull
import rh_fighter_final as d
import rh_concept_b_final_damage as damage
from rh_pir_elite_build import salt_tree
f=d.f

def atlas_png():
    from PIL import Image
    from scipy.ndimage import distance_transform_edt
    raw=Image.new('RGB',(4096,4096),(100,95,85))
    for views in d.read('projectors.json').values():
        for v in views:
            a=np.array(Image.open(d.OUT/v['image']).convert('RGBA'));valid=a[:,:,3]>100;assert valid.any()
            nn=distance_transform_edt(~valid,return_distances=False,return_indices=True)
            raw.paste(Image.fromarray(a[nn[0],nn[1],:3]),tuple(k*512 for k in v['tile']))
    raw.resize((2048,2048),Image.Resampling.LANCZOS).save(d.OUT/(d.ATLAS+'.png'))

def atlas_mat():
    path=d.OUT/(d.ATLAS+'.dds');png=path.with_suffix('.png');assert path.stat().st_mtime>=png.stat().st_mtime
    raw=path.read_bytes();assert raw[:4]==b'DDS ' and raw[84:88]==b'DXT1' and struct.unpack_from('<I',raw,28)[0]==12
    header,_=d.tree(d.MAT);mat=f.folder(d.ATLAS,f.textnode('Type','DcDt'),f.mesh.Node('Dc',np.ones(3,'<f4').tobytes()),f.textnode('Dt_name',d.ATLAS+'.tga'))
    ns=[f.folder('\\',f.folder('Material library',mat),f.folder('Texture library',f.folder(d.ATLAS+'.tga',f.mesh.Node('MIPS',raw))))]
    target=d.ASSETS/'rh_pir_fighter_lods.mat';target.write_bytes(f.mesh.write_tree(header,ns))
    d.dump(d.OUT/'atlas.json',dict(material=d.ATLAS,material_crc=f.mesh.crc(d.ATLAS),sha256=f.digest(target),size=2048,mips=12,format='DXT1',source_png_sha256=f.digest(png),projection_sources=d.read('projection_sources.json')))

def convex(gs,limit):
    p=np.unique(d.points(gs).round(5),axis=0);p=p[ConvexHull(p).vertices]
    chosen=list(dict.fromkeys([int(np.argmax(p[:,a]*s)) for a in range(3) for s in (-1,1)]))
    if len(chosen)<4:chosen=list(range(min(len(p),4)))
    while len(chosen)<min(len(p),limit):
        cv=ConvexHull(p[chosen]);distance=(p@cv.equations[:,:3].T+cv.equations[:,3]).max(1);distance[chosen]=-1
        if distance.max()<1e-5:break
        chosen.append(int(distance.argmax()))
    p=p[chosen];cv=ConvexHull(p);ts=[]
    for ids,eq in zip(cv.simplices,cv.equations):
        q=p[ids];normal=np.cross(q[1]-q[0],q[2]-q[0])
        if normal@eq[:3]<0:q=q[[0,2,1]]
        t=np.zeros((3,8));t[:,:3]=q;t[:,3:6]=eq[:3];ts.append(t)
    return [dict(material=0,corners=np.array(ts),unused=204)]

def project(gs,name):
    views=d.read('projectors.json')[name];ts=[]
    for g in gs:
        for t in np.array(g['corners'],float):
            n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=np.linalg.norm(n);p=max(views,key=lambda a:n@a['normal']);co=t[:,:3]-p['center'];x,y=p['tile']
            t[:,6]=(x+co@p['u']/p['scale']+.5)/8;t[:,7]=(y+.5-co@p['v']/p['scale'])/8;ts.append(t)
    return [dict(material=f.mesh.crc(d.ATLAS),corners=np.array(ts),unused=204)]

def far():
    data=d.read('blender_input.json');obs={o['name']:o['groups'] for o in data['original_objects']};near={o['name']:o['groups'] for o in data['objects']}
    main=[]
    for n in ('Root','Port_carved_flank','Starboard_carved_flank','Sculpted_roof_shoulders','Native_cabin_transition','Tapered_lower_receiver','Stern_receiver_fascia'):main+=obs[n]
    root=convex(main,30)+convex(obs['Native_cabin'],20)+convex(obs['Armored_transverse_drum'],34)
    for label in ('Port','Starboard'):root+=convex(obs[label+'_integrated_engine_seat'],12)
    out={'Root':project(root,'Root')}
    for name,gs in near.items():
        if name=='Root':continue
        if name.endswith('_wing_mesh'):out[name]=project(convex(gs,20),name)
        elif name.endswith('_engine_lod1'):out[name]=project(convex(gs,18),name)
        elif name=='glass_lod1':
            # The distant closed cockpit shell uses the photographed glazing.
            t=np.array(gs[0]['corners'][:1],float);t[:,:,:3]=np.array([[[0,-2,-6],[.001,-2,-6],[0,-2.001,-6]]])-data.get('origin_offset',[0,0,0]);out[name]=[dict(gs[0],corners=t)]
        elif '_baydoor_' in name:out[name]=d.packed(gs)
        else:
            out[name]=convex(gs,8)
            # Small mechanism proxy uses a native exterior panel, not the hold.
            for g in out[name]:g['material']=f.mesh.crc('pir_r_panel01_256');g['corners'][...,6:]=[.65,.55]
    count=sum(len(g['corners']) for gs in out.values() for g in gs);assert count<=500,count
    d.dump(d.OUT/'minimum_world.json',out);print('FAR LOD',count,flush=True);return out

def wire(nodes,far):
    names=f.component_map(nodes);library=f.mesh.child(nodes[0],'VMeshLibrary');out={}
    for file,name in names.items():
        gs=far[name];hidden=name=='glass_lod1' or '_baydoor_' in name or name.endswith(('_wing_mesh','_wing_slide'))
        if name.endswith('_wing_lod1'):gs=far[name.replace('_lod1','_mesh')]
        blob,v=f.mesh.pack(f.merge(gs));bw=f.clean_feature_wire(blob,0,angle=38);ids=np.frombuffer(bw,'<u2',offset=16)
        lines=[] if hidden else [q for q in v[ids,:3].reshape(-1,2,3) if np.linalg.norm(q[1]-q[0])>.10]
        # Far proxy's cabin and body are separate shells: their perimeter lines
        # explicitly retain the neck/cockpit break in the target HUD.
        verts={}
        for line in lines:
            for p in line:verts.setdefault(tuple(p.round(5)),len(verts))
        # A valid draw triangle plus unused backing vertices is the native wire convention.
        one=v[:3].copy();one[:,3:6]=[0,1,0];valid=np.zeros((1,3,8));valid[0]=one
        vb,vv=f.mesh.pack([dict(material=gs[0]['material'],corners=valid,unused=204)])
        base=len(vv);extra=np.zeros((len(verts),8),'<f4');extra[:,:3]=list(verts) if verts else np.empty((0,3));extra[:,4]=1
        raw=bytearray(vb);struct.pack_into('<H',raw,14,base+len(extra));raw+=extra.tobytes();vname='rhff_wire_'+name+'.vms'
        library.children.append(f.folder(vname,f.mesh.Node('VMeshData',bytes(raw))))
        ii=[verts[tuple(p.round(5))] for line in lines for p in line]
        payload=struct.pack('<II4H',16,f.mesh.crc(vname),base,len(verts),len(ii),len(verts))+np.array(ii,'<u2').tobytes()
        part=f.mesh.child(nodes[0],file);part.children=[n for n in part.children if n.name!='VMeshWire'];part.children.append(f.folder('VMeshWire',f.mesh.Node('VWireData',payload)))
        out[name]=dict(edges=len(lines),world=np.array(lines))
    d.dump(d.OUT/'wire.json',dict(parts=out,pose='static flight',per_part=True,empty_animated_child_wires=True))

def simple(zone,levels):
    header,_=d.tree(d.SOURCE/'original.cmp');salt=secrets.token_hex(6)
    library=f.folder('VMeshLibrary');multilevel=f.folder('MultiLevel',f.mesh.Node('Switch2',np.array([0,180,550,10000],'<f4').tobytes()))
    resources={};counts=[]
    for i,gs in enumerate(levels):
        name='rhff_damage_'+zone+'_lod'+str(i)+'_'+salt+'.vms'
        blob,v=f.mesh.pack(f.merge(gs));resources[name]=f.mesh.crc(name)
        library.children.append(f.folder(name,f.mesh.Node('VMeshData',blob)))
        multilevel.children.append(f.folder('Level'+str(i),f.folder('VMeshPart',f.mesh.Node('VMeshRef',f.fresh_ref(name,blob,v)))))
        counts.append(sum(len(g['corners']) for g in gs))
    assert len(levels)==3
    root=f.folder('\\',library,multilevel,
        f.folder('Hardpoints',f.folder('Fixed',f.folder('DpConnect',f.mesh.Node('Position',np.zeros(3,'<f4').tobytes()),f.mesh.Node('Orientation',np.eye(3,dtype='<f4').tobytes())))))
    path=d.ASSETS/('rh_pir_fighter_dmg_'+zone+'.3db');path.write_bytes(f.mesh.write_tree(header,[root]))
    tris=np.concatenate([g['corners'][...,:3] for g in levels[0]]);lo=tris.min((0,1));hi=tris.max((0,1));cuts=np.linspace(lo[2]-.001,hi[2]+.001,5)
    hs=damage.hull_regions(tris,0,[[(2,a,b)] for a,b in zip(cuts,cuts[1:])]);surf,lo,hi=damage.sur.encode_surface(hs)
    path.with_suffix('.sur').write_bytes(b'vers'+struct.pack('<fII',2,0,3)+b'!fxd'+b'exts'+struct.pack('<6f',*lo,*hi)+b'surf'+struct.pack('<I',len(surf))+surf)
    return dict(file=path.name,sha256=f.digest(path),triangles=counts[0],lod_triangles=counts,switches=[0,180,550,10000],salt=salt,resources=resources)

def build_damage(ns):
    hp=d.hardpoints(ns,('Sc_extend wing',0));records=[]
    lods=d.read('damage_lods_world.json');check=d.read('damage_lods_check.json')
    assert check['source_damage_sha256']==f.digest(d.OUT/'damage_world.json')
    assert check['source_geometry_sha256']==f.digest(d.OUT/'blender_input.json')
    authored={o['name']:o['groups'] for o in d.read('blender_input.json')['objects']}
    for zone,raw in d.read('damage_world.json').items():
        if zone.endswith('_wing'):raw=raw+authored[zone+'_lod1']+authored[zone+'_slide']
        h=hp[('DpRHF_'+zone).lower()];r=np.array(h['orientation']);t=np.array(h['position'])
        local=[f.base.world(d.packed(gs),r.T,-r.T@t) for gs in [raw,*lods[zone]]]
        records.append(dict(zone=zone,part=d.PARTS[zone],hardpoint=h['name'],position=h['position'],archetype='rh_pir_fighter_dmg_'+zone+'_cap',**simple(zone,local)))
    return records

def damage_only():
    data=d.read('build.json');path=d.ASSETS/'rh_pir_fighter.cmp'
    assert data['cmp_sha256']==f.digest(path)
    assert data['review_sha256']==f.digest(d.OUT/'rh_pir_fighter_review_open.cmp'),'Import manual HP changes first'
    _,ns=d.tree(path);data['damage']=build_damage(ns);d.dump(d.OUT/'build.json',data)
    print('DAMAGE ASSEMBLED; intact CMP, SUR and user HPs unchanged',flush=True)

def build():
    review=d.OUT/'rh_pir_fighter_review_open.cmp'
    if review.exists() and (d.OUT/'user_hardpoint_source.json').exists():
        previous=d.read('build.json')['review_sha256'] if (d.OUT/'build.json').exists() else ''
        assert f.digest(review) in (previous,d.read('user_hardpoint_source.json')['sha256']), 'Review HPs changed during build; import them before overwriting'
    header,ns=d.tree(d.OUT/'authoring_animated.cmp');names=f.component_map(ns);atlas=f.mesh.crc(d.ATLAS)
    distant=far();medium=d.read('medium_world.json');levels=[f.local_geometry(ns)]
    for lv in (medium,distant):levels.append({file:[dict(g,material=g['material'] or atlas,corners=np.array(g['corners'],float)) for g in lv[name]] for file,name in names.items()})
    f.write_geometry(ns,levels)
    for file in names:f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'MultiLevel'),'Switch2').blob=np.array([0,180,550,10000],'<f4').tobytes()
    hp=d.hardpoints(ns,('Sc_extend wing',0));records=build_damage(ns)
    wire(ns,distant);salt=secrets.token_hex(6);mapping=salt_tree(ns,salt);path=d.ASSETS/'rh_pir_fighter.cmp';path.write_bytes(f.mesh.write_tree(header,ns))
    # Static extended editor model keeps the exact same HPs in world space.
    op=copy.deepcopy(ns);tr,_=f.audit.transforms(op,('Sc_extend wing',0));fix=[]
    for file,name in f.component_map(op).items():
        if name=='Root':continue
        r,t=tr[file.lower()];fix.append(d.s64('Root')+d.s64(name)+np.r_[t,r.ravel()].astype('<f4').tobytes())
    f.mesh.child(f.mesh.child(op[0],'Cmpnd'),'Cons').children=[f.mesh.Node('Fix',b''.join(fix))];op[0].children=[n for n in op[0].children if n.name!='Animation']
    osalt=secrets.token_hex(6);omap=salt_tree(op,osalt);review=d.OUT/'rh_pir_fighter_review_open.cmp';review.write_bytes(f.mesh.write_tree(header,op))
    d.dump(d.OUT/'build.json',dict(origin_offset=d.read('blender_input.json').get('origin_offset',[0,0,0]),cmp_sha256=f.digest(path),review_sha256=f.digest(review),salt=salt,resources=mapping,review_salt=osalt,review_resources=omap,
        damage=records,hardpoints=len(hp),lod_triangles=[sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in levels],external_materials=True,installed=False))
    print('ASSEMBLED',path,flush=True)

if __name__=='__main__':
    if '--atlas-png' in sys.argv:atlas_png()
    elif '--atlas-mat' in sys.argv:atlas_mat()
    elif '--damage-only' in sys.argv:damage_only()
    else:build()
