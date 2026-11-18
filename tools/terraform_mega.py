"""Bake OR_HQ terraformer static attachments, preserving animated ring solars.

No universe generation. All live/staged DATA output uses DataFolder.
"""
import argparse
from collections import Counter
import json
import re
import struct as S
import numpy as np
import valensia_mega as m
from fix_valensia_towers import decoded, expected

OUT=m.REPO/'out/stations/terraform_mega'
NAME='tfm_or_hq_body'
TEMPLATE='Assets/Pythonlancer/templates/dockable/terraforming.py'
SYSTEM='Assets/Pythonlancer/universe/systems/or_hq_static.py'
LIVE='DATA/'+m.old.LIVE
MARK='; BEGIN OR_HQ TERRAFORM MEGA'


def field(block,key,value):
    pattern=rf'(?im)^{re.escape(key)}\s*=.*$'
    if value is None:return re.sub(pattern+'\n?', '',block)
    line=f'{key} = {value}'
    return re.sub(pattern,lambda _:line,block) if re.search(pattern,block) else block.rstrip()+'\n'+line+'\n\n'


def hp_node(name,transform):
    r,t=transform
    node=m.utf.Node(name)
    node.children=[m.utf.Node('Orientation',S.pack('<9f',*r.flatten())),m.utf.Node('Position',S.pack('<3f',*t))]
    return node


def build():
    m.OUT=OUT
    builder=m.Builder()
    # Only the tank carriers have this stationary Rev. Animated ring carriers
    # are deliberately never expanded or baked.
    builder.stationary_revolute_models={'polygon.cmp','polygon2.cmp'}
    live=builder.read(m.GAME/LIVE).decode('utf-8-sig')
    solar=builder.read(m.GAME/'DATA/SOLAR/solararch.ini').decode('utf-8-sig')
    loadouts=builder.read(m.GAME/'DATA/SOLAR/loadouts.ini').decode('utf-8-sig')
    template=builder.read(m.GAME/TEMPLATE).decode('utf-8-sig')
    system=builder.read(m.GAME/SYSTEM).decode('utf-8-sig')
    assert MARK not in solar
    blocks=m.old.blocks(live)
    groups=[]
    for index in (1,2,3):
        prefix=f'or_hq_terra_{index}'
        group=[p for p in m.b.placements_from_template(live) if p.name==prefix or p.name.startswith(prefix+'_')]
        assert len(group)==7
        root=next(p for p in group if p.name==prefix)
        normalized=sorted((p.name[len(prefix):],p.archetype,p.loadout,tuple(np.array(p.pos)-root.pos),p.rotate) for p in group)
        groups.append((root,group,normalized))
    assert groups[0][2]==groups[1][2]==groups[2][2], 'stations differ'
    root,rows,_=groups[0]
    origin=np.array(root.pos)
    sphere=next(p for p in rows if p.name.endswith('_SPHERE'))
    sphere_path=m.b.model_path(m.GAME/'DATA',m.old.one(builder.solars[sphere.archetype],'da_archetype'))
    sphere_root=m.utf.read_tree(builder.read(sphere_path))[1][0]
    sphere_hp=m.b.hardpoints(sphere_root)
    sphere_transform=(m.old.euler_matrix(*sphere.rotate),np.array(sphere.pos))
    visuals,hulls,libraries=[],[],set()
    effects=[]
    pending_fx=[]
    attachment_hps={}
    attachment_count=0
    for line in builder.loadouts[sphere.loadout]['equip']:
        nick,hp=[x.strip() for x in line.split(',')]
        eq=builder.equipment[nick.lower()]
        if eq['section']=='attachedfx':
            pending_fx.append((nick,hp))
            continue
        mount=m.b.compose(sphere_transform,sphere_hp[hp.lower()])
        assert eq['section']=='cargopod' and not m.old.one(eq,'loadout')
        path=m.b.model_path(m.GAME/'DATA',m.old.one(eq,'da_archetype'))
        parts,collision,child_hp=builder.asset(path)
        anchor=child_hp.get(m.old.one(eq,'hp_child','HpRoot').lower(),(np.eye(3),np.zeros(3)))
        r,t=m.b.compose(mount,m.b.inverse(anchor))
        for hp_name,tr in child_hp.items():
            attachment_hps.setdefault(hp_name,[]).append(m.b.compose((r,t),tr))
        ranges=tuple(m.mesh.floats(m.old.one(eq,'lodranges')))
        for levels,lr,lt in parts:
            wr,wt=m.b.compose((r,t),(lr,lt));used=min(len(levels),len(ranges)-1)
            assert used>0
            visuals.append(m.Visual(levels[:used],ranges[:used+1],wr,wt-origin))
        hulls.extend(m.old.ExactHull(h.points@r.T+t-origin,h.faces,m.utf.crc('Root'),False,h.raw) for h in collision)
        libraries.update(eq.get('material_library',[]));attachment_count+=1
    for nick,hp in pending_fx:
        if hp.lower() in sphere_hp:
            mount=m.b.compose(sphere_transform,sphere_hp[hp.lower()])
        else:
            candidates=attachment_hps.get(hp.lower(),[])
            assert len(candidates)==1,(hp,len(candidates))
            mount=candidates[0]
        effects.append((nick,hp,(mount[0],mount[1]-origin)))
    tank_rows=[p for p in rows if p.name.endswith('_tanks')]
    assert len(tank_rows)==3
    for row in tank_rows:
        assert all(',' in x and builder.equipment[x.split(',')[0].lower()]['section']=='cargopod' for x in builder.loadouts[row.loadout]['equip'])
        vv,hh,ll=builder.expand(row,origin)
        visuals.extend(vv);hulls.extend(hh);libraries.update(ll)
        attachment_count+=len(builder.loadouts[row.loadout]['equip'])
    raw,lods,stats=m.write_cmp(NAME,visuals)
    header,roots=m.utf.read_tree(raw)
    comp=m.b.one(roots[0],'Cmpnd')
    root_entry=next(n for n in comp.children if m.b.one(n,'Object name') and m.b.text(m.b.one(n,'Object name').blob)=='Root')
    root_part=m.b.one(roots[0],m.b.text(m.b.one(root_entry,'File name').blob))
    hp=m.utf.Node('Hardpoints');fixed=m.utf.Node('Fixed')
    fixed.children=[hp_node(name,tr) for _,name,tr in effects]
    hp.children=[fixed];root_part.children.append(hp)
    # Keep the original radar wire representation without its hidden helper mesh.
    wire_path=m.b.model_path(m.GAME/'DATA',m.old.one(builder.solars[root.archetype],'da_archetype'))
    wire=m.utf.read_tree(builder.read(wire_path))[1][0]
    wire_node=m.b.one(wire,'VMeshWire')
    if wire_node:
        root_part.children.append(m.b.clone(wire_node))
        m.b.one(roots[0],'VMeshLibrary').children.extend(m.b.clone(n) for n in m.b.one(wire,'VMeshLibrary').children)
    for label,entries in builder.embedded.items():
        node=m.utf.Node(label);node.children=[m.b.clone(n) for n in entries.values()];roots[0].children.append(node)
    raw=m.utf.write_tree(header,roots)
    lodmap={m.old.one(m.old.fields(s),'obj'):tuple(m.mesh.floats(m.old.one(m.old.fields(s),'lodranges'))) for s in lods}
    assert dict(decoded(raw,lodmap))==dict(expected(visuals)), 'visual/LOD mismatch'
    surf=m.old.surface_file([('Root',hulls)])
    restored=m.old.leaves(dict(dict(m.old.parts(surf))[m.utf.crc('Root')])[b'surf'])
    # SUR float serialization is exact for input points converted to float32.
    def hull_key(h):return np.asarray(h.points,dtype='<f4').tobytes(),h.raw[16:]
    assert Counter(map(hull_key,hulls))==Counter(map(hull_key,restored))
    builder.emit(f'DATA/SOLAR/OPTIMIZED/terraform_mega/{NAME}.cmp',raw)
    builder.emit(f'DATA/SOLAR/OPTIMIZED/terraform_mega/{NAME}.sur',surf)
    definition='\n'.join(['[Solar]',f'nickname = {NAME}','type = MISSION_SATELLITE',
        f'DA_archetype = solar\\OPTIMIZED\\terraform_mega\\{NAME}.cmp',*[f'material_library = {x}' for x in sorted(libraries)],
        'envmap_material = envmapsolar01','mass = 10000','solar_radius = 1000','shape_name = nav_largestation',
        'hit_pts = 1e30','radar_wireframe = true',f'loadout = {NAME}_fx','',*lods])
    builder.emit('DATA/SOLAR/solararch.ini',solar+'\n'+MARK+'\n'+definition+'\n; END OR_HQ TERRAFORM MEGA\n')
    builder.emit('DATA/SOLAR/loadouts.ini',loadouts+'\n'+MARK+f'\n[Loadout]\nnickname = {NAME}_fx\n'+''.join(f'equip = {nick}, {hp}\n' for nick,hp,_ in effects))
    removed={p.name for _,rows,_ in groups for p in rows if p.name.endswith('_tanks')}
    root_names={r.name for r,_,_ in groups}
    def edit(block):
        nick=m.old.one(m.old.fields(block),'nickname')
        if nick in removed:return ''
        if nick in root_names:return field(block,'archetype',NAME)
        if any(nick==name+'_SPHERE' for name in root_names):return field(block,'loadout',None)
        return block
    updated=''.join(map(edit,blocks))
    # Ring carrier objects and external FX are byte-identical; no animation is baked.
    original_rings=[b for b in blocks if '_rings_root' in m.old.one(m.old.fields(b),'nickname')]
    assert len(original_rings)==6 and all(b in updated for b in original_rings)
    builder.read(m.GAME/'DATA/polygon2.cmp')
    builder.emit(LIVE,updated)
    snapshot=LIVE.replace('.ini','TerraformOriginal.ini')
    assert not (m.GAME/snapshot).exists()
    builder.emit(snapshot,live)
    # Keep all existing template classes intact. This variant is restricted to OR_HQ.
    local=[]
    for block in blocks:
        nick=m.old.one(m.old.fields(block),'nickname')
        if nick!=root.name and not nick.startswith(root.name+'_'):continue
        block=edit(block)
        if not block:continue
        d=m.old.fields(block)
        pos=np.array(m.mesh.floats(m.old.one(d,'pos')))-origin
        block=field(block,'pos',', '.join(f'{x:g}' for x in pos))
        if nick==root.name:
            for key in ('ids_name','ids_info','reputation','behavior'):block=field(block,key,None)
            block=block.rstrip()+'\n{root_props}\n\n'
        local.append(block.replace(root.name,'alt_cur_02'))
    new_template=template+"\n\n# Static OR_HQ body with independent animated ring carriers.\nclass TerraformingTwoOrHQ(SpaceObjectTemplate):\n    SPACE_OBJECT_NAME = 'alt_cur_02'\n    TEMPLATE = '''"+''.join(local)+"'''\n"
    compile(new_template,TEMPLATE,'exec')
    backup=TEMPLATE.replace('.py','Original.py')
    assert not (m.GAME/backup).exists()
    builder.emit(backup,template)
    builder.emit(TEMPLATE,new_template)
    assert system.count('terraforming.TerraformingTwo')==3
    builder.emit(SYSTEM,system.replace('terraforming.TerraformingTwo','terraforming.TerraformingTwoOrHQ'))
    report=dict(instances=3,objects_before=7,objects_after=4,static_attachments_before=attachment_count,
        animated_carriers_preserved=6,fx_hardpoints=[x[1] for x in effects],hulls=len(hulls),**stats)
    manifest=dict(sources=builder.sources,payload=builder.payload,report=report)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PASS: triangles, LODs, exact collision leaves, identical instances and unchanged animated carriers',flush=True)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':build()
