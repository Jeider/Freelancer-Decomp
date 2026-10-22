"""Build a review bundle of high-benefit component LODs and local mesh repairs."""
import collections
import ctypes as C
import hashlib
import json
import math
import re
import struct as S
from pathlib import Path
import generate_industrial_lods as batch
from generate_station_lods import read_tree,write_tree,child,crc
from repair_panel_normals import leaves,triangles,face_normal

DATA=Path('D:/games/FL_MOD/DATA')
OUT=Path('bin/component_lods')
PREVIEW=Path('src/obj/component_previews')
NAMES=['space_control_tower','space_medium_control_tower','space_production',
       'space_large_production','shipyard_small','shipyard_medium','space_domea',
       'space_domeb','space_small_control_block','space_windows']


def geometry(blob):
    h=S.unpack_from('<II4H',blob);expected=16+12*h[2]+2*h[3]+32*h[-1]
    if expected<len(blob)<=expected+3 and not any(blob[expected:]):return blob[:expected]
    return blob


def fix_winding(blob):
    h,ds,gs=triangles(geometry(blob));out=bytearray(blob);offset=16+12*h[2];fixed=0
    for (_,size,_),cs in zip(ds,gs):
        for i in range(0,len(cs),3):
            face=cs[i:i+3];n=face_normal(face)
            normals=[S.unpack_from('<3f',v,12) for v in face]
            if n and all(sum(x*y for x,y in zip(n,v))<-.25 for v in normals):
                ys=[S.unpack_from('<3f',v)[1] for v in face]
                assert max(ys)-min(ys)<1.e-4 and all(abs(v[1])>.999 for v in normals)
                at=offset+i*2
                out[at+2:at+4],out[at+4:at+6]=out[at+4:at+6],out[at+2:at+4]
                fixed+=1
        offset+=size*2
    assert fixed==4, 'Unexpected medium-tower defect scope'
    assert out[offset:]==blob[offset:], 'Winding repair changed vertices'
    _,_,newgroups=triangles(geometry(out))
    for cs in newgroups:
        for i in range(0,len(cs),3):
            face=cs[i:i+3];n=face_normal(face)
            assert not(n and all(sum(x*y for x,y in zip(n,S.unpack_from('<3f',v,12)))<-.25 for v in face))
    return bytes(out),[dict(kind='horizontal_panel_winding',triangles=fixed)]


def fix_zero_normal(blob):
    h,ds,gs=triangles(geometry(blob));index=16+12*h[2];vertex_start=index+2*h[3]
    invalid=[i for i in range(h[-1]) if sum(x*x for x in S.unpack_from('<3f',blob,vertex_start+32*i+12))<1.e-12]
    assert len(invalid)==1;bad=invalid[0];summed=[0.,0.,0.];neighbors=[0.,0.,0.];faces=0
    for group_index,((_,size,_),cs) in enumerate(zip(ds,gs)):
        # Obtain the group start vertex from its descriptor rather than attributes.
        base=S.unpack_from('<H',blob,16+12*group_index+4)[0]
        ids=S.unpack_from('<'+'H'*size,blob,index)
        ids=[v+base if h[0]&1 else v for v in ids]
        for i in range(0,size,3):
            if bad not in ids[i:i+3]:continue
            face=cs[i:i+3];p,q,r=[S.unpack_from('<3f',v) for v in face]
            a=[q[k]-p[k] for k in range(3)];b=[r[k]-p[k] for k in range(3)]
            n=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
            for k in range(3):summed[k]+=n[k]
            for v in face:
                nn=S.unpack_from('<3f',v,12)
                for k in range(3):neighbors[k]+=nn[k]
            faces+=1
        index+=size*2
    length=math.sqrt(sum(x*x for x in summed));assert length>1.e-8 and faces==2
    normal=tuple(x/length for x in summed)
    assert sum(x*y for x,y in zip(normal,neighbors))>0
    out=bytearray(blob);start=vertex_start+32*bad+12
    S.pack_into('<3f',out,start,*normal)
    assert out[:start]==blob[:start] and out[start+12:]==blob[start+12:]
    return bytes(out),[dict(kind='zero_normal',vertices=1,incident_triangles=faces,normal=normal)]


def remove_duplicates(blob):
    h,ds,gs=triangles(geometry(blob));assert h[2]==1
    material,size,unused=ds[0];seen=set();kept=[];removed=0
    for i in range(0,len(gs[0]),3):
        face=gs[0][i:i+3];key=min(tuple(face),tuple(face[1:]+face[:1]),tuple(face[2:]+face[:2]))
        if key in seen:removed+=1
        else:seen.add(key);kept.extend(face)
    assert removed==755
    unique=list(dict.fromkeys(kept));mapping={v:i for i,v in enumerate(unique)}
    out=S.pack('<II4H',1,4,1,len(kept),0x112,len(unique))
    out+=S.pack('<I4H',material,0,len(unique)-1,len(kept),unused)
    out+=S.pack('<'+'H'*len(kept),*(mapping[v] for v in kept))+b''.join(unique)
    _,_,groups=triangles(out)
    verify=set()
    for i in range(0,len(groups[0]),3):
        face=groups[0][i:i+3];verify.add(min(tuple(face),tuple(face[1:]+face[:1]),tuple(face[2:]+face[:2])))
    assert verify==seen
    return out,[dict(kind='exact_same_winding_duplicates',removed_triangles=removed,
                     vertices_before=h[-1],vertices_after=len(unique))]


def repair_only(relative,transform):
    data=(DATA/relative).read_bytes();header,roots=read_tree(data);root=roots[0]
    ref,mesh,original=batch.library_main(root);fixed,notes=transform(original)
    child(mesh,'VMeshData').blob=fixed
    h=triangles(geometry(fixed))[0]
    new_ref=bytearray(ref);S.pack_into('<6H',new_ref,8,0,h[-1],0,h[3],0,h[2])
    assert new_ref[:8]==ref[:8] and new_ref[20:]==ref[20:]
    child(child(root,'VMeshPart'),'VMeshRef').blob=bytes(new_ref)
    output=write_tree(header,roots)
    before={p:b for p,_,b in leaves(data)[1]};after={p:b for p,_,b in leaves(output)[1]}
    for p,b in before.items():
        if p.lower().endswith('/'+mesh.name.lower()+'/vmeshdata'):assert after[p]==fixed
        elif p=='/\\/VMeshPart/VMeshRef':assert after[p]==bytes(new_ref)
        else:assert after[p]==b
    dest=OUT/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(output)
    prefix=PREVIEW/Path(relative).stem;prefix.parent.mkdir(parents=True,exist_ok=True)
    for level,blob in enumerate((geometry(original),geometry(fixed),geometry(fixed))):
        prefix.with_name(prefix.name+f'_{level}.vms').write_bytes(blob)
    return dict(file=relative,source_sha256=batch.sha(data),output_sha256=batch.sha(output),
                original=dict(vertices=S.unpack_from('<H',original,14)[0],triangles=S.unpack_from('<H',original,10)[0]//3),
                repaired=dict(vertices=h[-1],triangles=h[3]//3),repairs=notes)


def catalogs():
    references=collections.defaultdict(list)
    for file in (DATA/'SOLAR/solararch.ini',DATA/'EQUIPMENT/select_equip.ini'):
        for block in re.split(r'(?m)(?=^\[)',file.read_text(encoding='cp1251')):
            m=re.search(r'(?mi)^DA_archetype\s*=\s*([^;\r\n]+)',block)
            if m:references[Path(m[1].strip().replace('\\','/')).stem.lower()].append(block)
    result={}
    for name in NAMES:
        source=DATA/'SOLAR/MISC'/(name+'.3db');catalog={};files=[source]
        for block in references[name]:
            files.extend(DATA/p.strip().replace('\\','/') for p in re.findall(r'(?mi)^material_library\s*=\s*([^;\r\n]+)',block))
        for file in dict.fromkeys(files):
            for path,_,blob in leaves(file.read_bytes())[1]:
                parts=path.split('/')
                if parts[-1].lower()=='type' and len(parts)>3:
                    catalog[crc(parts[3])]=(parts[3],blob.rstrip(b'\0').decode())
        _,r=read_tree(source.read_bytes());h,ds,gs=triangles(geometry(batch.library_main(r[0])[2]))
        ids={d[0] for d in ds};assert ids<=catalog.keys()
        protected={m for m in ids if catalog[m][1] not in ('DcDt','DcDtEt','DcDtBt')}
        for m in protected:
            assert sum(d[0]==m for d in ds)==1, 'Transparent material occurs in multiple ordered groups'
        result[name]=dict(materials={hex(m):catalog[m] for m in ids},preserved=sorted(protected))
    return result


def main():
    batch.OUT=OUT;OUT.mkdir(parents=True,exist_ok=True);PREVIEW.mkdir(parents=True,exist_ok=True)
    materials=catalogs();dll=C.CDLL(str(Path('bin/lod_meshopt.dll').resolve()))
    dll.simplify_lod.argtypes=[C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.c_size_t,C.POINTER(C.c_float),C.c_size_t,C.POINTER(C.c_ubyte),C.c_size_t,C.c_float,C.POINTER(C.c_float)]
    dll.simplify_lod.restype=C.c_size_t
    models=[]
    for name in NAMES:
        transform=fix_winding if name=='space_medium_control_tower' else None
        if name=='space_small_control_block':
            # The tiny aerial is a separate material island; do not bend it.
            materials[name]['preserved'].append(0xe61a4408)
        levels=((1,.65,.02),(2,.40,.03)) if name in ('space_production','space_large_production') else ((1,.65,.025),(2,.40,.04))
        r=batch.generate_one('SOLAR/MISC/'+name+'.3db',dll,levels=levels,mesh_transform=transform,
                             simplify_options={'preserve_materials':materials[name]['preserved']},preview_root=PREVIEW)
        r['materials']=materials[name];models.append(r)
        print(name,r['original'],'->',[{k:l[k] for k in ('vertices','triangles','groups')} for l in r['levels']],flush=True)
    fixes=[repair_only('SOLAR/MISC/space_long_large_arch.3db',fix_zero_normal),
           repair_only('SOLAR/ASTEROIDS_MOD/DYSON/dyson_box_detail_fixed.3db',remove_duplicates)]
    configs=batch.prepare_configs({r['file'].lower() for r in models},Path('src/obj/component_config'))
    manifest=dict(models=models,fixes=fixes,configs=configs)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Prepared',len(models),'LOD models,',len(fixes),'standalone repairs,',sum(len(c['changes']) for c in configs),'config references')


if __name__=='__main__':main()
