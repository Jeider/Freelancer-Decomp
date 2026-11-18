"""Replace selected native mesh batches without reauthoring material libraries."""
import copy
from native_common import *

def pack(groups):
    stride=groups[0]['corners'].shape[-1];descriptors=bytearray();ib=bytearray();vb=bytearray();offset=0
    for g in groups:
        assert g['corners'].shape[-1]==stride
        unique={};indices=[]
        for row in g['corners'].astype('<f4').reshape(-1,stride):
            key=row.tobytes()
            if key not in unique:unique[key]=len(unique)
            indices.append(unique[key])
        descriptors.extend(S.pack('<I4H',g['material'],offset,offset+len(unique)-1,len(indices),g['unused']))
        ib.extend(np.asarray(indices,dtype='<u2').tobytes());vb.extend(b''.join(unique));offset+=len(unique)
    assert offset<=65535 and len(ib)//2<=65535
    return bytes(S.pack('<II4H',1,4,len(groups),len(ib)//2,{6:0x12,8:0x112,10:0x212,12:0x312,14:0x412}[stride],offset)+descriptors+ib+vb)
def ref(name,blob,groups,old):
    _,_,ng,ni,_,nv=S.unpack_from('<II4H',blob)
    p=np.concatenate([g['corners'].reshape(-1,g['corners'].shape[-1])[:,:3] for g in groups])
    hi=p.max(0);lo=p.min(0)
    if old:
        bounds=S.unpack_from('<6f',old,20);hi=np.maximum(hi,bounds[::2]);lo=np.minimum(lo,bounds[1::2])
    center=(hi+lo)*.5;radius=float(np.linalg.norm(p-center,axis=1).max())+.001
    return S.pack('<II6H10f',60,crc(name),0,nv,0,ni,0,ng,hi[0],lo[0],hi[1],lo[1],hi[2],lo[2],*center,radius)

def patch(raw,changes,model):
    header,roots=read_tree(raw);root=roots[0];before=dict(leaves(root));parts=get_parts(root)
    library=child(root,'VMeshLibrary');compound=child(root,'Cmpnd');cons=child(compound,'Cons')
    try:fix=child(cons,'Fix')
    except StopIteration:fix=Node('Fix',b'');cons.children.append(fix)
    next_index=max(S.unpack('<I',child(p['record'],'Index').blob)[0] for p in parts)+1
    allowed=set();records=[];expected={};new_names=set()
    for pi,p in enumerate(parts):
        groups=copy.deepcopy(p['groups'])
        if not any((p['name'],gi) in changes for gi in range(len(groups))):continue
        for gi,g in enumerate(groups):
            if (p['name'],gi) in changes:g['corners']=changes[p['name'],gi]
        chunks=[];chunk=[];count=0
        for g in groups:
            assert len(g['corners'])*3<60000,'Large single material needs explicit splitting'
            if count+len(g['corners'])*3>60000:chunks.append(chunk);chunk=[];count=0
            chunk.append(g);count+=len(g['corners'])*3
        if chunk:chunks.append(chunk)
        allowed.update(path for path,b in before.items() if path.endswith('/'+p['filename']+'/VMeshPart/VMeshRef') or path.endswith('/'+p['filename']+'/MultiLevel/Level0/VMeshPart/VMeshRef'))
        for ci,chunk in enumerate(chunks):
            name=f'{model}.relief1.p{pi}c{ci}.vms';blob=pack(chunk)
            assert all(crc(n.name)!=crc(name) for n in library.children)
            library.children.append(node(name,[Node('VMeshData',blob)]))
            newref=ref(name,blob,groups if ci==0 else chunk,p['ref'].blob if ci==0 else None)
            if ci==0:p['ref'].blob=newref;partname=p['name']
            else:
                partname=f'RHRelief{pi}_{ci}';filename=partname+'.3db';new_names.add(partname)
                compound.children.append(node('Part_'+partname,[Node('Object name',partname.encode()+b'\0'),Node('File name',filename.encode()+b'\0'),Node('Index',S.pack('<I',next_index))]));next_index+=1
                root.children.append(node(filename,[node('VMeshPart',[Node('VMeshRef',newref)])]))
                fix.blob+=S.pack('<64s64s12f',p['name'].encode(),partname.encode(),0,0,0,1,0,0,0,1,0,0,0,1)
                allowed.update(path for path in before if path.endswith('/Cons/Fix'))
            expected[partname]=chunk
            h=S.unpack_from('<II4H',blob);records.append(dict(part=partname,parent=p['name'],vertices=h[5],indices=h[3],groups=h[2]))
    result=write_tree(header,roots);after_root=read_tree(result)[1][0];after=dict(leaves(after_root))
    modified=[p for p,b in before.items() if after.get(p)!=b]
    assert set(modified)<=allowed,modified
    for path,b in before.items():
        if path.endswith('/Cons/Fix'):assert after[path].startswith(b)
    output_parts=get_parts(after_root)
    for p in output_parts:
        original=expected.get(p['name'])
        if original is None:original=next(q for q in parts if q['name']==p['name'])['groups']
        assert len(original)==len(p['groups'])
        for g,h in zip(original,p['groups']):assert g['material']==h['material'] and np.array_equal(g['corners'],h['corners'])
    return result,dict(source_sha256=sha(raw),prepared_sha256=sha(result),changed_original_leaves=modified,
        original_materials_textures_animations_joint_records_unchanged=True,both_uv_sets_preserved=True,
        source_triangles=sum(len(g['corners']) for p in parts for g in p['groups']),
        result_triangles=sum(len(g['corners']) for p in output_parts for g in p['groups']),mesh_blocks=records,new_static_parts=sorted(new_names))
