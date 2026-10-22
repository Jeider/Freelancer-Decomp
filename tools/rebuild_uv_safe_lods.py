"""Repair all previously generated LODs in place in a separate review bundle.

Reuses the currently installed Level0, keeping local repairs, materials,
hardpoints, visibility distances and all unmodified archive leaves intact.
"""
import ctypes as C
import hashlib
import json
import struct as S
from pathlib import Path
from generate_station_lods import read_tree,write_tree,child,crc,simplify
from generate_industrial_lods import geometry
from repair_panel_normals import leaves,triangles
from lod_uv_guard import UvGuard

DATA=Path('D:/games/FL_MOD/DATA')
OUT=Path('bin/uv_safe_lods')
PREVIEW=Path('src/obj/uv_safe_previews')


def sha(b):return hashlib.sha256(b).hexdigest()


def source_mesh(root,level=None):
    scope=child(child(root,'MultiLevel'),f'Level{level}') if level is not None else root
    node=child(child(scope,'VMeshPart'),'VMeshRef');ref=node.blob;key=S.unpack_from('<I',ref,4)[0]
    mesh=next(n for n in child(root,'VMeshLibrary').children if crc(n.name)==key)
    return node,child(mesh,'VMeshData')


def uv_signature(blob):
    _,ds,gs=triangles(geometry(blob));result=set()
    for (m,_,_),cs in zip(ds,gs):
        for i in range(0,len(cs),3):
            # Local normal/winding repairs and exact duplicate removal must not
            # be mistaken for UV edits. Compare rendered position + UV corners.
            face=tuple(sorted(v[:12]+v[24:32] for v in cs[i:i+3]))
            result.add((m,face))
    return result


def audit_original_uv():
    originals=[]
    for folder in ('industrial_lods','component_lods'):
        bundle=Path('bin')/folder;m=json.loads((bundle/'manifest.json').read_text())
        receipt=json.loads((bundle/'installation.json').read_text(encoding='utf-8-sig'))
        for r in m['models']+m.get('fixes',[]):originals.append((r['file'],Path(receipt['Backup'])/r['file']))
    misc=DATA/'SOLAR/MISC'
    originals.append(('SOLAR/MISC/space_trade_station_part.3db',misc/'.before_trade_station_lods_20261022_110538/space_trade_station_part.3db'))
    for name in ('space_panel_rotated.3db','space_panel45.3db','space_panel_Z90.3db'):
        originals.append(('SOLAR/MISC/'+name,misc/'.before_panel_normals_20261022_002831'/name))
    originals.append(('SOLAR/MISC/space_panel.3db',misc/'.before_or_hq_panel_normals_20261022_103115/space_panel.3db'))
    rows=[]
    for file,backup in originals:
        old=backup.read_bytes();current=(DATA/file).read_bytes()
        _,rs=read_tree(old);oldroot=rs[0]
        _,rs=read_tree(current);nowroot=rs[0]
        oldlevel=0 if any(n.name.lower()=='multilevel' and any(c.name.lower()=='level0' for c in n.children) for n in oldroot.children) else None
        nowlevel=0 if any(n.name.lower()=='multilevel' and any(c.name.lower()=='level0' for c in n.children) for n in nowroot.children) else None
        before=source_mesh(oldroot,oldlevel)[1].blob;after=source_mesh(nowroot,nowlevel)[1].blob
        assert uv_signature(before)==uv_signature(after), 'Near UV/geometry changed: '+file
        rows.append(dict(file=file,original=str(backup),near_uv_verified=True))
    assert len(rows)==36 and len({r['file'] for r in rows})==36
    return rows


def main():
    OUT.mkdir(parents=True,exist_ok=True);PREVIEW.mkdir(parents=True,exist_ok=True)
    uv_audit=audit_original_uv()
    specifications=[]
    for folder in ('industrial_lods','component_lods'):
        m=json.loads((Path('bin')/folder/'manifest.json').read_text())
        specifications.extend((r,folder) for r in m['models'])
    trade=json.loads(Path('bin/generated_station_lods/space_trade_station_part.report.json').read_text())
    trade['file']='SOLAR/MISC/space_trade_station_part.3db'
    specifications.append((trade,'generated_station_lods'))
    dll=C.CDLL(str(Path('bin/lod_meshopt.dll').resolve()))
    dll.simplify_lod.argtypes=[C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.c_size_t,C.POINTER(C.c_float),C.c_size_t,C.POINTER(C.c_ubyte),C.c_size_t,C.c_float,C.POINTER(C.c_float)]
    dll.simplify_lod.restype=C.c_size_t
    models=[]
    for specification,folder in specifications:
        relative=specification['file'];data=(DATA/relative).read_bytes();header,roots=read_tree(data);root=roots[0]
        _,near=source_mesh(root,0);original=geometry(near.blob);h,ds,gs=triangles(original);guard=UvGuard(ds,gs)
        changed={};row=dict(file=relative,previous_bundle=folder,source_sha256=sha(data),levels=[])
        prefix=PREVIEW/Path(relative).stem
        prefix.with_name(prefix.name+'_0.vms').write_bytes(original)
        for spec in specification['levels']:
            level=spec['level'];ref_node,mesh_node=source_mesh(root,level)
            old_h,old_ds,old_gs=triangles(geometry(mesh_node.blob))
            before_issues={hex(m):dict(guard.issues(m,cs)) for (m,_,_),cs in zip(old_ds,old_gs) if guard.issues(m,cs)}
            blob,stats=simplify(original,dll,spec.get('ratio_goal',spec.get('requested_ratio',.5)),
                                spec.get('error_limit',spec.get('metric_limit',.025)),
                                protect_flat_caps=(folder=='generated_station_lods'),retain_missing_materials=True,
                                preserve_materials=specification.get('materials',{}).get('preserved',()))
            new_h,new_ds,new_gs=triangles(blob)
            assert all(not guard.issues(m,cs) for (m,_,_),cs in zip(new_ds,new_gs))
            mesh_node.blob=blob;new_ref=bytearray(ref_node.blob)
            S.pack_into('<6H',new_ref,8,0,new_h[-1],0,new_h[3],0,new_h[2]);ref_node.blob=bytes(new_ref)
            changed[id(mesh_node)]=True;changed[id(ref_node)]=True
            prefix.with_name(prefix.name+f'_{level}.vms').write_bytes(blob)
            row['levels'].append(dict(level=level,previous_vertices=old_h[-1],vertices=new_h[-1],triangles=new_h[3]//3,
                                      previous_uv_issues=before_issues,materials=stats))
        output=write_tree(header,roots)
        old={p:b for p,_,b in leaves(data)[1]};new={p:b for p,_,b in leaves(output)[1]}
        for path,b in old.items():
            # Only Level1/2 references and their referenced mesh payloads change.
            if '/multilevel/level1/' in path.lower() or '/multilevel/level2/' in path.lower():continue
            if path.lower().endswith('/vmeshdata') and '_auto.lod' in path.lower():continue
            assert new[path]==b,(relative,path)
        # Validate the serialized references, including the near and hidden LOD.
        _,rs=read_tree(output);r=rs[0]
        for n in child(r,'MultiLevel').children:
            if n.name.lower().startswith('level'):
                ref,mesh=source_mesh(r,int(n.name[5:]));hh=triangles(geometry(mesh.blob))[0]
                assert S.unpack_from('<6H',ref.blob,8)==(0,hh[-1],0,hh[3],0,hh[2])
        dest=OUT/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(output)
        row['output_sha256']=sha(output);models.append(row)
        print(Path(relative).name,[(l['previous_vertices'],l['vertices'],sum(sum(v.values()) for v in l['previous_uv_issues'].values())) for l in row['levels']],flush=True)
    assert len(models)==30
    manifest=dict(models=models,original_uv_audit=uv_audit,configs_changed=False)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Rebuilt 60 visible LODs; all 36 changed near meshes match their original UV layouts')


if __name__=='__main__':main()
