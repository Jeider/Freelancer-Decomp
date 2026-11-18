"""Aggressive semantic Valensia bake. Does not run Pythonlancer generation."""
import ast
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct as S
import numpy as np
import valensia_optimize as old
import bake_compound as b
import bake_one_part as mesh
import generate_station_lods as utf
import train_sur.build as sur

GAME, REPO = old.GAME, old.REPO
OUT = REPO/'out/stations/valensia_mega'
MARK = '; BEGIN VALENSIA MEGA'


@dataclass
class Visual:
    levels: list
    ranges: tuple
    rotation: np.ndarray
    translation: np.ndarray


class Builder:
    def __init__(self):
        self.sources, self.payload = {}, {}
        self.folder = old.data_folder(GAME, OUT/'stage')
        self.solars, self.equipment, self.loadouts = b.catalog(GAME/'DATA')
        self.assets = {}
        self.embedded = defaultdict(dict)

    def read(self, path):
        raw = path.read_bytes()
        self.sources[path.relative_to(GAME).as_posix()] = old.sha256(raw).hexdigest()
        return raw

    def emit(self, relative, content):
        if isinstance(content, str): content = content.encode('utf-8')
        if relative.startswith('DATA/'):
            self.folder.sync_data_file(relative[5:], content)
        else:
            path = OUT/'stage'/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.payload[relative] = old.sha256(content).hexdigest()

    def asset(self, path):
        if path in self.assets: return self.assets[path]
        root = utf.read_tree(self.read(path))[1][0]
        for node in root.children:
            if node.name.lower() in ('material library','texture library'):
                for entry in node.children:
                    self.embedded[node.name][entry.name] = b.clone(entry)
        library = b.library_meshes(root)
        comp = next((x for x in root.children if x.name.lower() == 'cmpnd'), None)
        nodes, transforms, hp = [], {}, {}
        if comp:
            links = {}
            cons = b.one(comp, 'Cons')
            for kind in cons.children if cons else []:
                is_fix=kind.name.lower()=='fix'
                # polygon.cmp is an unanimated attachment helper in these loadouts.
                stationary = getattr(self, 'stationary_revolute_models', {'polygon.cmp'})
                assert is_fix or (path.name.lower() in stationary and kind.name.lower()=='rev'), (path,kind.name)
                stride=176 if is_fix else 208
                for at in range(0,len(kind.blob),stride):
                    rec=kind.blob[at:at+stride]
                    r=np.array(S.unpack_from('<9f',rec,140 if is_fix else 152)).reshape(3,3)
                    t=np.array(S.unpack_from('<3f',rec,128))
                    if not is_fix: t-=r@np.array(S.unpack_from('<3f',rec,140))
                    links[b.text(rec[64:128])]=(b.text(rec[:64]),r,t)
            def resolve(name):
                if name in transforms: return transforms[name]
                if name not in links: result = (np.eye(3), np.zeros(3))
                else:
                    parent, r, t = links[name]
                    result = b.compose(resolve(parent), (r,t))
                transforms[name] = result
                return result
            for entry in comp.children:
                name, file = b.one(entry,'Object name'), b.one(entry,'File name')
                if name and file:
                    nodes.append((b.one(root,b.text(file.blob)), *resolve(b.text(name.blob))))
        else:
            nodes = [(root, np.eye(3), np.zeros(3))]
        visuals = []
        for node,r,t in nodes:
            for name, transform in b.hardpoints(node).items(): hp[name] = b.compose((r,t),transform)
            multi = next((c for c in node.children if c.name.lower()=='multilevel'),None)
            levels = sorted((c for c in multi.children if c.name.lower().startswith('level')),key=lambda c:int(c.name[5:])) if multi else [node]
            # Some stock models (space_control_tower) have a Switch2-only
            # MultiLevel stub; their actual geometry is the direct VMeshPart.
            if not levels:
                levels = [node]
            parsed = []
            for level in levels:
                ref = b.one(level,'VMeshRef')
                if not ref: continue
                ident = S.unpack_from('<I',ref.blob,4)[0]
                base,nv,si,ni,sg,ng = S.unpack_from('<6H',ref.blob,8)
                groups, verts = mesh.read_mesh(b.one(library[ident],'VMeshData').blob)
                selected = []
                for mat,lo,hi,unused,ids in groups[sg:sg+ng]:
                    absolute = [base+lo+i for i in ids]
                    assert all(base<=i<base+nv for i in absolute)
                    selected.append((mat,absolute))
                assert sum(len(ids) for _,ids in selected)==ni
                parsed.append((selected,verts))
            assert parsed or not list(b.find(node,'VMeshRef')), (path,'unconsumed visual geometry')
            if parsed: visuals.append((parsed,r,t))
        collision = []
        surface_path = path.with_suffix('.sur')
        if surface_path.exists():
            sections = dict(old.parts(self.read(surface_path)))
            root_id = utf.crc('Root') if comp else 0
            assert root_id in sections, (path,list(sections))
            collision = old.leaves(dict(sections[root_id])[b'surf'])
            from station_collision_parts import active_port_hulls
            collision = active_port_hulls(root,collision)
        self.assets[path] = visuals,collision,hp
        return self.assets[path]

    def expand(self, row, origin):
        visuals,hulls,libraries = [],[],set()
        def add(spec,r,t):
            path = b.model_path(GAME/'DATA',old.one(spec,'da_archetype'))
            items,collision,hp = self.asset(path)
            ranges = tuple(mesh.floats(old.one(spec,'lodranges','0, 30000')))
            for levels,lr,lt in items:
                wr,wt = b.compose((r,t),(lr,lt))
                used = min(len(levels),len(ranges)-1)
                assert used>0, path
                visuals.append(Visual(levels[:used],ranges[:used+1],wr,wt-origin))
            hulls.extend(old.ExactHull(h.points@r.T+t-origin,h.faces,utf.crc('Root'),False,h.raw) for h in collision)
            libraries.update(spec.get('material_library',[]))
            return hp
        r,t = old.euler_matrix(*row.rotate),np.array(row.pos)
        arch = self.solars[row.archetype]
        hp = add(arch,r,t)
        if row.loadout:
            loadout = self.loadouts[row.loadout.lower()]
            for line in loadout.get('equip',[]):
                nick,hardpoint = [s.strip() for s in line.split(',')[:2]]
                eq = self.equipment[nick.lower()]
                assert eq['section']=='cargopod' and not old.one(eq,'loadout'), (nick,eq)
                child = self.asset(b.model_path(GAME/'DATA',old.one(eq,'da_archetype')))
                anchor = child[2].get(old.one(eq,'hp_child','HpRoot').lower(),(np.eye(3),np.zeros(3)))
                er,et = b.compose((r,t),b.compose(hp[hardpoint.lower()],b.inverse(anchor)))
                add(eq,er,et)
        return visuals,hulls,libraries


def packed_meshes(visuals, level):
    by_material = defaultdict(list)
    before = 0
    for visual in visuals:
        groups,verts = visual.levels[level]
        transformed = [mesh.xform_vert(v,visual.rotation,visual.translation) for v in verts]
        for material,ids in groups:
            before += 1
            by_material[material].extend(transformed[i] for i in ids)
    # Material batches with tight vertex slices, bounded by UTF's 16-bit limits.
    chunks,groups,verts,total = [],[],[],0
    def flush():
        nonlocal groups,verts,total
        if groups:
            chunks.append(mesh.write_mesh(groups,verts))
            groups,verts,total = [],[],0
    for material,triangle_vertices in sorted(by_material.items()):
        offset = 0
        while offset<len(triangle_vertices):
            available = (60000-total)//3*3
            if not available: flush(); continue
            raw = triangle_vertices[offset:offset+available]
            unique = list(dict.fromkeys(raw))
            if len(verts)+len(unique)>60000: flush(); continue
            base = len(verts)
            mapping = {v:i for i,v in enumerate(unique)}
            indices = [mapping[v] for v in raw]
            groups.append((material,base,base+len(unique)-1,204,indices))
            verts.extend(unique)
            total += len(indices)
            offset += len(raw)
    flush()
    return chunks,before


def mesh_ref(ident,blob):
    raw = bytearray(mesh.ref_bytes(ident,blob))
    groups,verts = mesh.read_mesh(blob)
    lo,hi,_,_ = mesh.bounds(verts)
    S.pack_into('<6f',raw,20,hi[0],lo[0],hi[1],lo[1],hi[2],lo[2])
    return bytes(raw)


def write_cmp(name,visuals):
    root,library,comp = utf.Node('\\'),utf.Node('VMeshLibrary'),utf.Node('Cmpnd')
    root.children = [library,comp]
    cohorts = defaultdict(list)
    for visual in visuals: cohorts[visual.ranges].append(visual)
    entries,fix,lods = [],bytearray(),[]
    before,after,triangles = 0,0,0
    for ranges,items in sorted(cohorts.items()):
        all_levels = [packed_meshes(items,i) for i in range(len(ranges)-1)]
        before += all_levels[0][1]
        after += sum(S.unpack_from('<H',blob,8)[0] for blob in all_levels[0][0])
        triangles += sum(S.unpack_from('<H',blob,10)[0]//3 for blob in all_levels[0][0])
        # Each level can have a different chunk count: separate fixed mesh part
        # per chunk, with absent levels represented by an empty Level node.
        for chunk in range(max(len(blobs) for blobs,_ in all_levels)):
            index = len(entries)
            partname = 'Root' if not index else f'batch{index:02d}'
            # EngBase caches nested archetypes globally by this filename's CRC,
            # not by (parent CMP, filename). Generic Root.3db aliases other models.
            file = name+'_'+partname+'.3db'
            node,multi = utf.Node(file),utf.Node('MultiLevel')
            node.children=[multi]
            multi.children.append(utf.Node('Switch2',S.pack('<'+'f'*len(ranges),*ranges)))
            for level,(blobs,_) in enumerate(all_levels):
                levelnode = utf.Node(f'Level{level}')
                multi.children.append(levelnode)
                if chunk>=len(blobs): continue
                blob = blobs[chunk]
                meshname = f'{name}_{index:02d}_{level}.vms'
                entry = utf.Node(meshname)
                entry.children=[utf.Node('VMeshData',blob)]
                library.children.append(entry)
                vpart = utf.Node('VMeshPart')
                vpart.children=[utf.Node('VMeshRef',mesh_ref(utf.crc(meshname),blob))]
                levelnode.children=[vpart]
            root.children.append(node)
            entries.append(mesh.part_entry('Root' if not index else f'Part{index}',partname,index,file))
            if index: fix.extend(mesh.fix_record('Root',partname,np.eye(3),np.zeros(3)))
            lods.append(f'[LOD]\nobj = {partname}\nLODranges = '+', '.join(f'{x:g}' for x in ranges)+'\n')
    cons = utf.Node('Cons')
    if fix: cons.children=[utf.Node('Fix',bytes(fix))]
    comp.children=[cons,*entries]
    header=[0x20465455,0x101,0,0,0,44,0,0,0,0,0,0,0,0]
    return utf.write_tree(header,[root]),lods,dict(draw_groups_before=before,draw_groups_after=after,triangles=triangles,mesh_parts=len(entries))


def group_name(row):
    token = next((s for s in row.name.split('_') if s.isupper()),'')
    return {'L5':'TOP','L6':'BOTTOM','L7':'WAIST','L8':'WAIST'}.get(token,token) if token in ('TOP','BOTTOM',*[f'L{i}' for i in range(1,9)]) else None


def optimize(builder,text,label,prefix=None):
    rows=b.placements_from_template(text)
    selected=[p for p in rows if not prefix or p.name.startswith(prefix)]
    groups=defaultdict(list)
    for row in selected:
        group=group_name(row)
        if group: groups[group].append(row)
    planets=[p for p in selected if p.archetype.startswith('sw_center')]
    replacements,removed,defs,report={},set(),[],[]
    for group,items in groups.items():
        center=np.mean([p.pos for p in items],axis=0)
        anchor=min(planets,key=lambda p:np.linalg.norm(np.array(p.pos)-center))
        origin=np.array(anchor.pos)
        name=f'vlm_{label}_{group.lower()}'
        visuals,hulls,libraries=[],[],set()
        for item in items:
            vv,hh,ll=builder.expand(item,origin)
            visuals.extend(vv);hulls.extend(hh);libraries.update(ll)
        raw,lods,stats=write_cmp(name,visuals)
        header,roots=utf.read_tree(raw)
        for library_label,entries in builder.embedded.items():
            node=utf.Node(library_label)
            node.children=[b.clone(entry) for entry in entries.values()]
            roots[0].children.append(node)
        raw=utf.write_tree(header,roots)
        builder.emit(f'DATA/SOLAR/OPTIMIZED/valensia_mega/{name}.cmp',raw)
        builder.emit(f'DATA/SOLAR/OPTIMIZED/valensia_mega/{name}.sur',old.surface_file([('Root',hulls)]))
        defs.append('\n'.join(['[Solar]',f'nickname = {name}','type = SATELLITE',
            f'da_archetype = solar\\OPTIMIZED\\valensia_mega\\{name}.cmp',
            *[f'material_library = {lib}' for lib in sorted(libraries)],
            'envmap_material = envmapsolar01','mass = 10000','hit_pts = 1e30','solar_radius = 100',
            '',*lods]))
        first=items[0]
        replacements[first.name]='\n'.join(['[Object]',f'nickname = {first.name}',
            'pos = '+', '.join(f'{x:g}' for x in origin),'rotate = 0, 0, 0',
            f'archetype = {name}',f'parent = {first.parent}','\n'])
        removed.update(p.name for p in items[1:])
        report.append(dict(name=name,group=group,origin=origin.tolist(),planet=anchor.name,
                           members=[p.name for p in items],hulls=len(hulls),**stats))
    result=''.join('' if old.one(old.fields(block),'nickname') in removed else replacements.get(old.one(old.fields(block),'nickname'),block) for block in old.blocks(text))
    return result,defs,dict(before=len(selected),after=len(selected)-len(removed),components=report)


def main():
    builder=Builder()
    original=builder.read(GAME/old.ORIGINAL_TEMPLATE).decode('utf-8-sig')
    current=builder.read(GAME/old.TEMPLATE)
    builder.emit(old.TEMPLATE.replace('.py','PairsOriginal.py'),current)
    appended,defs,reports=[],[],{}
    renamed=original
    for cls in ast.parse(original).body:
        if not isinstance(cls,ast.ClassDef): continue
        value=next(m.value for m in cls.body if isinstance(m,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEMPLATE' for t in m.targets))
        optimized,d,r=optimize(builder,ast.literal_eval(value),'v1' if cls.name=='ValensiaOutside' else 'v2')
        renamed=renamed.replace(f'class {cls.name}(SpaceObjectTemplate):',f'class {cls.name}Original(SpaceObjectTemplate):',1)
        appended.append(f"\n\nclass {cls.name}({cls.name}Original):\n    TEMPLATE = '''"+optimized+"'''\n")
        defs.extend(d);reports[cls.name]=r
    updated=renamed+''.join(appended)
    compile(updated,old.TEMPLATE,'exec')
    builder.emit(old.TEMPLATE,updated)
    live=builder.read(GAME/'DATA'/old.LIVE)
    builder.emit('DATA/'+old.LIVE.replace('.ini','PairsOriginal.ini'),live)
    original_live=builder.read(GAME/'DATA'/old.LIVE.replace('.ini','Original.ini')).decode('utf-8-sig')
    optimized,d,r=optimize(builder,original_live,'hq','or_hq_station_1')
    defs.extend(d);reports['or_hq_live']=r
    builder.emit('DATA/'+old.LIVE,optimized)
    solar=builder.read(GAME/'DATA/SOLAR/solararch.ini').decode('utf-8-sig')
    assert MARK not in solar
    builder.emit('DATA/SOLAR/solararch.ini',solar+'\n'+MARK+'\n'+'\n'.join(defs)+'\n; END VALENSIA MEGA\n')
    manifest=dict(sources=builder.sources,payload=builder.payload,reports=reports)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    for name,r in reports.items(): print(name,r['before'],'->',r['after'],flush=True)


if __name__=='__main__': main()
