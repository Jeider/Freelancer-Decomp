"""Nansei's complete panel mounts, with native revolute animation and moving SUR."""
import math
import numpy as np
import valensia_mega as m
from potsdam_panels import single_part, rev_record
from terraform_mega import hp_node

NAME='nansei_panel_rotor'
CLIP='Sc_nansei_panel_rotation'

def prepare(builder,config,prefix,rows):
    visuals=[];hulls=[];libraries=set();mounts={}
    def append(spec,pose):
        items,hs,hp=builder.asset(m.b.model_path(m.GAME/'DATA',m.old.one(spec,'da_archetype')))
        r,t=pose
        for levels,lr,lt in items:
            wr,wt=m.b.compose(pose,(lr,lt))
            # Use the source's detailed model for the complete moving assembly.
            visuals.append(m.Visual(levels[:1],(0.,50000.),wr,wt))
        hulls.extend(m.old.ExactHull(h.points@r.T+t,h.faces,m.utf.crc('Rotor01'),False,h.raw) for h in hs)
        libraries.update(spec.get('material_library',[]))
        for key,local in hp.items():mounts[key]=m.b.compose(pose,local)
    append(builder.solars['space_industriala'],(np.eye(3),np.zeros(3)))
    for line in builder.loadouts['lightpanels_x3']['equip']:
        nick,hp=[s.strip().lower() for s in line.split(',')[:2]]
        eq=builder.equipment[nick];assert eq['section']=='cargopod'
        child=builder.asset(m.b.model_path(m.GAME/'DATA',m.old.one(eq,'da_archetype')))
        anchor=child[2].get(m.old.one(eq,'hp_child','HpRoot').lower(),(np.eye(3),np.zeros(3)))
        assert hp in mounts,(nick,hp)
        append(eq,m.b.compose(mounts[hp],m.b.inverse(anchor)))
    header,part,meshes,stats=single_part(NAME+'_moving',visuals)
    part.name=NAME+'_Rotor01.3db'
    hp=m.utf.Node('Hardpoints');fixed=m.utf.Node('Fixed')
    fixed.children=[hp_node(k,v) for k,v in mounts.items()];hp.children=[fixed];part.children.append(hp)
    root=m.utf.Node('\\');lib=m.utf.Node('VMeshLibrary');lib.children=meshes
    center=m.utf.Node(NAME+'_Root.3db');multi=m.utf.Node('MultiLevel')
    multi.children=[m.utf.Node('Switch2',m.S.pack('<2f',0,50000)),m.utf.Node('Level0')];center.children=[multi]
    comp=m.utf.Node('Cmpnd');cons=m.utf.Node('Cons')
    # The source industrial cylinder and the three panel arms share local Z.
    record=bytearray(rev_record('Root','Rotor01',np.eye(3),np.zeros(3)))
    m.S.pack_into('<3f',record,188,0,0,1)
    cons.children=[m.utf.Node('Rev',bytes(record))]
    comp.children=[cons,m.mesh.part_entry('Root','Root',0,center.name),m.mesh.part_entry('Part1','Rotor01',1,part.name)]
    animation=m.utf.Node('Animation');scripts=m.utf.Node('Script');clip=m.utf.Node(CLIP);joint=m.utf.Node('Joint map 0');channel=m.utf.Node('Channel')
    channel.children=[m.utf.Node('Header',m.S.pack('<IfI',5,-1.,1)),m.utf.Node('Frames',b''.join(m.S.pack('<ff',90*i/4,math.pi*i/2) for i in range(5)))]
    joint.children=[m.utf.Node('Parent name',b'Root\0'),m.utf.Node('Child name',b'Rotor01\0'),channel]
    clip.children=[joint];scripts.children=[clip];animation.children=[scripts]
    reverse=m.b.clone(clip);reverse.name=CLIP+'_reverse'
    frames=next(m.b.find(reverse,'Frames'))
    frames.blob=b''.join(m.S.pack('<ff',90*i/4,-math.pi*i/2) for i in range(5))
    scripts.children.append(reverse)
    root.children=[lib,comp,center,part,animation]
    for label,entries in builder.embedded.items():
        node=m.utf.Node(label);node.children=[m.b.clone(e) for e in entries.values()];root.children.append(node)
    corners=np.array([[x,y,z] for x in (-.01,.01) for y in (-.01,.01) for z in (-.01,.01)])
    surface=bytearray(m.old.surface_file([('Root',[m.sur.make_hull(corners,m.utf.crc('Root'),False)])]))
    points=np.concatenate([h.points for h in hulls]);radius=float(np.linalg.norm(points,axis=1).max())*1.02
    m.S.pack_into('<6f',surface,24,*([-radius]*3),*([radius]*3));m.S.pack_into('<f',surface,80,radius)
    surface+=m.old.surface_file([('Rotor01',hulls)])[8:]
    relative=f'DATA/SOLAR/OPTIMIZED/{NAME}/{NAME}'
    builder.emit(relative+'.cmp',m.utf.write_tree(header,[root]));builder.emit(relative+'.sur',bytes(surface))
    solar='\n'.join(['[Solar]',f'nickname = {NAME}','type = SATELLITE',f'DA_archetype = solar\\OPTIMIZED\\{NAME}\\{NAME}.cmp',
        *[f'material_library = {v}' for v in sorted(libraries)],'mass = 10000','hit_pts = 1e30','solar_radius = 100',
        'LODranges = 0, 50000',f'loadout = {NAME}_animation',''])
    loadout=f'[Loadout]\nnickname = {NAME}_animation\nequip = {NAME}_motor\n'
    reverse_loadout=f'[Loadout]\nnickname = {NAME}_reverse\nequip = {NAME}_reverse_motor\n'
    equip='DATA/EQUIPMENT/select_equip.ini'
    raw=builder.read(m.GAME/equip).decode('utf-8-sig')
    for suffix,animation_clip in (('_motor',CLIP),('_reverse_motor',CLIP+'_reverse')):
        if NAME+suffix not in builder.equipment:
            raw+=f'\n[InternalFX]\nnickname = {NAME+suffix}\nuse_animation = {animation_clip}\n'
        else:assert m.old.one(builder.equipment[NAME+suffix],'use_animation')==animation_clip
    builder.emit(equip,raw)
    config['overrides']={prefix+'_'+suffix:dict(archetype=NAME,loadout=NAME+'_animation') for suffix in ('lightpanel01','lightpanel02')}
    config['overrides'][prefix+'_lightpanel02']['loadout']=NAME+'_reverse'
    config['retain']=sorted(set(config.get('retain',[]))|set(config['overrides']))
    config['panel_model']=dict(model=relative+'.cmp',hulls=len(hulls),period=90,draw_groups=stats['draw_groups_after'])
    return [solar],[loadout,reverse_loadout]
