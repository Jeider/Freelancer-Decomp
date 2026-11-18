"""Stage reviewed Bismarck relief as native CMP; preserve all authored materials."""
import copy
import io
from native_common import *

def pack_groups(groups):
    descriptors=bytearray();ib=bytearray();vb=bytearray();offset=0
    for g in groups:
        corners=np.asarray(g['corners'],dtype='<f4').reshape(-1,10)
        unique={};indices=[]
        for row in corners:
            key=row.tobytes()
            if key not in unique:unique[key]=len(unique)
            indices.append(unique[key])
        descriptors.extend(S.pack('<I4H',g['material'],offset,offset+len(unique)-1,len(indices),g['unused']))
        ib.extend(np.asarray(indices,dtype='<u2').tobytes());vb.extend(b''.join(unique));offset+=len(unique)
    assert offset<=65535 and len(ib)//2<=65535
    blob=S.pack('<II4H',1,4,len(groups),len(ib)//2,0x212,offset)+descriptors+ib+vb
    check=decode(blob)
    for a,b in zip(groups,check):assert np.array_equal(np.asarray(a['corners'],dtype='<f4'),b['corners'])
    return bytes(blob)

def reference(name,blob,points,original_bounds=None):
    _,_,ng,ni,_,nv=S.unpack_from('<II4H',blob)
    p=np.concatenate(points).reshape(-1,10)[:,:3]
    lo=p.min(0);hi=p.max(0)
    if original_bounds is not None:
        old=S.unpack_from('<6f',original_bounds,20)
        hi=np.maximum(hi,old[::2]);lo=np.minimum(lo,old[1::2])
    center=(lo+hi)*.5
    radius=float(np.max(np.linalg.norm(p-center,axis=1)))+.005
    return S.pack('<II6H10f',60,crc(name),0,nv,0,ni,0,ng,hi[0],lo[0],hi[1],lo[1],hi[2],lo[2],*center,radius)

def prepare():
    OUT.mkdir(exist_ok=True)
    source=(GAME/'DATA'/REL).read_bytes()
    assert sha(source)==json.loads((PROTO/'source.json').read_text())['sha256'],'Game source changed since preview'
    header,roots=read_tree(source);root=roots[0]
    before=dict(leaves(root));parts=get_parts(root);main=next(p for p in parts if p['name']=='Root')
    geometry=np.load(OUT/'native_geometry.npz')
    changed={int(k) for k in geometry.files}
    assert changed==set(json.loads((PROTO/'prototype_stats.json').read_text())['changed_batches'])
    groups=copy.deepcopy(main['groups']);validation={}
    for i in changed:
        corners=geometry[str(i)].astype('<f4')
        assert corners.shape[2]==10 and np.isfinite(corners).all()
        n=corners[:,:,3:6];length=np.linalg.norm(n,axis=2)
        assert np.max(abs(length-1))<.001
        cross=np.cross(corners[:,1,:3]-corners[:,0,:3],corners[:,2,:3]-corners[:,0,:3])
        area=np.linalg.norm(cross,axis=1)
        # Clipping can produce collapsed slivers after float32 conversion.
        # Remove only zero-area triangles, never the original native batches.
        good=area>1e-10
        facing=np.einsum('ij,ij->i',cross,n.mean(1))
        assert np.all(facing[good]>-1e-7),(i,float(facing.min()))
        groups[i]['corners']=corners[good]
        validation[str(i)]=dict(triangles=int(good.sum()),collapsed_triangles_removed=int((~good).sum()),
                                max_normal_length_error=float(abs(length-1).max()))
    # Native headers/index counts are uint16. Split on material boundaries,
    # adding one static identity child; all existing animated parts remain exact.
    chunks=[];current=[];nindices=0
    for g in groups:
        count=len(g['corners'])*3
        if nindices+count>60000:chunks.append(current);current=[];nindices=0
        current.append(g);nindices+=count
    if current:chunks.append(current)
    compound=child(root,'Cmpnd');fix=child(child(compound,'Cons'),'Fix')
    library=child(root,'VMeshLibrary');chunk_report=[]
    next_index=max(S.unpack('<I',child(p['record'],'Index').blob)[0] for p in parts)+1
    for i,chunk in enumerate(chunks):
        name=f'rh_bizmark_bar_relief_v8_{i}.lod0-212.vms';blob=pack_groups(chunk)
        assert all(crc(x.name)!=crc(name) for x in library.children)
        library.children.append(node(name,[Node('VMeshData',blob)]))
        ref=reference(name,blob,[g['corners'] for g in (groups if i==0 else chunk)],main['ref'].blob if i==0 else None)
        if i==0:main['ref'].blob=ref
        else:
            partname=f'BizRelief{i:02d}';filename=f'rh_bizmark_bar_relief_v8_{i}.3db'
            compound.children.append(node('Part_'+partname,[Node('Object name',partname.encode()+b'\0'),Node('File name',filename.encode()+b'\0'),Node('Index',S.pack('<I',next_index))]));next_index+=1
            root.children.append(node(filename,[node('VMeshPart',[Node('VMeshRef',ref)])]))
            fix.blob+=S.pack('<64s64s12f',b'Root',partname.encode(),0,0,0,1,0,0,0,1,0,0,0,1)
        h=S.unpack_from('<II4H',blob)
        chunk_report.append(dict(mesh=name,groups=h[2],indices=h[3],vertices=h[5],triangles=h[3]//3))
    output=write_tree(header,roots)
    staged_root=read_tree(output)[1][0];after=dict(leaves(staged_root))
    modified=[p for p,b in before.items() if after.get(p)!=b]
    assert len(modified)==2 and any(p.endswith('/Cons/Fix') for p in modified) and any(main['filename']+'/VMeshPart/VMeshRef' in p for p in modified),modified
    oldfix=next(b for p,b in before.items() if p.endswith('/Cons/Fix'))
    assert fix.blob.startswith(oldfix)
    newparts=get_parts(staged_root)
    for p in parts[1:]:
        q=next(q for q in newparts if q['name']==p['name'])
        assert q['ref'].blob==p['ref'].blob
        for a,b in zip(p['groups'],q['groups']):assert np.array_equal(a['corners'],b['corners'])
    actual=[]
    for name in ['Root']+[f'BizRelief{i:02d}' for i in range(1,len(chunks))]:actual.extend(next(p for p in newparts if p['name']==name)['groups'])
    assert len(actual)==len(groups)
    for a,b in zip(groups,actual):assert a['material']==b['material'] and np.array_equal(a['corners'],b['corners'])
    untouched=[i for i in range(len(groups)) if i not in changed]
    for i in untouched:assert np.array_equal(actual[i]['corners'],main['groups'][i]['corners'])
    DataFolder(root=STAGE).sync_data_file(REL,output)
    report=dict(source_sha256=sha(source),prepared_sha256=sha(output),changed_original_leaves=modified,
                source_triangles=sum(len(g['corners']) for p in parts for g in p['groups']),
                result_triangles=sum(len(g['corners']) for p in newparts for g in p['groups']),
                chunks=chunk_report,changed_batches=validation,unchanged_root_batches=untouched,
                original_material_library_byte_identical=True,original_texture_library_byte_identical=True,
                original_non_root_parts_byte_identical=True,original_joint_records_byte_identical=True,
                native_wireframe_preserved=True,both_uv_sets_retained=True,installed=False)
    dump(OUT/'native_validation.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':prepare()
