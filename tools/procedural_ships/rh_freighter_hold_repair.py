"""Repair the hold surround, preserving the user's latest running/dock lights."""
import copy,json,shutil,secrets,struct,sys
from pathlib import Path
import numpy as np
import rh_freighter_final as d
from rh_freighter_far_lod import named,signature,wire_lines
from rh_pir_elite_build import salt_tree
f=d.f;OUT=d.OUT/'hold_repair';PREV=d.OUT/'hold_damage'
LIVE=d.GAME/'DATA/ships/rheinland/rh_pir_freighter/rh_pir_freighter.cmp'
CANON=d.GAME/'Assets/Pythonlancer/assets/ships/rheinland/rh_pir_freighter'

def far_surround():
    """42-triangle closed distant body, with a narrow rectangular cargo opening.

    Keep broad outside surfaces independent of the hold width. Four continuous
    ledges join the opening to the old outline. The distant nose cap is a
    triangle beneath the separate cockpit, saving two faces against 44.
    """
    from rh_freighter_min_lod import B,project
    b=B();sections=[(-8.416,1.98,-2.079,.766),(-4.1,3.2,-4.,3.81),
                    (5.72,3.2,-4.,3.81),(8.30,2.04,-2.62,1.78)]
    rings=[np.array([[-w,bot,z],[w,bot,z],[w,top,z],[-w,top,z]]) for z,w,bot,top in sections]
    rings[0][:2,0]=0
    def face(ps,normal,mid=0):
        clean=[]
        for p in ps:
            if not any(np.allclose(p,q,atol=1e-7) for q in clean):clean.append(p)
        if len(clean)>2:b.face(np.array(clean),mid,normal=normal)
    for i,(a,c) in enumerate(zip(rings,rings[1:])):
        for j in range(4):
            if i==1 and j==2:continue
            n=([0,-1,0],[1,0,0],[0,1,0],[-1,0,0])[j]
            face([a[j],a[(j+1)%4],c[(j+1)%4],c[j]],n)
    face(rings[0],[0,0,-1]);face(rings[-1],[0,0,1])
    exterior=project(b.groups(),'Root');exterior[0]['material']=f.mesh.crc('rh_pir_freighter_projection_lod')
    b=B();b.allow_bay_metal=True
    rim=np.array([rings[1][3],rings[1][2],rings[2][2],rings[2][3]])
    inner=np.array([[-1.1,3.81,-2.51],[1.1,3.81,-2.51],[1.1,3.81,4.39],[-1.1,3.81,4.39]])
    floor=inner.copy();floor[:,1]=.355
    face(floor,[0,1,0],3821786036)
    for i in range(4):
        j=(i+1)%4;face([rim[i],rim[j],inner[j],inner[i]],[0,1,0],4138378680)
        ps=np.array([inner[i],inner[j],floor[j],floor[i]]);n=floor.mean(0)-ps.mean(0);n[1]=0
        face(ps,n,3821786036)
    for g in b.groups():
        t=g['corners']
        if g['material']==4138378680:
            # Four authored quads, each retaining one calm native panel crop.
            for start in range(0,len(t),2):
                q=t[start:start+2];co=q[:,:,[0,2]];lo=co.min((0,1));span=np.ptp(co,axis=(0,1))
                q[:,:,6:8]=[.51,.27]+(co-lo)/span*[.48,.57]
        else:
            for tri in t:
                axis=np.argmax(np.abs(tri[0,3:6]));axes=(0,2) if axis==1 else (2,1) if axis==0 else (0,1)
                tri[:,6:8]=tri[:,list(axes)]/2.4
        exterior.append(g)
    assert sum(len(a['corners']) for a in exterior)==42
    edges={}
    for group in exterior:
        for tri in group['corners']:
            points=[tuple(v.round(5)) for v in tri[:,:3]]
            for a,c in zip(points,points[1:]+points[:1]):edges.setdefault(tuple(sorted((a,c))),[]).append((a,c))
    assert all(len(v)==2 and v[0]!=v[1] for v in edges.values()),'Distant cargo closure/winding'
    return exterior

def repair_distant(data):
    original=json.loads((OUT/'input.json').read_text())['original_levels']
    core=far_surround()
    gs=copy.deepcopy(original[1]['Root']);found=0
    for g in gs:
        if len(g['corners'])==678:
            t=np.array(g['corners']);g['corners']=np.concatenate((t[:32],t[294:-12]));found+=1
    assert found==1
    data['roots'][1]=gs+core
    gs=copy.deepcopy(original[2]['Root']);assert len(gs)==1
    gs[0]['corners']=np.array(gs[0]['corners'])[36:]
    data['roots'][2]=gs+core
    return data

def prepare():
    assert shutil.disk_usage(d.ROOT).free>4*1024**3
    OUT.mkdir(exist_ok=True)
    raw=LIVE.read_bytes();source=OUT/'user_source.cmp'
    if source.exists():assert source.read_bytes()==raw,'User edited CMP again; do not overwrite pinned source'
    else:source.write_bytes(raw)
    _,ns=d.tree(source);_,old=d.tree(CANON/'rh_pir_freighter.cmp')
    for lv in range(3):assert signature(ns,lv)==signature(old,lv),'Source has geometry edits: inspect before rebuilding'
    hp=d.hardpoints(ns,('Sc_extend wing',0));baseline=d.hardpoints(old,('Sc_extend wing',0))
    changes={k:dict(before=baseline.get(k),after=v) for k,v in hp.items() if baseline.get(k,{}).get('leaves')!=v['leaves']}
    d.dump(OUT/'user_hardpoints.json',dict(source=str(LIVE),sha256=f.digest(source),all_hardpoints=hp,changes=changes))
    old_input=json.loads((PREV/'input.json').read_text())
    d.dump(OUT/'input.json',dict(source_sha256=f.digest(source),levels=[d.world(ns,('Sc_extend wing',0),lv) for lv in range(3)],
        original_levels=old_input['levels'],materials=old_input['materials'],scene=old_input['scene'],hardpoints=hp,
        shared_mat_sha256=f.digest(d.MAT)))
    # Exact UV ownership is available from the original reconstruction, including
    # authored fore/aft cornices. The new cargo floor will be built separately.
    import rh_freighter_uv15 as u
    u.base.configure();cfg=json.loads((d.PREVIOUS/'cornice_symmetry.json').read_text());u.MIRROR_Z=cfg['plane_z']
    ref=json.loads((u.REFERENCE/'native_fore.json').read_text())[1];shape=cfg['front']
    ts=np.array([t['corners'] for t in ref['triangles'] if t['material']=='pir_r_panel01_256' and t['source_triangle'] in (93,94)])
    z0=ts[:,:,2].min();ts[:,:,0]-=shape['source_center_x'];ts[:,:,1]=u.TOP;ts[:,:,2]+=shape['top_z'][0]-z0;ts[:,:,3:6]=[0,1,0]
    u.TOP_GROUP=dict(material=u.uv.P,corners=ts)
    ribs=json.loads((d.PREVIOUS/'aft_rib_geometry.json').read_text())['ribs']
    u.aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})
    raw=json.loads((d.PREVIOUS/'mechanical_geometry.json').read_text())['objects']
    core=next(o for o in raw if o['name'].startswith('Continuous hull'))
    d.dump(OUT/'original_core.json',u.core_map(core['name'],core['groups']))
    print('PINNED',f.digest(source),'USER HP CHANGES',list(changes),flush=True)

def export():
    header,ns=d.tree(OUT/'user_source.cmp');before=copy.deepcopy(ns)
    data=repair_distant(json.loads((OUT/'geometry.json').read_text()));d.dump(OUT/'export_geometry.json',data)
    names=f.component_map(ns);tr,_=f.audit.transforms(ns,('Sc_extend wing',0))
    file=next(k for k,v in names.items() if v=='Root');r,t=tr[file.lower()];lib=f.mesh.child(ns[0],'VMeshLibrary')
    for lv,gs in enumerate(data['roots']):
        local=f.base.world(d.packed(gs),r.T,-r.T@t);blob,vs=f.mesh.pack(f.merge(local));vn='rpf_hold_surround_'+str(lv)+'.vms'
        lib.children.append(f.folder(vn,f.mesh.Node('VMeshData',blob)))
        level=f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'MultiLevel'),'Level'+str(lv))
        f.mesh.child(f.mesh.child(level,'VMeshPart'),'VMeshRef').blob=f.fresh_ref(vn,blob,vs)
    used={struct.unpack_from('<I',n.blob,4)[0] for p,n in f.mesh.walk(ns) if p.lower().endswith(('/vmeshref','/vwiredata'))}
    lib.children=[n for n in lib.children if f.mesh.crc(n.name) in used]
    salt=secrets.token_hex(6);mapping=salt_tree(ns,salt)
    path=OUT/'rh_pir_freighter.cmp';path.write_bytes(f.mesh.write_tree(header,ns));_,ns=d.tree(path)
    hp=d.hardpoints(ns,('Sc_extend wing',0));ohp=d.hardpoints(before,('Sc_extend wing',0));assert hp.keys()==ohp.keys()
    for k,v in hp.items():assert v['owner']==ohp[k]['owner'] and v['leaves']==ohp[k]['leaves'],k
    for part,a in wire_lines(before).items():assert np.allclose(a,wire_lines(ns)[part],atol=2e-5),part
    for lv in range(3):
        for part,a in signature(before,lv).items():
            if part!='Root':assert a==signature(ns,lv)[part]
    for tag in ('Animation','Cons'):
        sub=lambda a:f.mesh.child(a[0],tag) if tag=='Animation' else f.mesh.child(f.mesh.child(a[0],'Cmpnd'),tag)
        leaves=lambda a:{p:n.blob for p,n in f.mesh.walk([sub(a)])}
        assert leaves(before)==leaves(ns)
    mats=f.audit.material_table([d.MAT,d.ENV]);limits=[]
    for p,n in f.mesh.walk(ns):
        assert n.name.lower() not in ('texture library','material library')
        if p.lower().endswith('/vmeshdata'):
            v,gs,ids=f.audit.decode(n.blob);assert len(v)<65536 and len(ids)<65536 and np.isfinite(v).all()
            at=0
            for mid,lo,hi,num,_ in gs:
                assert mid in mats and num%3==0;ii=ids[at:at+num]+lo;at+=num
                assert ii.min()>=lo and ii.max()<=hi<len(v)
            limits.append(dict(vertices=len(v),indices=len(ids)))
    roots=[d.world(ns,('Sc_extend wing',0),lv)['Root'] for lv in range(3)]
    for authored,actual in zip(data['roots'],roots):
        a=f.merge(d.packed(authored));b=f.merge(actual);assert len(a)==len(b)
        for x,y in zip(a,b):assert x['material']==y['material'] and np.allclose(x['corners'],y['corners'],atol=3e-5)
    opened=copy.deepcopy(ns)
    for p,n in f.mesh.walk(opened):
        if p.lower().endswith('/cons/pris'):
            raw=bytearray(n.blob)
            for at in range(0,len(raw),208):
                v=np.frombuffer(raw,'<f4',20,at+128).copy();v[:3]+=v[15:18];raw[at+128:at+208]=v.tobytes()
            n.blob=bytes(raw)
    opened[0].children=[n for n in opened[0].children if n.name.lower()!='animation'];osalt=secrets.token_hex(6);omap=salt_tree(opened,osalt)
    (OUT/'rh_pir_freighter_review_open.cmp').write_bytes(f.mesh.write_tree(header,opened))
    counts=[sum(len(g['corners']) for gs in named(ns,lv).values() for g in gs) for lv in range(3)];assert counts[2]<=500
    d.dump(OUT/'exported_roots.json',dict(cmp_sha256=f.digest(path),roots=roots))
    d.dump(OUT/'validation.json',dict(cmp_sha256=f.digest(path),source_sha256=f.digest(OUT/'user_source.cmp'),
        counts=counts,all_hp_bytes_preserved=True,wire_preserved=True,native_animation_bytes_preserved=True,
        private_salt=salt,resources=mapping,review_salt=osalt,review_resources=omap,mesh_limits=limits,
        damage_sur_materials='Existing files unchanged',distant_body_triangles=42,distant_body_closed=True,
        distant_external_decks_not_squeezed=True,installed=False))
    print('EXPORTED',counts,'ALL USER HP BYTES PRESERVED',flush=True)

def verify_delivery():
    path=OUT/'rh_pir_freighter.cmp';sha=f.digest(path)
    reports={k:json.loads((OUT/(k+'.json')).read_text()) for k in ('validation','motion_check','preview_manifest')}
    assert all(r['cmp_sha256']==sha for r in reports.values())
    assert reports['validation']['all_hp_bytes_preserved'] and not reports['motion_check']['collisions']
    assert reports['motion_check']['blend_reopened']
    assert len(reports['motion_check']['single_surface_rim_samples'])==12
    assert all(a['visible_layers']==1 for a in reports['motion_check']['single_surface_rim_samples'])
    assert len(reports['motion_check']['both_end_panels_coverage'])==12
    for name,digest in reports['preview_manifest']['images'].items():assert f.digest(OUT/name)==digest
    source=json.loads((OUT/'input.json').read_text())
    assert f.digest(LIVE)==source['source_sha256'],'New user edit: preserve it before offering this revision'
    assert f.digest(d.MAT)==source['shared_mat_sha256'],'Shared MAT changed: recheck exported materials'
    dependencies={}
    for p in sorted(CANON.iterdir()):
        if p.suffix.lower() not in ('.sur','.3db'):continue
        game=LIVE.parent/p.name;assert f.digest(p)==f.digest(game),str(game)
        dependencies[p.name]=dict(sha256=f.digest(p),source=str(p),game=str(game),unchanged=True)
    outputs={p.name:dict(sha256=f.digest(p),bytes=p.stat().st_size) for p in
             (path,OUT/'rh_pir_freighter_review_open.cmp',OUT/'rh_pir_freighter_review.blend')}
    d.dump(OUT/'delivery_manifest.json',dict(installed=False,game_cmp_unchanged=True,
        user_source_sha256=source['source_sha256'],outputs=outputs,dependencies=dependencies,
        shared_mat=dict(path=str(d.MAT),sha256=source['shared_mat_sha256'],unchanged=True),
        deployment='Offline only; installation is controlled by the user under the latest supplied AGENTS.md',
        triangle_counts=reports['validation']['counts'],hardpoints_preserved=68))
    print('DELIVERY VERIFIED',sha,'GAME FILES UNCHANGED',flush=True)

if __name__=='__main__':
    if '--export' in sys.argv:export()
    elif '--verify' in sys.argv:verify_delivery()
    else:prepare()
