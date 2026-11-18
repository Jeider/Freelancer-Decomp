"""Content-only station batch: exact geometry, bounded static colliders, retained behavior."""
import dataclasses
import re
import os
from collections import Counter, defaultdict
import json
import numpy as np
import valensia_mega as m
from check_valensia_mega import templates
from fix_valensia_towers import decoded, expected
from terraform_mega import hp_node

CONFIG=json.loads(os.environ['STATION_BATCH_CONFIG'])
TASK=CONFIG['task']; CLASS=CONFIG['class']; SOURCE_PREFIX=CONFIG['source_prefix']
ASSET_PREFIX=TASK if len(TASK)<=24 else TASK[:15]+'_'+format(m.utf.crc(TASK),'08x')
HULL_LIMIT=int(CONFIG.get('max_hulls',1500))
OUT=m.REPO/'out/stations/station_batch'/TASK
TEMPLATE=CONFIG['template']; LIVE=CONFIG['instances'][0]['path']
PREFIX='__'+TASK
MARK='; BEGIN '+TASK.upper()
RETAIN={}
GROUPS={}


def source_text(source):
    if not CONFIG.get('static'):
        parsed=templates(source)
        return parsed[CLASS+'Original' if CONFIG.get('rebuild') else CLASS]
    if re.search(r'(?m)^nickname = divider\r?$',source):
        from sync_story_dev import split_dev
        source=split_dev(source.encode('utf-8'))[0].decode('utf-8')
    return ''.join(block for block in m.old.blocks(source)
        if (lambda name:name==SOURCE_PREFIX or name.startswith(SOURCE_PREFIX+'_'))(m.old.one(m.old.fields(block),'nickname'))
        and block.lstrip().lower().startswith('[object]'))


class Builder(m.Builder):
    def __init__(self):
        super().__init__()
        self.discarded_degenerate_leaves=[]
        self.collect_used=False
        self.used_surfaces=set()

    def emit(self,relative,content):
        if CONFIG.get('rebuild') and (m.GAME/relative).exists():self.read(m.GAME/relative)
        super().emit(relative,content)

    def asset(self,path):
        if self.collect_used and path.with_suffix('.sur').exists():
            self.used_surfaces.add(path.with_suffix('.sur').relative_to(m.GAME).as_posix())
        if path in self.assets:return self.assets[path]
        visuals,hulls,hp=super().asset(path)
        if path.name.lower() in CONFIG.get('repair_panel_normals',[]):
            from repair_panel_normals import repair_parsed
            corrected=[];changed=0
            for levels,r,t in visuals:
                repaired=[]
                for groups,vertices in levels:
                    level,count=repair_parsed(groups,vertices);repaired.append(level);changed+=count
                corrected.append((repaired,r,t))
            visuals=corrected
            print('Panel normals:',path.name,changed,'corrected corners',flush=True)
        # Do not leave an unvalidated result cached when validation rejects it.
        self.assets.pop(path,None)
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
    return GROUPS.get(row.name)


def classify(builder,text):
    blocks={m.old.one(m.old.fields(b),'nickname'):b for b in m.old.blocks(text)}
    rows=m.b.placements_from_template(text)
    for row in rows:
        try:
            assert row.name not in CONFIG.get('retain',[]), 'preserved after precision audit'
            assert row.name not in CONFIG.get('omit',[]), 'replaced by working dock'
            assert row.name.startswith(PREFIX+'_'), 'independently named object'
            block=blocks[row.name];props=m.old.fields(block)
            assert row.name!=PREFIX and '{' not in block, 'functional root/dock'
            assert set(props)<={'nickname','pos','rotate','archetype','parent','loadout'}, 'object behavior'
            arch=builder.solars[row.archetype.lower()]
            assert not arch.get('docking_sphere'), 'working dock'
            loadout=row.loadout or m.old.one(arch,'loadout')
            lights=[];cargo=[]
            for line in builder.loadouts.get(loadout,{}).get('equip',[]):
                fields=[x.strip() for x in line.split(',')]
                assert len(fields)==2, 'equipment arguments'
                eq=builder.equipment[fields[0].lower()]
                assert eq['section'] in ('light','attachedfx','cargopod'), 'functional equipment '+fields[0]
                (cargo if eq['section']=='cargopod' else lights).append(line)
            assert not loadout or loadout in builder.loadouts, 'unknown loadout'
            assert not loadout or set(builder.loadouts[loadout])<={'section','nickname','equip'}, 'loadout behavior'
            # The old expander safely handles static cargo. Probe before grouping;
            # dynamic constraints/unknown attachments stay as original objects.
            probe=dataclasses.replace(row,archetype=row.archetype.lower(),loadout='')
            if cargo:
                probe=dataclasses.replace(probe,loadout='__probe')
                builder.loadouts['__probe']={'equip':cargo}
            _,probe_hulls,_=builder.expand(probe,np.zeros(3))
            assert len(probe_hulls)<=3000, 'large original collider retained'
            if probe_hulls:
                points=np.concatenate([h.points for h in probe_hulls])-np.array(row.pos)
                assert np.abs(points).max()<16000, 'outlying original collider retained'
            path=m.b.model_path(m.GAME/'DATA',m.old.one(arch,'da_archetype'))
            assert path.with_suffix('.sur').exists(), 'native fallback collision'
            for ident,chunks in m.old.parts(path.with_suffix('.sur').read_bytes()):
                assert ident in (0,m.utf.crc('Root')) or b'!fxd' not in dict(chunks), 'separate physical child'
            hps=builder.asset(path)[2]
            assert all(line.split(',')[1].strip().lower() in hps for line in lights), 'missing light mount'
            suffix=row.name[len(PREFIX)+1:];token=suffix.split('_')[0]
            key=token if token.isupper() and not token[-1:].isdigit() else (token if re.fullmatch(r'[A-Z][0-9]',token) else 'STRUCTURE')
            GROUPS[row.name]=key
        except (AssertionError,KeyError,ValueError) as exc:
            RETAIN[row.name]=str(exc)
    # Preserve every nickname referenced by another object or system section.
    for block in m.old.blocks(text):
        d=m.old.fields(block)
        for key,values in d.items():
            if key in ('nickname','parent'):continue
            for value in values:
                if value in GROUPS:
                    RETAIN[value]='referenced by '+key;GROUPS.pop(value)
    # Other system/mission INIs can target station subobjects by nickname.
    # Keep such nodes intact, including references in dev source systems.
    for inst in CONFIG['instances']:
        names={name.replace(PREFIX,inst['prefix']):name for name in GROUPS}
        if not names:continue
        pattern=re.compile(r'(?<![A-Za-z0-9_])(?:'+'|'.join(map(re.escape,names))+r')(?![A-Za-z0-9_])')
        live_path=(m.GAME/inst['path']).resolve()
        for path in (m.GAME/'DATA').rglob('*.ini'):
            if path.resolve() in (live_path,(m.GAME/TEMPLATE).resolve()) or 'original' in path.name.lower():continue
            content=path.read_text(encoding='utf-8-sig',errors='replace')
            if inst['prefix'] not in content:continue
            # Definitions in an independent historical/static copy are not references.
            content=re.sub(r'(?mi)^\s*nickname\s*=.*$','',content)
            for match in pattern.finditer(content):
                name=names[match[0]]
                RETAIN[name]='external reference: '+path.relative_to(m.GAME).as_posix()
                GROUPS.pop(name,None)
    # Bound generic groups spatially, preserving semantic labels where present.
    grouped=defaultdict(list)
    for row in rows:
        if row.name in GROUPS:grouped[GROUPS[row.name]].append(row)
    for key,items in grouped.items():
        index=[0]
        def split(items):
            xyz=np.array([r.pos for r in items]);span=np.ptp(xyz,axis=0)
            if span.max()>2400 and len(items)>1:
                ordered=sorted(items,key=lambda r:r.pos[int(np.argmax(span))]);mid=len(ordered)//2
                split(ordered[:mid]);split(ordered[mid:]);return
            name=key+str(index[0]);index[0]+=1
            for row in items:GROUPS[row.name]=name
        split(items)



def build():
    m.OUT=OUT
    builder=Builder()
    source_bytes=builder.read(m.GAME/TEMPLATE)
    source=source_bytes.decode('utf-8-sig')
    text=unique_names(source_text(source).replace(SOURCE_PREFIX,PREFIX))
    assert CONFIG.get('static') or '{root_props}' in text or '{dock_props}' in text, 'decorative debris, no station root/dock'
    lives=[]
    rows=m.b.placements_from_template(text)
    for inst in CONFIG['instances']:
        live_bytes=builder.read(m.GAME/inst['path'])
        if CONFIG.get('rebuild'):
            original=builder.read(m.GAME/inst['path'].replace('.ini',CLASS+'Original.ini')).decode('utf-8-sig')
            def target(block):
                name=m.old.one(m.old.fields(block),'nickname')
                return block.lstrip().lower().startswith('[object]') and (name==inst['prefix'] or name.startswith(inst['prefix']+'_'))
            restored=''.join(b for b in m.old.blocks(live_bytes.decode('utf-8-sig')) if not target(b))+'\n\n'+''.join(b for b in m.old.blocks(original) if target(b))
            live_working=restored
        else:live_working=live_bytes.decode('utf-8-sig')
        live=unique_names(live_working.replace(inst['prefix'],PREFIX))
        live_rows={p.name:p for p in m.b.placements_from_template(live)}
        assert {p.name for p in rows}<=set(live_rows),inst
        offset=np.array(live_rows[rows[0].name].pos)-rows[0].pos
        for p in rows:
            q=live_rows[p.name]
            assert np.allclose(np.array(p.pos)+offset,q.pos,atol=1e-4,rtol=0),p.name
            assert (p.rotate,p.archetype.lower(),p.loadout)==(q.rotate,q.archetype.lower(),q.loadout),p.name
        lives.append((inst,live_bytes,live,offset))
    solar=builder.read(m.GAME/'DATA/SOLAR/solararch.ini').decode('utf-8-sig')
    loadouts=builder.read(m.GAME/'DATA/SOLAR/loadouts.ini').decode('utf-8-sig')
    if CONFIG.get('rebuild'):
        pattern=r'(?ms)^'+re.escape(MARK)+r'\r?\n.*?^; END '+re.escape(TASK.upper())+r'\r?\n'
        solar,n=re.subn(pattern,'',solar);assert n==1
        loadouts,n=re.subn(pattern,'',loadouts);assert n==1
    else:assert not re.search(r'(?m)^'+re.escape(MARK)+r'\r?$',solar)
    dock_defs=[];dock_loadouts=[]
    if CONFIG.get('docks'):
        from station_docks import prepare
        dock_defs,dock_loadouts=prepare(builder,CONFIG,PREFIX,rows)
    if CONFIG.get('panel_rotors'):
        from station_panel_rotors import prepare
        dock_defs,dock_loadouts=prepare(builder,CONFIG,PREFIX,rows)
    classify(builder,text)
    (OUT/'classification.json').write_text(json.dumps(dict(groups=GROUPS,retained=RETAIN),indent=2))
    print('Classified:',len(GROUPS),'static objects;',len(RETAIN),'retained',flush=True)
    groups=defaultdict(list)
    for row in rows:
        key=group(row)
        if key:groups[key].append(row)
    defs,new_loadouts,reports=list(dock_defs),list(dock_loadouts),[]
    replacements={};removed=set(CONFIG.get('omit',[]))
    unstable_members=set()
    builder.collect_used=True
    for key,items in groups.items():
        name=ASSET_PREFIX+'_'+key.lower()
        hull_limit=next((limit for prefix,limit in sorted(CONFIG.get('group_hull_limits',{}).items(),key=lambda x:-len(x[0])) if key.startswith(prefix)),HULL_LIMIT)
        positions=np.array([p.pos for p in items]);origin=(positions.min(0)+positions.max(0))/2
        visuals,hulls,libraries=[],[],set();lights=[];bodies=[]
        for index,item in enumerate(items):
            arch=builder.solars[item.archetype.lower()]
            assert not arch.get('docking_sphere'),item.name
            loadout=item.loadout or m.old.one(arch,'loadout')
            # Props may add nonvisual behavior; refuse unexpected object settings.
            block=next(b for b in m.old.blocks(text) if m.old.one(m.old.fields(b),'nickname')==item.name)
            assert set(m.old.fields(block)) <= {'nickname','pos','rotate','archetype','parent','loadout'},item.name
            lines=builder.loadouts.get(loadout,{}).get('equip',[])
            cargo=[line for line in lines if builder.equipment[line.split(',')[0].strip().lower()]['section']=='cargopod']
            fx=[line for line in lines if line not in cargo]
            builder.loadouts['__cargo']={'equip':cargo}
            row=dataclasses.replace(item,archetype=item.archetype.lower(),loadout='__cargo' if cargo else '')
            vv,hh,ll=builder.expand(row,origin)
            visuals.extend(vv);hulls.extend(hh);libraries.update(ll)
            bodies.append((item.name,hh))
            if fx:
                _,_,hps=builder.asset(m.b.model_path(m.GAME/'DATA',m.old.one(arch,'da_archetype')))
                for line in fx:
                    nick,hp=[s.strip() for s in line.split(',')]
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
            if chunk and sum(len(h) for _,h in chunk)+len(hh)>hull_limit:
                chunks.append(chunk);chunk=[]
            chunk.append((member,hh))
        if chunk:chunks.append(chunk)
        bounded=[]
        def partition(entries):
            if len(entries)<=hull_limit:
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
            def deviation(points,faces):
                a,b,c=[points[faces[:,i]] for i in range(3)]
                normal=np.cross(b-a,c-a);length=np.linalg.norm(normal,axis=1)
                if np.any(length<=1e-9):return float('inf')
                return float(((normal@points.T-(normal*a).sum(1)[:,None])/length[:,None]).max())
            unstable=[]
            for member,hh in chunk:
                for h in hh:
                    points=h.points-pivot
                    if deviation(points.astype('<f4').astype(float),h.faces)>deviation(points,h.faces)+.005:
                        unstable.append(member);break
            if unstable:
                unstable_members.update(unstable)
            proxy=name+f'_collision{index:02d}'
            # An empty render part supplies an instance and its solid SUR only.
            head,tree=m.utf.read_tree(raw);root=tree[0]
            lib=m.utf.Node('VMeshLibrary');cmp=m.utf.Node('Cmpnd')
            file=proxy+'_Root.3db';node=m.utf.Node(file);node.children=[m.utf.Node('MultiLevel')]
            assert len(file.encode('ascii'))<64, 'native part filename limit'
            cmp.children=[m.utf.Node('Cons'),m.mesh.part_entry('Root','Root',0,file)]
            root.children=[lib,cmp,node]
            builder.emit(f'DATA/SOLAR/OPTIMIZED/{TASK}/{proxy}.cmp',m.utf.write_tree(head,tree))
            data=m.old.surface_file([('Root',local)])
            restored=m.old.leaves(dict(dict(m.old.parts(data))[m.utf.crc('Root')])[b'surf'])
            def hull_key(h):return np.asarray(h.points,dtype='<f4').tobytes(),h.raw[16:]
            assert Counter(map(hull_key,local))==Counter(map(hull_key,restored))
            builder.emit(f'DATA/SOLAR/OPTIMIZED/{TASK}/{proxy}.sur',data)
            defs.append('[Solar]\nnickname = '+proxy+'\ntype = SATELLITE\nDA_archetype = solar\\OPTIMIZED\\'+TASK+'\\'+proxy+'.cmp\nmass = 10000\nsolar_radius = 1\nhit_pts = 1e30\n')
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
        builder.emit(f'DATA/SOLAR/OPTIMIZED/{TASK}/{name}.cmp',raw)
        builder.emit(f'DATA/SOLAR/OPTIMIZED/{TASK}/{name}.sur',surf)
        defs.append('\n'.join(['[Solar]',f'nickname = {name}','type = SATELLITE',
            f'DA_archetype = solar\\OPTIMIZED\\{TASK}\\{name}.cmp',*[f'material_library = {x}' for x in sorted(libraries)],
            'envmap_material = envmapsolar01','mass = 10000','solar_radius = 1','hit_pts = 1e30','phantom_physics = true',
            *([f'loadout = {name}_lights'] if lights else []),'',*lods]))
        # Keep one original nickname per group; references to removed names are checked below.
        replacements[items[0].name]=(name,origin)
        removed.update(p.name for p in items[1:])
        reports.append(dict(group=key,name=name,origin=origin.tolist(),members=[p.name for p in items],lights=len(lights),hulls=len(hulls),bodies=body_report,**stats))
        print(key,len(items),'objects -> 1;',stats['draw_groups_before'],'->',stats['draw_groups_after'],'draw groups',flush=True)
    def rewrite(text,offset):
        result=[]
        if CONFIG.get('unified_core'):
            from station_docks import unite_core
            text=unite_core(text,PREFIX)
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
                nickname=PREFIX+'_col_'+body['name'][len(ASSET_PREFIX)+1:]
                assert all(len(nickname.replace(PREFIX,i['prefix']))<64 for i in CONFIG['instances'])
                result.append('[Object]\nnickname = '+nickname+'\npos = '+', '.join(f'{x:.9g}' for x in pos)+'\nrotate = 0, 0, 0\narchetype = '+body['name']+'\nparent = '+PREFIX+'\n\n')
        rewritten=''.join(result)
        result=[]
        for block in m.old.blocks(rewritten):
            nick=m.old.one(m.old.fields(block),'nickname')
            for key,value in CONFIG.get('overrides',{}).get(nick,{}).items():
                if key in ('pos','rotate'):
                    value=', '.join(f'{v:.9g}' for v in (np.array(value)+(offset if key=='pos' else 0)))
                assert re.search(r'(?mi)^'+key+r'\s*=',block)
                block=re.sub(r'(?mi)^'+key+r'\s*=[^\r\n]*',key+' = '+value,block)
            result.append(block)
        return ''.join(result)
    if unstable_members:
        (OUT/'precision_retained.json').write_text(json.dumps(sorted(unstable_members)))
        raise AssertionError('float32 collision precision: preserve '+str(sorted(unstable_members)))
    new_text=rewrite(text,np.zeros(3)).replace(PREFIX,SOURCE_PREFIX)
    assert len(m.b.placements_from_template(new_text)) < len(rows), 'no object reduction'
    for inst,live_bytes,live,offset in lives:
        new_live=rewrite(live,offset)
        retained=[b for b in m.old.blocks(live) if m.old.one(m.old.fields(b),'nickname') not in removed|replacements.keys()|CONFIG.get('overrides',{}).keys()
                  and not (CONFIG.get('unified_core') and re.search(r'(?m)^parent\s*=\s*'+re.escape(PREFIX+'_dock')+r'\s*$',b))]
        assert all(b in new_live for b in retained)
        for nick in removed:
            assert not any(re.search(r'(?<![A-Za-z0-9_])'+re.escape(nick)+r'(?![A-Za-z0-9_])',line) for line in new_live.splitlines() if '=' in line and not line.lstrip().startswith(';')),nick+' reference remains'
        backup=inst['path'].replace('.ini',CLASS+'Original.ini')
        if not CONFIG.get('rebuild'):
            assert not (m.GAME/backup).exists()
            builder.emit(backup,live_bytes)
        builder.emit(inst['path'],new_live.replace(PREFIX,inst['prefix']))
    if CONFIG.get('static'):
        from sync_story_dev import split_dev,generator_static,semantic
        prefix,tail=split_dev(source_bytes)
        transformed=rewrite(unique_names(prefix.decode('utf-8-sig').replace(SOURCE_PREFIX,PREFIX)),np.zeros(3)).replace(PREFIX,SOURCE_PREFIX)
        new_source=transformed.encode('utf-8')+tail
        assert split_dev(new_source)[1]==tail
        projected=source_text(generator_static(new_source))
        if semantic(projected)!=semantic(new_text):
            import difflib
            (OUT/'dev_projection.diff').write_text('\n'.join(difflib.unified_diff(semantic(new_text),semantic(projected))))
            raise AssertionError('dev station projection differs; inspect dev_projection.diff')
        staged_live=(OUT/'stage'/LIVE).read_text(encoding='utf-8-sig')
        assert semantic(generator_static(new_source))==semantic(staged_live), 'dev/live roundtrip'
        template_backup=TEMPLATE.replace('.ini',CLASS+'Original.ini')
    else:
        if CONFIG.get('rebuild'):
            import ast
            cls=next(c for c in ast.parse(source).body if isinstance(c,ast.ClassDef) and c.name==CLASS)
            member=next(n for n in cls.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEMPLATE' for t in n.targets))
            lines=source.splitlines(keepends=True)
            new_source=''.join(lines[:member.lineno-1])+"    TEMPLATE = '''"+new_text+"'''\n"+''.join(lines[member.end_lineno:])
        else:
            new_source,n=re.subn(r'class '+CLASS+r'\(', 'class '+CLASS+'Original(',source,count=1)
            assert n==1 and CLASS+'Original' not in templates(source)
            assert "'''" not in new_text
            new_source+="\n\nclass "+CLASS+"("+CLASS+"Original):\n    TEMPLATE = '''"+new_text+"'''\n"
        compile(new_source,TEMPLATE,'exec')
        template_backup=TEMPLATE.replace('.py','Original.py')
    if not (m.GAME/template_backup).exists():builder.emit(template_backup,source_bytes)
    builder.emit(TEMPLATE,new_source)
    builder.emit('DATA/SOLAR/solararch.ini',solar+'\n'+MARK+'\n'+'\n'.join(defs)+'\n; END '+TASK.upper()+'\n')
    builder.emit('DATA/SOLAR/loadouts.ini',loadouts+'\n'+MARK+'\n'+'\n'.join(new_loadouts)+'\n; END '+TASK.upper()+'\n')
    manifest=dict(sources=builder.sources,payload=builder.payload,components=reports,removed=sorted(removed),
        config=CONFIG,retained=RETAIN,before=len(rows),after=len(rows)-len(removed)+sum(len(r['bodies']) for r in reports),offset=offset.tolist(),
        used_surfaces=sorted(builder.used_surfaces),
        discarded_degenerate_leaves=[d for d in builder.discarded_degenerate_leaves if d['source'] in builder.used_surfaces])
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PASS: exact triangles/LODs/SUR, light mounts, template/live equivalence; objects',manifest['before'],'->',manifest['after'])


if __name__=='__main__':build()


