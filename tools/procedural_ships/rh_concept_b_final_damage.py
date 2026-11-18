"""Geometry-specific break surfaces, native DpConnect assets and SUR assembly."""
import collections
import copy
import importlib.util
import json
from pathlib import Path
import struct as S
import sys
import numpy as np
from scipy.spatial import ConvexHull
import rh_concept_b_final as f

b,mesh,audit=f.b,f.mesh,f.audit
OUT=f.OUT
spec=importlib.util.spec_from_file_location('rh_sur_writer',Path(__file__).resolve().parents[1]/'train_sur/build.py')
sur=importlib.util.module_from_spec(spec);sys.modules[spec.name]=sur;spec.loader.exec_module(sur)


def rupture(loop,normal,depth=.22,seed=0,tail=False):
    """Authored torn sheet perimeter, recessed dark machinery and broken ribs."""
    p=np.array(loop,float);normal=mesh.unit(np.asarray(normal,float))
    center=p.mean(0)
    outer=p+normal*.008
    inner=center+(p-center)*.70
    # Irregular edge heights are deterministic; no dense spikes or decorative bolts.
    offsets=np.array([.75,1,.45,.85,.55,1.10,.65,.90])
    inner+=normal*(depth*offsets[(np.arange(len(p))+seed)%len(offsets)])[:,None]
    back=center+(p-center)*.68-normal*.045
    builder=b.Builder();builder.part='damage'
    damage=mesh.crc('pir_r_dmg3');equip=mesh.crc('Equip_genD')
    def quad(q,material,normal,uv):
        # Torn edges are deliberately nonplanar; triangulate before ear clipping.
        for ids in ((0,1,2),(0,2,3)):
            builder.explicit(np.array(q)[list(ids)],material,(0,0,1,1),normal,np.array(uv)[list(ids)])
    # Original rh_pir_elite caps use the light-to-charred vertical gradient of
    # pir_r_dmg3 across the torn skin, and the TOP LEFT machinery of Equip_gen.
    # One perimeter chart, shared across triangles: never fit the whole atlas
    # independently to every little edge triangle.
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1))]/2.2
    for i in range(len(p)):
        j=(i+1)%len(p)
        u,v=arc[i],arc[i+1]
        quad([outer[i],outer[j],inner[j],inner[i]],damage,normal,[[u,.10],[v,.10],[v,.72],[u,.72]])
        n=mesh.unit(center-(p[i]+p[j])/2)
        quad([inner[i],inner[j],back[j],back[i]],damage,n,[[u,.72],[v,.72],[v,.94],[u,.94]])
    axes=np.argsort(np.ptp(p,axis=0))[-2:][::-1]
    q=back[:,axes];span=np.ptp(q,axis=0)
    uv=.254+(q-(q.min(0)+q.max(0))/2)*(.44/max(span))
    builder.explicit(back,equip,(0,0,1,1),normal,uv)
    builder.explicit(outer,b.DARK,b.prior.PLAIN,-normal)
    if tail:
        # Two short bent internal spars emerge from each fracture, not a new
        # frame joining the surviving upper and lower sections.
        for k,x in enumerate((-.48,.48)):
            a=center.copy();a[0]=x;a-=normal*.045
            direction=np.array([(-1 if k==0 else 1),0,0.])
            length=.38+.07*((k+seed)%2)
            centers=[a,a+normal*length*.65,a+normal*length+direction*.13]
            rings=[c+np.array([[-.085,0,-.035],[.085,0,-.035],[.085,0,.035],[-.085,0,.035]])*(1 if j<2 else .72)
                   for j,c in enumerate(centers)]
            for j in range(2):
                for edge in range(4):
                    nxt=(edge+1)%4
                    points=np.array([rings[j][edge],rings[j][nxt],rings[j+1][nxt],rings[j+1][edge]])
                    outward=points.mean(0)-(centers[j]+centers[j+1])/2
                    quad(points,damage,outward,[[edge*.19,.23+j*.30],[(edge+1)*.19,.23+j*.30],[(edge+1)*.19,.53+j*.30],[edge*.19,.53+j*.30]])
            builder.explicit(rings[0],damage,(.1,.83,.3,.96),-normal)
            builder.explicit(rings[-1],equip,(.31,.30,.37,.36),normal)
    return builder.groups()


def write_simple(name,groups):
    # Native standalone 3DB tree, two levels, neutral DpConnect.
    template=audit.DATA/'ships/rheinland/rh_pir_elite/rh_pir_elite_dmg_tail.3db'
    header,ns=mesh.read_tree(template.read_bytes());root=ns[0]
    root.children=[]
    lib=f.folder('VMeshLibrary');ml=f.folder('MultiLevel',mesh.Node('Switch2',np.array([0,550,10000],'<f4').tobytes()))
    blob,v=mesh.pack(f.merge(groups));vname=name+'.vms'
    lib.children.append(f.folder(vname,mesh.Node('VMeshData',blob)))
    ref=f.fresh_ref(vname,blob,v)
    for lv in (0,1):ml.children.append(f.folder('Level'+str(lv),f.folder('VMeshPart',mesh.Node('VMeshRef',ref))))
    root.children += [lib,ml,f.folder('Hardpoints',f.folder('Fixed',f.folder('DpConnect',
        mesh.Node('Position',np.zeros(3,dtype='<f4').tobytes()),mesh.Node('Orientation',np.eye(3,dtype='<f4').tobytes()))))]
    # Material CRCs resolve through the shared MAT declared by each Simple.
    # Standalone viewers must load that library too; never duplicate its pixels.
    target=OUT/'damage'/f'{name}.3db';target.parent.mkdir(exist_ok=True)
    target.write_bytes(mesh.write_tree(header,ns))
    # A standalone damage cap uses part id zero, matching the original convention.
    # Separate stumps must not acquire a convex collision bridge across the
    # missing rear upright. Build a leaf hull for each connected piece.
    adjacency=collections.defaultdict(set)
    for g in groups:
        for tri in g['corners']:
            points=[tuple(p.round(5)) for p in tri[:,:3]]
            for p in points:adjacency[p].update(points)
    pending=set(adjacency);hulls=[]
    while pending:
        start=pending.pop();component={start};queue=[start]
        while queue:
            fresh=adjacency[queue.pop()]&pending;pending-=fresh;component|=fresh;queue.extend(fresh)
        points=np.array(list(component))
        if len(points)>=4 and np.linalg.matrix_rank(points-points[0])==3:hulls.append(sur.make_hull(points,0))
    assert hulls
    surface,lo,hi=sur.encode_surface(hulls)
    target.with_suffix('.sur').write_bytes(b'vers'+S.pack('<fII',2.,0,3)+b'!fxd'+b'exts'+S.pack('<6f',*lo,*hi)+b'surf'+S.pack('<I',len(surface))+surface)
    return dict(file=target.relative_to(OUT).as_posix(),sha256=f.digest(target),triangles=sum(len(g['corners']) for g in groups))


def damage(nodes):
    hp=f.hp_world(nodes);names=f.component_map(nodes);tr,_=audit.transforms(nodes)
    assembly=json.loads((OUT/'assembly.json').read_text());descriptions=[]
    split=assembly['split']
    shift=np.array(assembly.get('center_shift_native',[0,0,0]))
    for kind,part,hpname in [('port_wing','Rh_port_wing_lod1','dpport_wing'),('starboard_wing','Rh_starboard_wing_lod1','dpstarboard_wing'),
                             ('port_engine','Rh_port_engine_lod1','dpport_engine'),('starboard_engine','Rh_starboard_engine_lod1','dpstarboard_engine'),
                             ('tail','Rh_tail_lod1','dptail')]:
        side=-1 if kind.startswith('port') else 1
        anchor=np.array(hp[hpname]['position'])
        if 'wing' in kind:
            normal=np.array([side,0,0.])
            loop=np.array([[side*3.02,-.62,7.49],[side*3.02,-.38,7.49],[side*3.02,-.38,8.23],[side*3.02,-.62,8.23]])
            loops=[loop]
        elif 'engine' in kind:
            normal=np.array([0.,-1,0])
            loops=[np.array([[side*1.12,-.83,7.49],[side*1.87,-.83,7.49],[side*1.87,-.83,8.28],[side*1.12,-.83,8.28]])]
        else:
            normal=np.array([0.,1,0]);loops=[np.array(p) for p in split['cut_loops']]
        if kind!='tail':loops=[p+shift for p in loops]
        parent_groups=[];child_groups=[]
        for i,loop in enumerate(loops):
            if kind=='tail':normal=np.array(split['cuts'][i]['normal'])
            parent_groups+=rupture(loop,normal,.16,i,tail=kind=='tail')
            child_groups+=rupture(loop,-normal,.12,i+2,tail=kind=='tail')
        parent_local=b.base.world(parent_groups,np.eye(3),-anchor)
        parent=write_simple('rh_b_dmg_'+kind,parent_local)
        file=next(k for k,n in names.items() if n==part)
        r,t=tr[file.lower()]
        # Debris hardpoint retains its own moving parent's frame and cap basis.
        cap=b.base.world(child_groups,r.T,-r.T@anchor)
        child=write_simple('rh_b_break_'+kind,cap)
        partnode=mesh.child(nodes[0],file)
        hps=next((n for n in partnode.children if n.name=='Hardpoints'),None)
        if hps is None:hps=f.folder('Hardpoints',f.folder('Fixed'));partnode.children.append(hps)
        fixed=next((n for n in hps.children if n.name=='Fixed'),None)
        if fixed is None:fixed=f.folder('Fixed');hps.children.append(fixed)
        fixed.children=[n for n in fixed.children if n.name!='DpBreak']
        fixed.children.append(f.folder('DpBreak',mesh.Node('Position',np.array(r.T@(anchor-t),'<f4').tobytes()),
                                       mesh.Node('Orientation',np.eye(3,dtype='<f4').tobytes())))
        descriptions.append(dict(zone=kind,part=part,hardpoint=hpname,anchor=anchor.tolist(),parent=parent,debris=child,
                                 world_groups=[dict(material=g['material'],corners=g['corners'].tolist()) for g in parent_groups]))
    (OUT/'damage_manifest.json').write_text(json.dumps(descriptions,indent=2))
    return descriptions


def hull_regions(tris,partid,regions):
    hulls=[]
    for region in regions:
        points=[]
        for tri in tris:
            poly=tri
            for axis,a,c in region:
                if len(poly) and a is not None:poly=sur.clip(poly,axis,a,True)
                if len(poly) and c is not None:poly=sur.clip(poly,axis,c,False)
            points.extend(poly)
        if len(points)<4:continue
        p=np.array(points)
        if np.linalg.matrix_rank(p-p[0],tol=1e-6)<3:continue
        hulls.append(sur.make_hull(p,partid))
    return hulls


def collision(nodes):
    assembly=json.loads((OUT/'assembly.json').read_text())
    shift=np.array(assembly.get('center_shift_native',[0,0,0]))
    names=f.component_map(nodes);tr,_=audit.transforms(nodes);local=f.local_geometry(nodes)
    own={};world_hulls=[];report=[]
    for file,gs in local.items():
        name=names[file];r,t=tr[file.lower()]
        if 'glass' in name.lower() or name.lower().startswith('baydoor'):continue
        groups=b.base.world(gs,r,t);tris=np.concatenate([g['corners'][...,:3] for g in groups])
        if name=='Root':
            # Main hull longitudinal slices, aft bed, separate drum body. Do not
            # convexify the entire ship and fill the large tail negative space.
            regions=[[(2,a,c)] for a,c in zip([-5.7,-2.1,-.1,2.7,4.55],[ -2.1,-.1,2.7,4.55,6.5])]
            regions += [[(2,a,c),(1,None,.31)] for a,c in ((6.5,8),(8,9.5),(9.5,11),(11,12.57))]
            regions += [[(1,.31,4.45),(0,-1.02,1.02),(2,7.05,11.45)]]
            regions += [[(1,y,y+.8),(2,z,z+1.15)] for y in (3.85,4.65,5.45) for z in (6.35,7.50,8.65,9.80,10.95,12.10)]
            regions += [[(1,1.7,3.1),(2,10.7,11.9)]]
        elif '_tail_' in name.lower():
            regions=[[(0,-1.3201,1.3201),(1,y,y+1.45),(2,z,z+1.55)] for y in (.30,1.75,3.20,4.65) for z in (6.35,7.90,9.45,11.0,12.55)]
            for box in assembly.get('tail_pylon_bounds',[]):
                regions.append([(axis,box[0][axis]-1e-5,box[1][axis]+1e-5) for axis in range(3)])
        elif '_wing_' in name.lower():
            side=-1 if '_port_' in name.lower() else 1
            regions=[[(0,*sorted((side*a,side*c)))] for a,c in ((2.4,5.4),(5.4,8.8))]
        elif 'upperarm' in name.lower():
            # Preserve the U-slot: top/bottom jaws and inner back, not a full box.
            regions=[[(1,-.85,-.69)],[(1,-.31,-.15)],[(1,-.69,-.31)]]
        else:regions=[[(2,6.84,8.1)],[(2,8.1,9.4)],[(2,9.4,10.56)]]
        regions=[[(axis,None if a is None else a+shift[axis],None if c is None else c+shift[axis]) for axis,a,c in region] for region in regions]
        hulls=hull_regions(tris,mesh.crc(name),regions)
        assert hulls,name
        # Retain every mesh sample; explicit leftovers become compact convex patches.
        points=tris.reshape(-1,3);covered=np.zeros(len(points),bool)
        for h in hulls:
            q=ConvexHull(h.points);covered |= np.all(points@q.equations[:,:3].T+q.equations[:,3]<=2e-4,axis=1)
        if not covered.all():
            leftover=tris[np.any(~covered.reshape(-1,3),axis=1)]
            # These are the small side weapon pylons / support webs outside the core.
            for side in (-1,1):
                pts=leftover[np.mean(leftover[...,0],axis=1)*side>=0].reshape(-1,3)
                if len(pts)>=4 and np.linalg.matrix_rank(pts-pts[0])==3:hulls.append(sur.make_hull(pts,mesh.crc(name)))
        world_hulls.extend(hulls)
        own[name]=[sur.Hull((h.points-t)@r,h.faces,h.hull_id) for h in hulls]
        report.append(dict(name=name,hulls=len(hulls),regions=regions))
    # Glass is part of the fixed cabin collision envelope; cargo doors stay within it.
    # The source SUR carries equipment hardpoint IDs and small attachment hulls.
    # Recreate them on their NEW owners, so shots and break-off equipment follow
    # the moving wing rather than the historical source coordinates.
    from ship_collision_audit import sur_parts
    source_ids=set()
    for _,chunks in sur_parts(b.base.SOURCE.with_suffix('.sur').read_bytes()):
        for tag,raw in chunks:
            if tag==b'hpid':source_ids.update(np.frombuffer(raw,'<u4').tolist())
    hpids=collections.defaultdict(list)
    for info in f.hp_world(nodes).values():
        crc=mesh.crc(info['name'])
        if crc not in source_ids:continue
        owner=names[info['file']]
        if owner not in own:continue
        p=np.array(info['position']);r,t=tr[info['file'].lower()]
        offsets=np.array([[x,y,z] for x in (-.075,.075) for y in (-.075,.075) for z in (-.075,.075)])
        h=sur.make_hull(offsets+p,crc);world_hulls.append(h)
        own[owner].append(sur.Hull((h.points-t)@r,h.faces,crc));hpids[owner].append(crc)
    raw=bytearray(b'vers'+S.pack('<f',2.))
    for name,hulls in own.items():
        if name=='Root':hulls=world_hulls
        ids=sorted(source_ids) if name=='Root' else hpids[name]
        surface,lo,hi=sur.encode_surface(hulls)
        raw.extend(S.pack('<II',mesh.crc(name),(3 if name=='Root' else 2)+bool(ids)))
        if name=='Root':raw.extend(b'!fxd')
        raw.extend(b'exts'+S.pack('<6f',*lo,*hi)+b'surf'+S.pack('<I',len(surface))+surface)
        if ids:raw.extend(b'hpid'+S.pack('<I',len(ids))+np.array(ids,'<u4').tobytes())
    target=OUT/'rh_concept_b.sur';target.write_bytes(raw)
    (OUT/'collision_manifest.json').write_text(json.dumps(dict(cmp_sha256=f.digest(f.DEST),sur_sha256=f.digest(target),parts=report),indent=2))
    return own


def config(descriptions):
    sections=list(audit.sections(audit.DATA/'SHIPS/shiparch.ini'));idx=next(i for i,(kind,d) in enumerate(sections) if kind=='ship' and d.get('nickname')==['rh_elite_pir'])
    source=[]
    for kind,values in sections[idx:]:
        if source and kind=='ship':break
        source.append((kind,copy.deepcopy(values)))
    text=['; Offline final model. New nickname; no edits to installed archetypes.\n']
    for kind,values in source:
        if kind=='ship':
            values['nickname']=['rh_concept_b'];values['da_archetype']=[r'ships\rheinland\rh_concept_b\rh_concept_b.cmp']
            values['lodranges']=['0, 180, 550, 10000']
            lod_library=r'ships\rheinland\rh_concept_b\rh_concept_b_lods.mat'
            if lod_library not in values['material_library']:values['material_library'].append(lod_library)
        elif kind=='collisiongroup':
            zone=next((d for d in descriptions if values.get('obj',[''])[0].lower()==d['part'].lower()),None)
            if zone:
                values['dmg_obj']=[Path(zone['parent']['file']).stem+'_cap']
                values['group_dmg_hp']=['DpBreak'];values['group_dmg_obj']=[Path(zone['debris']['file']).stem+'_cap']
        text.append('['+kind+']')
        for key,vs in values.items():text.extend(key+' = '+v for v in vs)
        text.append('')
    for d in descriptions:
        for key in ('parent','debris'):
            file=Path(d[key]['file']);text+=['[Simple]','nickname = '+file.stem+'_cap',
                'DA_archetype = ships\\rheinland\\rh_concept_b\\damage\\'+file.name,
                r'material_library = ships\rheinland\rh_pir_playerships.mat',
                'mass = 1','LODranges = 0, 550, 10000','']
    (OUT/'shiparch_fragment.ini').write_text('\n'.join(text),encoding='utf8')


def finish():
    header,nodes=mesh.read_tree(f.DEST.read_bytes())
    assembly=json.loads((OUT/'assembly.json').read_text())
    f.place_hardpoints(nodes,f.hp_world(nodes),assembly['split'])
    levels=[f.local_geometry(nodes)]
    for level,raw in enumerate(json.loads((OUT/'lod_baked_geometry.json').read_text()),1):
        levels.append({file:[dict(g,material=mesh.crc(f'rh_b_lod{level}'),corners=np.array(g['corners'])) for g in gs] for file,gs in raw.items()})
    f.write_geometry(nodes,levels)
    descriptions=damage(nodes);config(descriptions)
    shared_materials(nodes)
    f.DEST.write_bytes(mesh.write_tree(header,nodes))
    collision(nodes);f.export_lod0(nodes)
    review(nodes,descriptions)
    print('FINAL ASSETS',f.DEST,'LODs', [sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in levels],flush=True)


def review(nodes,descriptions):
    mats=audit.material_table(f.material_files())
    groups=[]
    for d in descriptions:
        groups.extend(dict(g,corners=np.array(g['corners']),part=d['part']) for g in d['world_groups'])
        capnodes=mesh.read_tree((OUT/d['debris']['file']).read_bytes())[1]
        libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(capnodes) if p.lower().endswith('/vmeshdata')}
        ref=next(n.blob for p,n in mesh.walk(capnodes) if '/level0/' in p.lower() and p.lower().endswith('/vmeshref'))
        d['debris_groups']=[dict(material=g['material'],corners=g['corners'].tolist()) for g in audit.extract(ref,libs)]
    b.base.export_obj(OUT/'damage_preview.obj',groups,mats)
    names=f.component_map(nodes);hps=[]
    for file,name in names.items():
        part=mesh.child(nodes[0],file)
        hp=next((n for n in part.children if n.name=='Hardpoints'),None)
        if not hp:continue
        for kind in hp.children:
            for item in kind.children:
                hps.append(dict(name=item.name,owner=name,kind=kind.name,
                    position=np.frombuffer(mesh.child(item,'Position').blob,'<f4').astype(float).tolist(),
                    orientation=np.frombuffer(mesh.child(item,'Orientation').blob,'<f4').reshape(3,3).astype(float).tolist()))
    data=dict(cmp_sha256=f.digest(f.DEST),hardpoints=hps,damages=descriptions,lods=[],
              materials={str(k):dict(name=v['name'],texture=v['texture'].rsplit('.',1)[0]+'.png' if v['image'] else None,colour=v['colour'].tolist()) for k,v in mats.items()})
    for level in (1,2):
        data['lods'].append([dict(name=names[file],file=file,groups=[dict(material=g['material'],corners=g['corners'].tolist()) for g in gs]) for file,gs in f.local_geometry(nodes,level).items()])
    (OUT/'review_data.json').write_text(json.dumps(data,separators=(',',':')))


def damage_only():
    """Refresh caps without touching the accepted CMP, its SUR or animations."""
    raw=f.DEST.read_bytes();header,nodes=mesh.read_tree(raw)
    before={p:n.blob for p,n in mesh.walk(nodes)}
    descriptions=damage(nodes)
    assert before=={p:n.blob for p,n in mesh.walk(nodes)},'Damage refresh changed CMP data'
    config(descriptions);review(nodes,descriptions)
    print('DAMAGE ONLY',sum((OUT/d[k]['file']).stat().st_size for d in descriptions for k in ('parent','debris')),'bytes',flush=True)


def shared_materials(nodes):
    """Geometry-only CMP. Shared user MAT stays untouched; LOD MAT is separate."""
    nodes[0].children=[n for n in nodes[0].children if n.name.lower() not in ('material library','texture library')]


def externalize():
    header,nodes=mesh.read_tree(f.DEST.read_bytes());before=f.digest(f.DEST)
    shared_materials(nodes);packed=mesh.write_tree(header,nodes)
    if packed!=f.DEST.read_bytes():f.DEST.write_bytes(packed)
    prior=OUT/'materials_manifest.json'
    original=json.loads(prior.read_text())['cmp_before_sha256'] if prior.exists() else before
    manifest=dict(cmp_before_sha256=original,cmp_sha256=f.digest(f.DEST),shared_mat_sha256=f.digest(f.SHARED_MAT),
                  source_mat=str(b.prior.LIBRARY),source_mat_sha256=f.digest(b.prior.LIBRARY),lod_mat=str(f.LOD_MAT),lod_mat_sha256=f.digest(f.LOD_MAT))
    (OUT/'materials_manifest.json').write_text(json.dumps(manifest,indent=2))
    damage_only();f.export_lod0(nodes)
    # Only storage moved: the SUR data and geometry are unchanged.
    p=OUT/'collision_manifest.json';data=json.loads(p.read_text());data['cmp_sha256']=manifest['cmp_sha256'];p.write_text(json.dumps(data,indent=2))
    print('EXTERNAL LOD MAT',f.LOD_MAT,'CMP bytes',f.DEST.stat().st_size,flush=True)


if __name__=='__main__':
    if '--externalize' in sys.argv:externalize()
    elif '--damage-only' in sys.argv:damage_only()
    else:finish()
