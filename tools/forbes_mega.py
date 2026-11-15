"""Semantic ForbesMegafactory compounds; retain docks/ships and transfer yard lights."""
import dataclasses
from collections import Counter, defaultdict
import json
import numpy as np
import valensia_mega as m
from check_valensia_mega import templates
from fix_valensia_towers import decoded, expected
from terraform_mega import hp_node

OUT=m.REPO/'out/forbes_mega'
TEMPLATE='Assets/Pythonlancer/templates/dockable/forbes_megafactory.py'
LIVE='DATA/UNIVERSE/SYSTEMS_MOD/LI_FORBES/li_for.ini'
PREFIX='li_for_05'
MARK='; BEGIN FORBES MEGA'


class Builder(m.Builder):
    def __init__(self):
        super().__init__()
        self.discarded_degenerate_leaves=[]

    def asset(self,path):
        if path in self.assets:return self.assets[path]
        visuals,hulls,hp=super().asset(path)
        valid=[]
        for index,h in enumerate(hulls):
            a,b,c=[h.points[h.faces[:,i]] for i in range(3)]
            area=np.linalg.norm(np.cross(b-a,c-a),axis=1)
            if np.any(area<=1e-9):
                assert path.name.lower()=='space_shield_cut.3db' and np.all(area<=1e-9)
                assert np.linalg.matrix_rank(h.points-h.points.mean(0))<2
                self.discarded_degenerate_leaves.append(dict(
                    source=path.with_suffix('.sur').relative_to(m.GAME).as_posix(),leaf=index))
            else:valid.append(h)
        self.assets[path]=visuals,valid,hp
        return self.assets[path]


def unique_names(text):
    # Temporary identifiers keep every occurrence of duplicate source names.
    import re
    counts=Counter()
    def rename(match):
        nick=match[2]
        if not nick.startswith(PREFIX):return match[0]
        counts[nick]+=1
        return match[1]+nick+(f'_duplicate{counts[nick]}' if counts[nick]>1 else '')
    return re.sub(r'(?m)^(nickname\s*=\s*)(\S+)',rename,text)


def group(row):
    if row.name==PREFIX or row.loadout=='large_co_tradelane_dummy_loadout':return None
    suffix=row.name[len(PREFIX)+1:]
    if suffix.startswith('tube'):return 'TUBES'
    if suffix.startswith('prison'):return 'CORE'
    token=suffix.split('_')[0]
    assert token in ('S1','S2','S3','S4','S5','S6','HILL','TLR','PROD','STOR'),row.name
    return token


def build():
    m.OUT=OUT
    builder=Builder()
    source_bytes=builder.read(m.GAME/TEMPLATE)
    source=source_bytes.decode('utf-8-sig')
    text=unique_names(templates(source)['ForbesMegafactory'].replace('li_for_02',PREFIX))
    live_bytes=builder.read(m.GAME/LIVE)
    live=unique_names(live_bytes.decode('utf-8-sig').replace('li_for_05',PREFIX))
    solar=builder.read(m.GAME/'DATA/SOLAR/solararch.ini').decode('utf-8-sig')
    loadouts=builder.read(m.GAME/'DATA/SOLAR/loadouts.ini').decode('utf-8-sig')
    assert MARK not in solar
    rows=m.b.placements_from_template(text)
    live_rows={p.name:p for p in m.b.placements_from_template(live) if p.name==PREFIX or p.name.startswith(PREFIX+'_')}
    assert set(live_rows)=={p.name for p in rows}
    offset=np.array(live_rows[PREFIX].pos)-next(p.pos for p in rows if p.name==PREFIX)
    for p in rows:
        q=live_rows[p.name]
        assert np.allclose(np.array(p.pos)+offset,q.pos,atol=1e-6,rtol=0)
        assert (p.rotate,p.archetype.lower(),p.loadout)==(q.rotate,q.archetype.lower(),q.loadout),p.name
    groups=defaultdict(list)
    for row in rows:
        key=group(row)
        if key:groups[key].append(row)
    defs,new_loadouts,reports=[],[],[]
    replacements={};removed=set()
    for key,items in groups.items():
        name='forbes_mega_'+key.lower()
        positions=np.array([p.pos for p in items]);origin=(positions.min(0)+positions.max(0))/2
        visuals,hulls,libraries=[],[],set();lights=[];bodies=[]
        for index,item in enumerate(items):
            arch=builder.solars[item.archetype.lower()]
            assert not arch.get('docking_sphere'),item.name
            loadout=item.loadout or m.old.one(arch,'loadout')
            # Props may add nonvisual behavior; refuse unexpected object settings.
            block=next(b for b in m.old.blocks(text) if m.old.one(m.old.fields(b),'nickname')==item.name)
            assert set(m.old.fields(block)) <= {'nickname','pos','rotate','archetype','parent','loadout'},item.name
            row=dataclasses.replace(item,archetype=item.archetype.lower(),loadout=loadout if loadout not in ('shipyard','mplatform_module_white','mplatform_module_black','gas_miner_core') else '')
            vv,hh,ll=builder.expand(row,origin)
            visuals.extend(vv);hulls.extend(hh);libraries.update(ll)
            bodies.append((item.name,hh))
            if loadout in ('shipyard','mplatform_module_white','mplatform_module_black','gas_miner_core'):
                _,_,hps=builder.asset(m.b.model_path(m.GAME/'DATA',m.old.one(arch,'da_archetype')))
                for line in builder.loadouts[loadout]['equip']:
                    nick,hp=[s.strip() for s in line.split(',')]
                    assert builder.equipment[nick.lower()]['section'] in ('light','attachedfx'),nick
                    r,t=m.b.compose((m.old.euler_matrix(*item.rotate),np.array(item.pos)),hps[hp.lower()])
                    lights.append((nick,f'HpYard{index:02d}_{hp}',(r,t-origin)))
        raw,lods,stats=m.write_cmp(name,visuals)
        header,roots=m.utf.read_tree(raw)
        for label,entries in builder.embedded.items():
            node=m.utf.Node(label);node.children=[m.b.clone(n) for n in entries.values()];roots[0].children.append(node)
        if lights:
            comp=m.b.one(roots[0],'Cmpnd')
            entry=next(n for n in comp.children if m.b.one(n,'Object name') and m.b.text(m.b.one(n,'Object name').blob)=='Root')
            part=m.b.one(roots[0],m.b.text(m.b.one(entry,'File name').blob))
            hp=m.utf.Node('Hardpoints');fixed=m.utf.Node('Fixed')
            fixed.children=[hp_node(label,tr) for _,label,tr in lights]
            hp.children=[fixed];part.children.append(hp)
            restored=m.b.hardpoints(part)
            assert len(restored)==len(lights)
            for _,label,(r,t) in lights:
                rr,tt=restored[label.lower()]
                assert np.allclose(rr,r,atol=1e-6) and np.allclose(tt,t,atol=.001)
            new_loadouts.append('[Loadout]\nnickname = '+name+'_lights\n'+''.join(f'equip = {nick}, {hp}\n' for nick,hp,_ in lights))
        raw=m.utf.write_tree(header,roots)
        lodmap={m.old.one(m.old.fields(s),'obj'):tuple(m.mesh.floats(m.old.one(m.old.fields(s),'lodranges'))) for s in lods}
        assert dict(decoded(raw,lodmap))==dict(expected(visuals)),key+' geometry'
        # Keep render batching independent from static physical object size.
        chunks=[];chunk=[]
        for member,hh in bodies:
            if chunk and sum(len(h) for _,h in chunk)+len(hh)>1500:
                chunks.append(chunk);chunk=[]
            chunk.append((member,hh))
        if chunk:chunks.append(chunk)
        bounded=[]
        def partition(entries):
            if len(entries)<=1500:
                grouped=defaultdict(list)
                for member,hull in entries:grouped[member].append(hull)
                bounded.append(list(grouped.items()));return
            centers=np.array([h.points.mean(0) for _,h in entries])
            axis=int(np.argmax(np.ptp(centers,axis=0)))
            order=np.argsort(centers[:,axis],kind='stable');mid=len(order)//2
            partition([entries[i] for i in order[:mid]])
            partition([entries[i] for i in order[mid:]])
        for chunk in chunks:partition([(member,h) for member,hh in chunk for h in hh])
        chunks=bounded
        body_report=[]
        for index,chunk in enumerate(chunks):
            source_hulls=[h for _,hh in chunk for h in hh]
            if not source_hulls:continue
            points=np.concatenate([h.points for h in source_hulls]);pivot=(points.min(0)+points.max(0))/2
            local=[m.old.ExactHull(h.points-pivot,h.faces,m.utf.crc('Root'),False,h.raw) for h in source_hulls]
            proxy=name+f'_collision{index:02d}'
            # An empty render part supplies an instance and its solid SUR only.
            head,tree=m.utf.read_tree(raw);root=tree[0]
            lib=m.utf.Node('VMeshLibrary');cmp=m.utf.Node('Cmpnd')
            file=proxy+'_Root.3db';node=m.utf.Node(file);node.children=[m.utf.Node('MultiLevel')]
            cmp.children=[m.utf.Node('Cons'),m.mesh.part_entry('Root','Root',0,file)]
            root.children=[lib,cmp,node]
            builder.emit(f'DATA/SOLAR/OPTIMIZED/forbes_mega/{proxy}.cmp',m.utf.write_tree(head,tree))
            data=m.old.surface_file([('Root',local)])
            restored=m.old.leaves(dict(dict(m.old.parts(data))[m.utf.crc('Root')])[b'surf'])
            def hull_key(h):return np.asarray(h.points,dtype='<f4').tobytes(),h.raw[16:]
            assert Counter(map(hull_key,local))==Counter(map(hull_key,restored))
            builder.emit(f'DATA/SOLAR/OPTIMIZED/forbes_mega/{proxy}.sur',data)
            defs.append('[Solar]\nnickname = '+proxy+'\ntype = SATELLITE\nDA_archetype = solar\\OPTIMIZED\\forbes_mega\\'+proxy+'.cmp\nmass = 10000\nsolar_radius = 1\nhit_pts = 1e30\n')
            body_report.append(dict(name=proxy,origin=(origin+pivot).tolist(),hulls=len(local),members=[n for n,_ in chunk]))
        # Keep the phantom leaf tiny but include the visible geometry in the
        # surface header bounds: client culling uses the physical radius.
        corners=np.array([[x,y,z] for x in (-.01,.01) for y in (-.01,.01) for z in (-.01,.01)])
        surf=m.old.surface_file([('Root',[m.old.sur.make_hull(corners,m.utf.crc('Root'),False)])])
        points=np.concatenate([np.array([m.S.unpack_from('<3f',v) for v in m.mesh.read_mesh(m.b.one(node,'VMeshData').blob)[1]]) for node in m.b.one(m.utf.read_tree(raw)[1][0],'VMeshLibrary').children])
        surf=bytearray(surf)
        m.S.pack_into('<6f',surf,24,*points.min(0),*points.max(0))
        m.S.pack_into('<f',surf,80,float(np.linalg.norm(points,axis=1).max())*1.02)
        surf=bytes(surf)
        assert max(x['hulls'] for x in body_report)<2000
        builder.emit(f'DATA/SOLAR/OPTIMIZED/forbes_mega/{name}.cmp',raw)
        builder.emit(f'DATA/SOLAR/OPTIMIZED/forbes_mega/{name}.sur',surf)
        defs.append('\n'.join(['[Solar]',f'nickname = {name}','type = SATELLITE',
            f'DA_archetype = solar\\OPTIMIZED\\forbes_mega\\{name}.cmp',*[f'material_library = {x}' for x in sorted(libraries)],
            'envmap_material = envmapsolar01','mass = 10000','solar_radius = 1','hit_pts = 1e30','phantom_physics = true',
            *([f'loadout = {name}_lights'] if lights else []),'',*lods]))
        # Keep one original nickname per group; references to removed names are checked below.
        replacements[items[0].name]=(name,origin)
        removed.update(p.name for p in items[1:])
        reports.append(dict(group=key,name=name,origin=origin.tolist(),members=[p.name for p in items],lights=len(lights),hulls=len(hulls),bodies=body_report,**stats))
        print(key,len(items),'objects -> 1;',stats['draw_groups_before'],'->',stats['draw_groups_after'],'draw groups',flush=True)
    def rewrite(text,offset):
        result=[]
        for block in m.old.blocks(text):
            d=m.old.fields(block);nick=m.old.one(d,'nickname')
            if nick in removed:continue
            if nick in replacements:
                name,origin=replacements[nick]
                result.append('[Object]\nnickname = '+nick+'\npos = '+', '.join(f'{x:.9g}' for x in origin+offset)+f'\nrotate = 0, 0, 0\narchetype = {name}\nparent = {PREFIX}\n\n')
            else:result.append(block)
        result.append('\n\n')
        for report in reports:
            for body in report['bodies']:
                pos=np.array(body['origin'])+offset
                result.append('[Object]\nnickname = '+PREFIX+'_'+body['name']+'\npos = '+', '.join(f'{x:.9g}' for x in pos)+'\nrotate = 0, 0, 0\narchetype = '+body['name']+'\nparent = '+PREFIX+'\n\n')
        return ''.join(result)
    new_text=rewrite(text,np.zeros(3)).replace(PREFIX,'li_for_02');new_live=rewrite(live,offset)
    # Root, working dock, battleships, all unrelated objects and zones survive verbatim.
    retained=[b for b in m.old.blocks(live) if m.old.one(m.old.fields(b),'nickname') not in removed|replacements.keys()]
    assert all(b in new_live for b in retained)
    for nick in removed:
        assert not any(nick in line for line in new_live.splitlines() if '=' in line and not line.lstrip().startswith(';')),nick+' reference remains'
    new_source=source.replace('class ForbesMegafactory(SpaceObjectTemplate):','class ForbesMegafactoryOriginal(SpaceObjectTemplate):',1)
    new_source+="\n\nclass ForbesMegafactory(ForbesMegafactoryOriginal):\n    TEMPLATE = '''"+new_text+"'''\n"
    compile(new_source,TEMPLATE,'exec')
    template_backup=TEMPLATE.replace('.py','Original.py')
    system_backup=LIVE.replace('.ini','ForbesMegafactoryOriginal.ini')
    assert not (m.GAME/template_backup).exists() and not (m.GAME/system_backup).exists()
    builder.emit(template_backup,source_bytes);builder.emit(TEMPLATE,new_source)
    builder.emit(system_backup,live_bytes);builder.emit(LIVE,new_live.replace(PREFIX,'li_for_05'))
    builder.emit('DATA/SOLAR/solararch.ini',solar+'\n'+MARK+'\n'+'\n'.join(defs)+'\n; END FORBES MEGA\n')
    builder.emit('DATA/SOLAR/loadouts.ini',loadouts+'\n'+MARK+'\n'+'\n'.join(new_loadouts)+'\n; END FORBES MEGA\n')
    manifest=dict(sources=builder.sources,payload=builder.payload,components=reports,removed=sorted(removed),
        before=len(rows),after=len(rows)-len(removed)+sum(len(r['bodies']) for r in reports),offset=offset.tolist(),
        discarded_degenerate_leaves=builder.discarded_degenerate_leaves)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PASS: exact triangles/LODs/SUR, light mounts, template/live equivalence; objects',manifest['before'],'->',manifest['after'])


if __name__=='__main__':build()


