"""Animated front-only dock clusters, using retail joints and shipping-door UVs."""
import json
import numpy as np
import re
import valensia_mega as m
from terraform_mega import hp_node

def unite_core(text,prefix):
    blocks=m.old.blocks(text)
    dock=next(b for b in blocks if m.old.one(m.old.fields(b),'nickname')==prefix+'_dock')
    values=m.old.fields(dock)
    out=[]
    for block in blocks:
        nickname=m.old.one(m.old.fields(block),'nickname')
        if nickname==prefix+'_dock':continue
        if nickname==prefix:
            if '{root_props}' in block:
                block=block.replace('{root_props}','{dock_props}')
            else:
                for key in ('dock_with','base','ids_name','ids_info','reputation','behavior','space_costume','voice'):
                    if key not in values:continue
                    block=re.sub(r'(?mi)^'+key+r'\s*=[^\r\n]*\r?\n','',block)
                    block=block.rstrip()+'\n'+key+' = '+m.old.one(values,key)+'\n\n'
        block=re.sub(r'(?m)^(parent\s*=\s*)'+re.escape(prefix+'_dock')+r'\s*$',lambda match:match[1]+prefix+'\n',block)
        out.append(block)
    return ''.join(out)

def direct(node,name):
    return next((c for c in node.children if c.name.lower()==name.lower()),None)

def entries(root):
    return [(m.b.text(direct(e,'Object name').blob),m.b.text(direct(e,'File name').blob))
            for e in direct(root,'Cmpnd').children if direct(e,'Object name')]

def numbered_uv(police,shipping,number):
    """Copy only STANUMS UVs; keep the police geometry, normals and topology."""
    pm=m.b.library_meshes(police);sm=m.b.library_meshes(shipping)
    pe=dict(entries(police));se=dict(entries(shipping));count=0
    for side in ('a','b'):
        pn=direct(police,pe['door1_'+side+'_lod1']);sn=direct(shipping,se[f'door{number}_{side}_lod1'])
        pr=list(m.b.find(pn,'VMeshRef'));sr=list(m.b.find(sn,'VMeshRef'));assert len(pr)==len(sr)
        uvmap={}
        first=True
        for p in pr:
            pd=direct(pm[m.S.unpack_from('<I',p.blob,4)[0]],'VMeshData')
            pg,pv=m.mesh.read_mesh(pd.blob)
            pb,_,_,_,pf,pc=m.S.unpack_from('<6H',p.blob,8)
            numbers=m.utf.crc('STANUMS_256')
            pnum=[g for g in pg[pf:pf+pc] if g[0]==numbers];assert len(pnum)==1
            a=pnum[0]
            if first:
                ref=sr[0];sd=direct(sm[m.S.unpack_from('<I',ref.blob,4)[0]],'VMeshData')
                sg,sv=m.mesh.read_mesh(sd.blob);sb,_,_,_,sf,sc=m.S.unpack_from('<6H',ref.blob,8)
                snum=[g for g in sg[sf:sf+sc] if g[0]==numbers];assert len(snum)==1
                b=snum[0];assert len(a[4])==len(b[4])
                for pi,si in set(zip(a[4],b[4])):
                    pi+=pb+a[1];si+=sb+b[1]
                    assert np.allclose(m.S.unpack_from('<3f',pv[pi]),m.S.unpack_from('<3f',sv[si]),atol=.001)
                    key=pv[pi][24:];value=sv[si][24:]
                    assert key not in uvmap or uvmap[key]==value
                    uvmap[key]=value
                first=False
            for pi in set(a[4]):
                pi+=pb+a[1];pv[pi]=pv[pi][:24]+uvmap[pv[pi][24:]];count+=1
            pd.blob=m.mesh.write_mesh(pg,pv)
    assert count>0
    return count

def build_model(builder,name,poses,core=None,source_model='DATA/SOLAR/DOCKABLE/space_police01.cmp',active_side=1):
    police_path=m.GAME/source_model
    header,source=m.utf.read_tree(builder.read(police_path));source=source[0]
    shipping=m.utf.read_tree(builder.read(m.GAME/'DATA/SOLAR/DOCKABLE/space_shipping01.cmp'))[1][0]
    source_sur=m.old.parts(builder.read(police_path.with_suffix('.sur')))
    original_parts=dict(entries(source));by_id={m.utf.crc(n):n for n in original_parts}
    original_hulls={by_id[i]:m.old.leaves(dict(chunks)[b'surf']) for i,chunks in source_sur}
    from station_collision_parts import active_port_hulls
    original_hulls['Root']=active_port_hulls(source,original_hulls['Root'])
    root=m.utf.Node('\\');lib=m.utf.Node('VMeshLibrary');comp=m.utf.Node('Cmpnd');cons=m.utf.Node('Cons')
    scripts=m.utf.Node('Script');animation=m.utf.Node('Animation');animation.children=[scripts]
    rootfile=name+'_Root.3db';rootpart=m.utf.Node(rootfile);rootpart.children=[m.utf.Node('MultiLevel')]
    comp.children=[cons,m.mesh.part_entry('Root','Root',0,rootfile)]
    root.children=[lib,comp,rootpart,animation]
    if core and not core.get('empty'):
        # The old invisible wire model is the new selectable root. All docks
        # are fixed children, expressed in this root's coordinate system.
        wire=m.utf.read_tree(builder.read(m.b.model_path(m.GAME/'DATA',m.old.one(core,'da_archetype'))))[1][0]
        ids={}
        for i,node in enumerate(direct(wire,'VMeshLibrary').children):
            old=m.utf.crc(node.name);node.name=f'{name}_wire{i}.vms';ids[old]=m.utf.crc(node.name);lib.children.append(node)
        rootpart.children=[m.b.clone(c) for c in wire.children if c.name in ('MultiLevel','VMeshWire')]
        for kind in ('VMeshRef','VWireData'):
            for ref in m.b.find(rootpart,kind):
                raw=bytearray(ref.blob);m.S.pack_into('<I',raw,4,ids[m.S.unpack_from('<I',raw,4)[0]]);ref.blob=bytes(raw)
    fix=[];rev=[];static=[];moving=[];hps=[];meta=[]
    root_hps=m.b.hardpoints(direct(source,original_parts['Root']))
    for index,(rotation,translation) in enumerate(poses,1):
        copied=m.b.clone(source);uv=numbered_uv(copied,shipping,index) if active_side==1 else 0
        names={old:f'D{index}_{old}' for old,_ in entries(copied)}
        files={old:f'{name}_D{index}_{i:02d}.3db' for i,(_,old) in enumerate(entries(copied))}
        if index==1 and not core:
            names['Root']='Root';files[original_parts['Root']]=rootfile
        mesh_ids={}
        for i,node in enumerate(direct(copied,'VMeshLibrary').children):
            old=m.utf.crc(node.name);node.name=f'{name}_D{index}_M{i:03d}.vms';mesh_ids[old]=m.utf.crc(node.name)
            lib.children.append(node)
        for old,file in entries(copied):
            part=direct(copied,file);part.name=files[file]
            # All docking HPs belong to the cluster root, once, with unique letters.
            part.children=[c for c in part.children if c.name.lower()!='hardpoints']
            for ref in m.b.find(part,'VMeshRef'):
                blob=bytearray(ref.blob);m.S.pack_into('<I',blob,4,mesh_ids[m.S.unpack_from('<I',blob,4)[0]]);ref.blob=bytes(blob)
            if index==1 and old=='Root' and not core:
                root.children.remove(rootpart);rootpart=part
            else:comp.children.append(m.mesh.part_entry('Part'+str(len(comp.children)-1),names[old],len(comp.children)-1,part.name))
            root.children.append(part)
        if index>1 or core:fix.append(m.mesh.fix_record('Root',names['Root'],rotation,translation))
        for kind in direct(direct(copied,'Cmpnd'),'Cons').children:
            assert kind.name in ('Fix','Rev')
            stride=176 if kind.name=='Fix' else 208
            for at in range(0,len(kind.blob),stride):
                record=bytearray(kind.blob[at:at+stride])
                for start in (0,64):
                    original=m.b.text(record[start:start+64]);replacement=names[original].encode('ascii')
                    assert len(replacement)<64;record[start:start+64]=replacement.ljust(64,b'\0')
                (fix if kind.name=='Fix' else rev).append(record)
        script=m.b.clone(direct(direct(direct(copied,'Animation'),'Script'),f'Sc_open dock{active_side}'))
        script.name=f'Sc_open dock{index}'
        for joint in script.children:
            for field in ('Parent name','Child name'):
                n=direct(joint,field);n.blob=(names[m.b.text(n.blob)]+'\0').encode('ascii')
        scripts.children.append(script)
        for old,hulls in original_hulls.items():
            if old=='Root':
                static.extend(m.old.ExactHull(h.points@rotation.T+translation,h.faces,m.utf.crc('Root'),False,h.raw) for h in hulls)
            else:
                moving.append((names[old],[m.old.ExactHull(h.points,h.faces,m.utf.crc(names[old]),False,h.raw) for h in hulls]))
        letter=chr(64+index)
        for source_hp,target in [('hpdockmounta','HpDockMount'+letter),('hpdockpointa01','HpDockPoint'+letter+'01'),('hpdockpointa02','HpDockPoint'+letter+'02'),('hpdockcama','HpDockCam'+letter)]:
            if active_side==2 and source_hp!='hpdockcama':source_hp=source_hp.replace('mounta','mountb').replace('pointa','pointb')
            hps.append(hp_node(target,m.b.compose((rotation,translation),root_hps[source_hp])))
        meta.append(dict(number=index,rotation=rotation.tolist(),position=translation.tolist(),numbered_vertices=uv))
    cons.children=[m.utf.Node('Fix',b''.join(fix)),m.utf.Node('Rev',b''.join(rev))]
    if active_side==2:
        # Keep the original front module's two capital-ship mooring terminals.
        for letter in ('c','d'):
            for source_hp in ('hpdockmount'+letter,'hpdockpoint'+letter+'01','hpdockpoint'+letter+'02'):
                hps.append(hp_node(source_hp,m.b.compose(poses[0],root_hps[source_hp])))
    hp=m.utf.Node('Hardpoints');fixed=m.utf.Node('Fixed');fixed.children=hps;hp.children=[fixed];rootpart.children.append(hp)
    surface=m.old.surface_file([('Root',static)])
    for part,hulls in moving:surface+=m.old.surface_file([(part,hulls)])[8:]
    relative=f'DATA/SOLAR/OPTIMIZED/{name}/{name}'
    builder.emit(relative+'.cmp',m.utf.write_tree(header,[root]));builder.emit(relative+'.sur',surface)
    body_count=1+len(moving);assert body_count==1+4*len(poses)
    solar='\n'.join(['[Solar]',f'nickname = {name}','type = STATION',f'DA_archetype = solar\\OPTIMIZED\\{name}\\{name}.cmp',
        'material_library = solar\\Solar_mat_dockable03.mat','material_library = fx\\envmapbasic.mat','envmap_material = envmapsolar01',
        'lodranges = 0, 3000, 50000','mass = 10000','solar_radius = 600','hit_pts = 1e30','shape_name = NAV_port',
        'open_sound = depot_open_sound','close_sound = depot_close_sound','docking_camera = 0',
        *[f'docking_sphere = berth, HpDockMount{chr(65+i)}, 4.5, Sc_open dock{i+1}' for i in range(len(poses))],''])
    if core:
        solar+=('radar_wireframe = true\n' if not core.get('empty') else '')+'[LOD]\nobj = Root\nLODranges = 0, 1\n'
        for index in range(1,len(poses)+1):
            for old in original_parts:
                solar+=f'[LOD]\nobj = D{index}_{old}\nLODranges = 0, 3000, 50000\n'
    if active_side==2:
        solar=solar.replace('docking_camera = 0\n','docking_camera = 0\ndocking_sphere = moor_medium, HpDockMountC, 5\ndocking_sphere = moor_medium, HpDockMountD, 5\n')
    return solar,dict(name=name,ports=meta,bodies=body_count,model=relative+'.cmp',source_model=source_model,active_side=active_side)

def prepare(builder,config,prefix,rows):
    if config['docks']=='shipping':
        from station_shipping_core import prepare as shipping
        return shipping(builder,config,prefix,rows)
    if config['docks']=='losangeles':
        name='losangeles_two_docks';center=np.array([0.,0.,-315.])
        poses=[(m.old.euler_matrix(0,180,0),-center),(np.eye(3),center)]
        solar,report=build_model(builder,name,poses,{'empty':True},'DATA/SOLAR/DOCKABLE/space_police02_losangeles.cmp',2)
        solar=solar.replace('solar\\Solar_mat_dockable03.mat','solar\\Solar_mat_space_dmg.mat')
        config['overrides']={prefix:dict(archetype=name,pos=center.tolist(),rotate=[0,0,0])}
        # These are the decorative cap beyond the rear airlock, replaced by dock 2.
        config['omit']=[prefix+'_contol_tower13',prefix+'_habitat18']
        report['root_name']=prefix;config['dock_model']=report
        (m.OUT/'docks.json').write_text(json.dumps(report,indent=2))
        return [solar],[]
    by_name={r.name:r for r in rows};primary=by_name[prefix+'_dock']
    main=(m.old.euler_matrix(*primary.rotate),np.array(primary.pos));poses=[(np.eye(3),np.zeros(3))]
    overrides={};omitted=[];loadouts=[]
    if config['docks']=='corsair':
        name='corsair_four_docks'
        for suffix in ('LEFT_S1_dock01','LEFT_S2_dock01','RIGHT_S1_dock01'):
            row=by_name[prefix+'_'+suffix];assert row.archetype=='space_locked_dock'
            poses.append(m.b.compose(m.b.inverse(main),(m.old.euler_matrix(*row.rotate),np.array(row.pos))))
            omitted.append(row.name)
    else:
        assert config['docks']=='odissey';name='odissey_eight_docks' if config.get('rear_docks') else 'odissey_five_docks'
        source_loadout=builder.loadouts['odissey_lock_dock_connect']
        clone='odissey_working_dock_windows'
        lines=[line for line in source_loadout['equip'] if not line.startswith('attached_locked_dock_lowdetail,')]
        assert len(lines)==2
        loadouts.append('[Loadout]\nnickname = '+clone+'\n'+''.join('equip = '+line+'\n' for line in lines))
        suffixes=['D1_connect01','D1_connect02','D1_connect03','D1_connect04']
        if config.get('rear_docks'):suffixes+=['D2_connect01','D2_connect02','D2_connect03']
        for suffix in suffixes:
            row=by_name[prefix+'_'+suffix];assert row.loadout=='odissey_lock_dock_connect'
            arch=builder.solars[row.archetype];parent_hp=builder.asset(m.b.model_path(m.GAME/'DATA',m.old.one(arch,'da_archetype')))[2]
            eq=builder.equipment['attached_locked_dock_lowdetail']
            child=builder.asset(m.b.model_path(m.GAME/'DATA',m.old.one(eq,'da_archetype')))
            anchor=child[2].get(m.old.one(eq,'hp_child','HpRoot').lower(),(np.eye(3),np.zeros(3)))
            world=m.b.compose((m.old.euler_matrix(*row.rotate),np.array(row.pos)),m.b.compose(parent_hp['hpodisseydock01'],m.b.inverse(anchor)))
            if suffix.startswith('D1'):assert world[1][2]>-142, 'use front hemisphere; keep rear spine access clear'
            poses.append(m.b.compose(m.b.inverse(main),world));overrides[row.name]={'loadout':clone}
    core=None
    if config.get('unified_core'):
        center=by_name[prefix];core=builder.solars[center.archetype]
        root_pose=(m.old.euler_matrix(*center.rotate),np.array(center.pos))
        poses=[m.b.compose(m.b.inverse(root_pose),m.b.compose(main,pose)) for pose in poses]
        omitted.append(primary.name);overrides[prefix]={'archetype':name}
    else:overrides[primary.name]={'archetype':name}
    solar,report=build_model(builder,name,poses,core)
    report['root_name']=prefix if core else primary.name
    config['overrides']=overrides;config['omit']=omitted;config['dock_model']=report
    (m.OUT/'docks.json').write_text(json.dumps(report,indent=2))
    return [solar],loadouts
