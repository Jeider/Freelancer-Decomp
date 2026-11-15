"""Semantic UlsterMegabase compounds; retain docks/ships and transfer yard lights."""
import dataclasses
from collections import Counter, defaultdict
import json
import numpy as np
import valensia_mega as m
from check_valensia_mega import templates
from fix_valensia_towers import decoded, expected
from terraform_mega import hp_node

OUT=m.REPO/'out/ulster_megabase'
TEMPLATE='Assets/Pythonlancer/templates/dockable/ulster_megabase.py'
LIVE='DATA/UNIVERSE/SYSTEMS_MOD/BR_WARWICK/br_wrw.ini'
PREFIX='br_uls_02'
MARK='; BEGIN ULSTER MEGABASE'


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


def group(row):
    if row.name in (PREFIX,PREFIX+'_dock',PREFIX+'_core'):return None
    suffix=row.name[len(PREFIX)+1:]
    parts=suffix.split('_')
    if parts[0]=='PANEL':return '_'.join(parts[:2])
    assert parts[0] in ('DOCK','CORE','TOP','BOTTOM','TOPLINE','BOTTOMLINE'),row.name
    return parts[0]


def build():
    m.OUT=OUT
    builder=Builder()
    source_bytes=builder.read(m.GAME/TEMPLATE)
    source=source_bytes.decode('utf-8-sig')
    text=templates(source)['UlsterMegabase']
    live_bytes=builder.read(m.GAME/LIVE)
    live=live_bytes.decode('utf-8-sig').replace('br_wrw_02',PREFIX)
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
        name='ulster_megabase_'+key.lower()
        positions=np.array([p.pos for p in items]);origin=(positions.min(0)+positions.max(0))/2
        visuals,hulls,libraries=[],[],set();lights=[]
        for index,item in enumerate(items):
            arch=builder.solars[item.archetype.lower()]
            assert not arch.get('docking_sphere'),item.name
            loadout=item.loadout or m.old.one(arch,'loadout')
            # Props may add nonvisual behavior; refuse unexpected object settings.
            block=next(b for b in m.old.blocks(text) if m.old.one(m.old.fields(b),'nickname')==item.name)
            assert set(m.old.fields(block)) <= {'nickname','pos','rotate','archetype','parent','loadout'},item.name
            row=dataclasses.replace(item,archetype=item.archetype.lower(),loadout=loadout if loadout!='shipyard' else '')
            vv,hh,ll=builder.expand(row,origin)
            visuals.extend(vv);hulls.extend(hh);libraries.update(ll)
            if loadout=='shipyard':
                _,_,hps=builder.asset(m.b.model_path(m.GAME/'DATA',m.old.one(arch,'da_archetype')))
                for line in builder.loadouts[loadout]['equip']:
                    nick,hp=[s.strip() for s in line.split(',')]
                    assert builder.equipment[nick.lower()]['section']=='light',nick
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
        surf=m.old.surface_file([('Root',hulls)])
        restored=m.old.leaves(dict(dict(m.old.parts(surf))[m.utf.crc('Root')])[b'surf'])
        def hull_key(h):return np.asarray(h.points,dtype='<f4').tobytes(),h.raw[16:]
        assert Counter(map(hull_key,hulls))==Counter(map(hull_key,restored)),key+' collision'
        builder.emit(f'DATA/SOLAR/OPTIMIZED/ulster_megabase/{name}.cmp',raw)
        builder.emit(f'DATA/SOLAR/OPTIMIZED/ulster_megabase/{name}.sur',surf)
        defs.append('\n'.join(['[Solar]',f'nickname = {name}','type = SATELLITE',
            f'DA_archetype = solar\\OPTIMIZED\\ulster_megabase\\{name}.cmp',*[f'material_library = {x}' for x in sorted(libraries)],
            'envmap_material = envmapsolar01','mass = 10000','solar_radius = 100','hit_pts = 1e30',
            *([f'loadout = {name}_lights'] if lights else []),'',*lods]))
        # Keep one original nickname per group; references to removed names are checked below.
        replacements[items[0].name]=(name,origin)
        removed.update(p.name for p in items[1:])
        reports.append(dict(group=key,name=name,origin=origin.tolist(),members=[p.name for p in items],lights=len(lights),hulls=len(hulls),**stats))
        print(key,len(items),'objects -> 1;',stats['draw_groups_before'],'->',stats['draw_groups_after'],'draw groups',flush=True)
    def rewrite(text,offset):
        result=[]
        for block in m.old.blocks(text):
            d=m.old.fields(block);nick=m.old.one(d,'nickname')
            if nick in removed:continue
            if nick in replacements:
                name,origin=replacements[nick]
                result.append('[Object]\nnickname = '+nick+'\npos = '+', '.join(f'{x:g}' for x in origin+offset)+f'\nrotate = 0, 0, 0\narchetype = {name}\nparent = {PREFIX}\n\n')
            else:result.append(block)
        return ''.join(result)
    new_text=rewrite(text,np.zeros(3));new_live=rewrite(live,offset)
    # Root, working dock, battleships, all unrelated objects and zones survive verbatim.
    retained=[b for b in m.old.blocks(live) if m.old.one(m.old.fields(b),'nickname') not in removed|replacements.keys()]
    assert all(b in new_live for b in retained)
    for nick in removed:
        assert not any(nick in line for line in new_live.splitlines() if '=' in line and not line.lstrip().startswith(';')),nick+' reference remains'
    new_source=source.replace('class UlsterMegabase(SpaceObjectTemplate):','class UlsterMegabaseOriginal(SpaceObjectTemplate):',1)
    new_source+="\n\nclass UlsterMegabase(UlsterMegabaseOriginal):\n    TEMPLATE = '''"+new_text+"'''\n"
    compile(new_source,TEMPLATE,'exec')
    template_backup=TEMPLATE.replace('.py','Original.py')
    system_backup=LIVE.replace('.ini','UlsterMegabaseOriginal.ini')
    assert not (m.GAME/template_backup).exists() and not (m.GAME/system_backup).exists()
    builder.emit(template_backup,source_bytes);builder.emit(TEMPLATE,new_source)
    builder.emit(system_backup,live_bytes);builder.emit(LIVE,new_live.replace(PREFIX,'br_wrw_02'))
    builder.emit('DATA/SOLAR/solararch.ini',solar+'\n'+MARK+'\n'+'\n'.join(defs)+'\n; END ULSTER MEGABASE\n')
    builder.emit('DATA/SOLAR/loadouts.ini',loadouts+'\n'+MARK+'\n'+'\n'.join(new_loadouts)+'\n; END ULSTER MEGABASE\n')
    manifest=dict(sources=builder.sources,payload=builder.payload,components=reports,removed=sorted(removed),
        before=len(rows),after=len(rows)-len(removed),offset=offset.tolist(),
        discarded_degenerate_leaves=builder.discarded_degenerate_leaves)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PASS: exact triangles/LODs/SUR, light mounts, template/live equivalence; objects',manifest['before'],'->',manifest['after'])


if __name__=='__main__':build()
