"""Keep the complete shipping dock, but make the station wireframe its root."""
import json
import numpy as np
import valensia_mega as m
from station_docks import direct,entries

def prepare(builder,config,prefix,rows):
    by_name={r.name:r for r in rows};center=by_name[prefix];dock=by_name[prefix+'_dock']
    assert dock.archetype=='space_shipping01'
    name='cambridge_shipping_core'
    arch=builder.solars[dock.archetype];core=builder.solars[center.archetype]
    path=m.b.model_path(m.GAME/'DATA',m.old.one(arch,'da_archetype'))
    header,roots=m.utf.read_tree(builder.read(path));root=roots[0]
    wire=m.utf.read_tree(builder.read(m.b.model_path(m.GAME/'DATA',m.old.one(core,'da_archetype'))))[1][0]
    pose=m.b.compose(m.b.inverse((m.old.euler_matrix(*center.rotate),np.array(center.pos))),
                     (m.old.euler_matrix(*dock.rotate),np.array(dock.pos)))
    r,t=pose;comp=direct(root,'Cmpnd');cons=direct(comp,'Cons');lib=direct(root,'VMeshLibrary')
    mapping={old:('DockRoot' if old=='Root' else old) for old,_ in entries(root)}
    rootpart=direct(root,dict(entries(root))['Root']);hardpoints=m.b.clone(direct(rootpart,'Hardpoints'))
    for category in hardpoints.children:
        for hp in category.children:
            pos=direct(hp,'Position');rot=direct(hp,'Orientation');axis=direct(hp,'Axis')
            if pos:pos.blob=m.S.pack('<3f',*(r@np.array(m.S.unpack('<3f',pos.blob))+t))
            if rot:rot.blob=m.S.pack('<9f',*(r@np.array(m.S.unpack('<9f',rot.blob)).reshape(3,3)).flat)
            if axis:axis.blob=m.S.pack('<3f',*(r@np.array(m.S.unpack('<3f',axis.blob))))
    for index,entry in enumerate([e for e in comp.children if direct(e,'Object name')],1):
        obj=direct(entry,'Object name');file=direct(entry,'File name');old=m.b.text(obj.blob)
        part=direct(root,m.b.text(file.blob));part.name=f'{name}_p{index:02d}.3db'
        part.children=[c for c in part.children if c.name not in ('Hardpoints','VMeshWire')]
        obj.blob=(mapping[old]+'\0').encode();file.blob=(part.name+'\0').encode()
        entry.name='Part'+str(index);direct(entry,'Index').blob=m.S.pack('<I',index)
    for kind in cons.children:
        assert kind.name in ('Fix','Rev');stride=176 if kind.name=='Fix' else 208
        raw=bytearray(kind.blob)
        for start in range(0,len(raw),stride):
            for field in (0,64):
                at=start+field;old=m.b.text(raw[at:at+64]);raw[at:at+64]=mapping[old].encode().ljust(64,b'\0')
        kind.blob=bytes(raw)
    fix=direct(cons,'Fix');fix.blob+=m.mesh.fix_record('Root','DockRoot',r,t)
    for script in direct(direct(root,'Animation'),'Script').children:
        for joint in script.children:
            for key in ('Parent name','Child name'):
                node=direct(joint,key)
                if node:node.blob=(mapping[m.b.text(node.blob)]+'\0').encode()
    newroot=m.utf.Node(name+'_Root.3db')
    newroot.children=[m.b.clone(c) for c in wire.children if c.name in ('MultiLevel','VMeshWire')]+[hardpoints]
    # Each source library gets its own remap before the two are combined.
    for label,library,scope in [('dock',lib,root),('wire',direct(wire,'VMeshLibrary'),newroot)]:
        ids={}
        for i,node in enumerate(library.children):
            old=m.utf.crc(node.name);node.name=f'{name}_{label}{i}.vms';ids[old]=m.utf.crc(node.name)
        for kind in ('VMeshRef','VWireData'):
            for ref in m.b.find(scope,kind):
                raw=bytearray(ref.blob);m.S.pack_into('<I',raw,4,ids[m.S.unpack_from('<I',raw,4)[0]]);ref.blob=bytes(raw)
    lib.children.extend(direct(wire,'VMeshLibrary').children)
    comp.children.insert(1,m.mesh.part_entry('Root','Root',0,newroot.name));root.children.append(newroot)
    sur=m.old.parts(builder.read(path.with_suffix('.sur')));surface=bytearray(b'vers'+m.S.pack('<f',2))
    for ident,chunks in sur:
        hulls=m.old.leaves(dict(chunks)[b'surf']);part=next(n for n in mapping if m.utf.crc(n)==ident)
        if part=='Root':hulls=[m.old.ExactHull(h.points@r.T+t,h.faces,m.utf.crc('Root'),False,h.raw) for h in hulls]
        surface+=m.old.surface_file([(part,hulls)])[8:]
    relative=f'DATA/SOLAR/OPTIMIZED/{name}/{name}'
    builder.emit(relative+'.cmp',m.utf.write_tree(header,[root]));builder.emit(relative+'.sur',bytes(surface))
    props={k:list(v) for k,v in arch.items() if k!='section'}
    props.update(nickname=[name],da_archetype=[f'solar\\OPTIMIZED\\{name}\\{name}.cmp'],radar_wireframe=['true'],shape_name=core['shape_name'])
    props['docking_request_range']=['3000']
    solar='[Solar]\n'+''.join(k+' = '+v+'\n' for k,vs in props.items() for v in vs)
    solar+='[LOD]\nobj = Root\nLODranges = 0, 1\n'
    for part in mapping.values():solar+=f'[LOD]\nobj = {part}\nLODranges = 0, 3000, 50000\n'
    config['overrides']={prefix:dict(archetype=name)};config['omit']=[dock.name]
    report=dict(name=name,root_name=prefix,model=relative+'.cmp',source_model=path.relative_to(m.GAME).as_posix(),layout='shipping',bodies=len(sur),
        ports=[dict(number=i+1,rotation=r.tolist(),position=t.tolist(),source_letter=chr(97+i)) for i in range(8)])
    config['dock_model']=report;(m.OUT/'docks.json').write_text(json.dumps(report,indent=2))
    return [solar],[]
