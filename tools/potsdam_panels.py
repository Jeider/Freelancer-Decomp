"""Animated Potsdam solar rotors: CMP Rev joints and independent moving SUR parts."""
from collections import Counter
import json
import math
import struct as S
import numpy as np
import potsdam_mega as p
from check_valensia_mega import templates
from fix_valensia_towers import decoded,expected
from terraform_mega import hp_node

m=p.m
OUT=m.REPO/'out/stations/potsdam_panels'
NAME='pdm_top_rotating'
CLIP='Sc_potsdam_solar_rotation'
PERIOD=90.0
EQUIPMENT='DATA/EQUIPMENT/select_equip.ini'


def rev_record(parent,child,r,t):
    raw=bytearray(208)
    raw[:len(parent)]=parent.encode();raw[64:64+len(child)]=child.encode()
    # Revolute rotation precedes the rest orientation; use the parent-space axis.
    S.pack_into('<20f',raw,128,*t,0,0,0,*r.flatten(),*(r@np.array([1.,0,0])),-2*math.pi,2*math.pi)
    return bytes(raw)


def single_part(name,visuals):
    raw,lods,stats=m.write_cmp(name,visuals)
    header,roots=m.utf.read_tree(raw);root=roots[0]
    assert stats['mesh_parts']==1
    lodmap={m.old.one(m.old.fields(s),'obj'):tuple(m.mesh.floats(m.old.one(m.old.fields(s),'lodranges'))) for s in lods}
    assert dict(decoded(raw,lodmap))==dict(expected(visuals))
    entry=next(e for e in m.b.one(root,'Cmpnd').children if m.b.one(e,'File name'))
    part=m.b.one(root,m.b.text(m.b.one(entry,'File name').blob))
    return header,part,m.b.one(root,'VMeshLibrary').children,stats


def build():
    m.OUT=OUT
    builder=m.Builder()
    original=builder.read(m.GAME/p.TEMPLATE.replace('.py','Original.py')).decode('utf-8-sig')
    rows=[r for r in m.b.placements_from_template(templates(original)['Potsdam']) if '_TOP_' in r.name]
    assert len(rows)==3
    manifest=json.loads((p.OUT/'manifest.json').read_text())
    origin=np.array(next(c['origin'] for c in manifest['components'] if c['group']=='TOP'))
    path=m.GAME/'DATA/solar/misc/space_solar_plant.cmp'
    items,source_hulls,_=builder.asset(path)
    source_root=m.utf.read_tree(builder.read(path))[1][0]
    entries=[e for e in m.b.one(source_root,'Cmpnd').children if m.b.one(e,'Object name')]
    names=[m.b.text(m.b.one(e,'Object name').blob) for e in entries]
    assert len(names)==len(items)==7
    ranges=(0.,100000.)
    center_visuals=[];panel_visuals=[]
    for name,(levels,r,t) in zip(names,items):
        v=m.Visual(levels[:1],ranges,r,t)
        (center_visuals if name=='Root' else panel_visuals).append(v)
    assert len(center_visuals)==1 and len(panel_visuals)==6
    # Stock surface has exactly seven convex leaves: thick central axle + six sheets.
    assert len(source_hulls)==7
    hub=max(source_hulls,key=lambda h:np.ptp(h.points[:,0]))
    sheets=[h for h in source_hulls if h is not hub]
    assert np.ptp(hub.points[:,0])>70 and all(np.ptp(h.points[:,0])<9 for h in sheets)
    centers=[];center_hulls=[];rotors=[]
    for index,row in enumerate(rows):
        r=m.old.euler_matrix(*row.rotate);t=np.array(row.pos)-origin
        for v in center_visuals:
            wr,wt=m.b.compose((r,t),(v.rotation,v.translation))
            centers.append(m.Visual(v.levels,v.ranges,wr,wt))
        center_hulls.append(m.old.ExactHull(hub.points@r.T+t,hub.faces,m.utf.crc('Root'),False,hub.raw))
        rotors.append((f'Rotor{index+1:02d}',r,t))
    header,root_part,library,root_stats=single_part(NAME+'_hub',centers)
    root_part.name=NAME+'_Root.3db'
    root=m.utf.Node('\\');lib=m.utf.Node('VMeshLibrary');comp=m.utf.Node('Cmpnd');cons=m.utf.Node('Cons')
    lib.children=library
    root.children=[lib,comp,root_part]
    comp.children=[cons,m.mesh.part_entry('Root','Root',0,root_part.name)]
    animation=m.utf.Node('Animation');scripts=m.utf.Node('Script');clip=m.utf.Node(CLIP)
    animation.children=[scripts];scripts.children=[clip];root.children.append(animation)
    rev=[];lods=['[LOD]\nobj = Root\nLODranges = 0, 100000\n'];surfaces=[('Root',center_hulls)]
    total_draws=root_stats['draw_groups_after']
    for index,(partname,r,t) in enumerate(rotors,1):
        _,part,meshes,stats=single_part(NAME+'_'+partname,panel_visuals)
        part.name=NAME+'_'+partname+'.3db'
        # Mounts move with their rotor, available for later equipment attachments.
        hp=m.utf.Node('Hardpoints');fixed=m.utf.Node('Fixed')
        fixed.children=[hp_node('HpRotorCenter',(np.eye(3),np.zeros(3)))]
        hp.children=[fixed];part.children.append(hp)
        lib.children.extend(meshes);root.children.append(part)
        comp.children.append(m.mesh.part_entry('Part'+str(index),partname,index,part.name))
        rev.append(rev_record('Root',partname,r,t))
        joint=m.utf.Node('Joint map '+str(index-1));channel=m.utf.Node('Channel')
        joint.children=[m.utf.Node('Parent name',b'Root\0'),m.utf.Node('Child name',partname.encode()+b'\0'),channel]
        channel.children=[m.utf.Node('Header',S.pack('<IfI',5,-1.,1)),
            m.utf.Node('Frames',b''.join(S.pack('<ff',PERIOD*i/4,math.pi*i/2) for i in range(5)))]
        clip.children.append(joint)
        lods.append(f'[LOD]\nobj = {partname}\nLODranges = 0, 100000\n')
        surfaces.append((partname,[m.old.ExactHull(h.points,h.faces,m.utf.crc(partname),False,h.raw) for h in sheets]))
        total_draws+=stats['draw_groups_after']
    cons.children=[m.utf.Node('Rev',b''.join(rev))]
    for label,entries in builder.embedded.items():
        node=m.utf.Node(label);node.children=[m.b.clone(e) for e in entries.values()];root.children.append(node)
    raw=m.utf.write_tree(header,[root])
    # Every rotor must be !fxd, with only its own LOCAL leaf geometry. The engine
    # allocates a physics body and follows its animated pose via AnimDB/Golem.
    surf=bytearray(b'vers'+S.pack('<f',2))
    for name,hulls in surfaces:surf.extend(m.old.surface_file([(name,hulls)])[8:])
    for name,hulls in surfaces:
        chunks=dict(dict(m.old.parts(bytes(surf)))[m.utf.crc(name)])
        assert b'!fxd' in chunks
        restored=m.old.leaves(chunks[b'surf'])
        def key(h):return np.asarray(h.points,dtype='<f4').tobytes(),h.raw[16:]
        assert Counter(map(key,hulls))==Counter(map(key,restored))
    builder.emit(f'DATA/SOLAR/OPTIMIZED/potsdam_mega/{NAME}.cmp',raw)
    builder.emit(f'DATA/SOLAR/OPTIMIZED/potsdam_mega/{NAME}.sur',bytes(surf))
    solar=builder.read(m.GAME/'DATA/SOLAR/solararch.ini').decode('utf-8-sig')
    assert f'nickname = {NAME}' not in solar
    arch=builder.solars['space_solar_plant']
    definition='\n'.join(['[Solar]',f'nickname = {NAME}','type = SATELLITE',
        f'DA_archetype = solar\\OPTIMIZED\\potsdam_mega\\{NAME}.cmp',*[f'material_library = {x}' for x in arch['material_library']],
        'envmap_material = envmapsolar01','mass = 10000','solar_radius = 100','hit_pts = 1e30',
        f'loadout = {NAME}_animation','',*lods])
    builder.emit('DATA/SOLAR/solararch.ini',solar+'\n; BEGIN POTSDAM PANEL ROTORS\n'+definition)
    loadouts=builder.read(m.GAME/'DATA/SOLAR/loadouts.ini').decode('utf-8-sig')
    builder.emit('DATA/SOLAR/loadouts.ini',loadouts+f'\n[Loadout]\nnickname = {NAME}_animation\nequip = {NAME}_motor\n')
    equipment=builder.read(m.GAME/EQUIPMENT).decode('utf-8-sig')
    builder.emit(EQUIPMENT,equipment+f'\n[InternalFX]\nnickname = {NAME}_motor\nuse_animation = {CLIP}\n')
    for path,backup in [(p.TEMPLATE,p.TEMPLATE.replace('.py','StaticOriginal.py')),(p.LIVE,p.LIVE.replace('.ini','PanelsOriginal.ini'))]:
        previous=builder.read(m.GAME/path)
        assert not (m.GAME/backup).exists()
        source=previous.decode('utf-8-sig')
        assert source.count('archetype = pdm_top\n')+source.count('archetype = pdm_top\r\n')==1
        updated=source.replace('archetype = pdm_top\r\n',f'archetype = {NAME}\r\n').replace('archetype = pdm_top\n',f'archetype = {NAME}\n')
        if path.endswith('.py'):compile(updated,path,'exec')
        builder.emit(backup,previous);builder.emit(path,updated)
    report=dict(rotors=3,period_seconds=PERIOD,axis='local X of each original solar plant',moving_surface_parts=3,
        stationary_hulls=len(center_hulls),moving_hulls=len(sheets)*3,draw_groups=total_draws)
    (OUT/'manifest.json').write_text(json.dumps(dict(sources=builder.sources,payload=builder.payload,report=report),indent=2))
    print('Built CMP revolute rotors with local !fxd SURs:',report)


if __name__=='__main__':build()
