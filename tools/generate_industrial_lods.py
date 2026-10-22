"""Generate two coarse LODs for audited custom, single-LOD industrial models.

Consumes the read-only audit in src/obj; writes reviewable models and a manifest
under bin/industrial_lods. Does not install or modify runtime input files.
"""
import collections
import ctypes as C
import hashlib
import json
import re
import struct as S
from pathlib import Path
from generate_station_lods import Node,read_tree,write_tree,child,crc,simplify
from repair_panel_normals import leaves,triangles

DATA=Path('D:/games/FL_MOD/DATA')
OUT=Path('bin/industrial_lods')


def sha(data):return hashlib.sha256(data).hexdigest()


def geometry(blob):
    h=S.unpack_from('<II4H',blob)
    expected=16+12*h[2]+2*h[3]+32*h[-1]
    if expected<len(blob)<=expected+3 and not any(blob[expected:]):return blob[:expected]
    return blob


def library_main(root):
    ref=child(child(root,'VMeshPart'),'VMeshRef').blob
    key=S.unpack_from('<I',ref,4)[0]
    mesh=next(n for n in child(root,'VMeshLibrary').children if crc(n.name)==key)
    return ref,mesh,child(mesh,'VMeshData').blob


def generate_one(relative,dll,levels=((1,.65,.025),(2,.40,.04)),mesh_transform=None,
                 simplify_options=None,preview_root=Path('src/obj/industrial_previews')):
    source=DATA/relative;data=source.read_bytes();header,roots=read_tree(data);root=roots[0]
    empty_ml=next((n for n in root.children if n.name.lower()=='multilevel'),None)
    if empty_ml:
        assert all(n.name.lower()=='switch2' for n in empty_ml.children), 'Existing render LODs are out of scope'
        root.children.remove(empty_ml)
    ref,mesh,original=library_main(root)
    assert not mesh.name.lower().startswith('data.solar.'), 'Retail mesh is out of scope'
    changed_mesh=None;repairs=[]
    if mesh_transform:
        original,repairs=mesh_transform(original)
        child(mesh,'VMeshData').blob=original;changed_mesh=mesh.name
    raw_original=original
    original=geometry(original)
    h=triangles(original)[0]
    assert S.unpack_from('<6H',ref,8)==(0,h[-1],0,h[3],0,h[2])
    part=child(root,'VMeshPart');root.children.remove(part)
    ml=Node('MultiLevel');lod0=Node('Level0');lod0.children=[part];ml.children=[lod0]
    root.children.append(ml)
    report=dict(file=relative,internal_name=mesh.name,source_sha256=sha(data),
                original=dict(vertices=h[-1],triangles=h[3]//3,groups=h[2]),levels=[],repairs=repairs)
    preview=preview_root/source.stem
    preview.parent.mkdir(parents=True,exist_ok=True)
    preview.with_name(preview.name+'_0.vms').write_bytes(original)
    for level,ratio,error in levels:
        blob,stats=simplify(original,dll,ratio,error,protect_flat_caps=False,
                            retain_missing_materials=True,**(simplify_options or {}));h=triangles(blob)[0]
        assert h[-1]<report['original']['vertices'], 'LOD did not reduce vertex count'
        assert h[3]//3<=report['original']['triangles']
        name=f'{source.stem}_auto.lod{level}-112.vms'
        assert all(crc(n.name)!=crc(name) for n in child(root,'VMeshLibrary').children)
        item=Node(name);item.children=[Node('VMeshData',blob)];child(root,'VMeshLibrary').children.append(item)
        new_ref=bytearray(ref);S.pack_into('<I6H',new_ref,4,crc(name),0,h[-1],0,h[3],0,h[2])
        new_part=Node('VMeshPart');new_part.children=[Node('VMeshRef',bytes(new_ref))]
        lod=Node(f'Level{level}');lod.children=[new_part];ml.children.append(lod)
        report['levels'].append(dict(level=level,vertices=h[-1],triangles=h[3]//3,
                                     groups=h[2],ratio_goal=ratio,error_limit=error,materials=stats))
        preview.with_name(preview.name+f'_{level}.vms').write_bytes(blob)
    # The old single-level renderer uses this same fallback end distance.
    ml.children.append(Node('Switch2',S.pack('<4f',0,1800,4500,1000000)))
    output=write_tree(header,roots)
    before={p:b for p,_,b in leaves(data)[1]};after={p:b for p,_,b in leaves(output)[1]}
    for p,b in before.items():
        if empty_ml and p.lower()=='/\\/multilevel/switch2':continue
        new=p.replace('/VMeshPart/','/MultiLevel/Level0/VMeshPart/',1) if p.startswith('/\\/VMeshPart/') else p
        if changed_mesh and p.lower().endswith('/'+changed_mesh.lower()+'/vmeshdata'):
            assert after[new]==raw_original,p
        else:assert after[new]==b,p
    # Check the exact serialized model, not just the in-memory generator tree.
    _,check=read_tree(output);r=check[0]
    library={crc(n.name):child(n,'VMeshData').blob for n in child(r,'VMeshLibrary').children}
    for i in range(3):
        rr=child(child(child(child(r,'MultiLevel'),f'Level{i}'),'VMeshPart'),'VMeshRef').blob
        hh=triangles(geometry(library[S.unpack_from('<I',rr,4)[0]]))[0]
        assert S.unpack_from('<6H',rr,8)==(0,hh[-1],0,hh[3],0,hh[2])
        assert rr[20:]==ref[20:], 'Bounds changed'
    destination=OUT/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(output)
    report['output_sha256']=sha(output)
    return report


def prepare_configs(targets,stage_root=Path('src/obj/industrial_config')):
    result=[];snippets=[]
    for file in (DATA/'SOLAR/solararch.ini',DATA/'EQUIPMENT/select_equip.ini'):
        before=file.read_bytes();changes=[]
        def update(m):
            block=m[0]
            archetype=re.search(rb'(?mi)^DA_archetype\s*=\s*([^;\r\n]+)',block)
            if not archetype:return block
            model=archetype[1].decode('ascii').strip().replace('\\','/').lower()
            if model not in targets:return block
            nick=re.search(rb'(?mi)^nickname\s*=\s*([^;\r\n]+)',block)[1].decode().strip()
            ranges=re.search(rb'(?mi)^LODranges\s*=\s*([^;\r\n]+)',block)
            assert ranges is not None,(file,nick)
            values=[float(x.strip()) for x in ranges[1].split(b',')]
            assert len(values)==2 and values[0]==0 and values[1]>0,(file,nick,values)
            far=values[-1];full=min(1800,far*.30);medium=min(4500,far*.65)
            new=[0,full,medium,far]
            text='LODranges = '+', '.join(f'{v:g}' for v in new)
            newblock,n=re.subn(rb'(?mi)^LODranges[^\r\n]*',text.encode(),block);assert n==1
            changes.append(dict(nickname=nick,model=model,before=values,after=new))
            snippets.append(b'; '+file.relative_to(DATA).as_posix().encode()+b'\r\n'+newblock)
            return newblock
        after=re.sub(rb'(?ms)^\[[^\r\n]+\]\r?\n(?:(?!^\[).)*',update,before)
        assert changes
        staged=stage_root/file.relative_to(DATA)
        staged.parent.mkdir(parents=True,exist_ok=True);staged.write_bytes(after)
        result.append(dict(file=file.relative_to(DATA).as_posix(),staged=staged.as_posix(),
                           source_sha256=sha(before),output_sha256=sha(after),changes=changes))
    (OUT/'archetype_changes.ini').write_bytes(b'\r\n'.join(snippets))
    return result


def main():
    audit=json.loads(Path('src/obj/industrial_inventory.json').read_text())
    selected=[r for r in audit if r['file'].startswith('SOLAR/') and len(r['refs'])==1
              and not any('data.solar.' in m['name'].lower() for m in r['meshes'])]
    dll=C.CDLL(str(Path('bin/lod_meshopt.dll').resolve()))
    dll.simplify_lod.argtypes=[C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.c_size_t,
        C.POINTER(C.c_float),C.c_size_t,C.POINTER(C.c_ubyte),C.c_size_t,C.c_float,C.POINTER(C.c_float)]
    dll.simplify_lod.restype=C.c_size_t
    OUT.mkdir(parents=True,exist_ok=True);models=[]
    for row in selected:
        levels=((1,.65,.05),(2,.40,.07)) if Path(row['file']).stem=='space_industrial01c' else ((1,.65,.025),(2,.40,.04))
        r=generate_one(row['file'],dll,levels);models.append(r)
        print(Path(r['file']).name,':',r['original']['vertices'],'->',
              '/'.join(str(l['vertices']) for l in r['levels']),'vertices;',
              r['original']['triangles'],'->','/'.join(str(l['triangles']) for l in r['levels']),'triangles',flush=True)
    configs=prepare_configs({r['file'].lower() for r in models})
    manifest=dict(models=models,configs=configs,skipped=[r['file'] for r in audit if r not in selected])
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Generated',len(models),'models; config references',sum(len(r['changes']) for r in configs))


if __name__=='__main__':main()
