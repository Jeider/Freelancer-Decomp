"""Validate packed DFM, preserved facial data, and every LOD before installation."""
import json, hashlib
import numpy as np
from io import BytesIO
from PIL import Image
from build import OUT, REL, DataFolder, read_tree, child, arr, blob, triangles, strand_normal

def leaves(node,prefix=''):
    result={}
    path=prefix+'/'+node.name
    if node.children:
        for n in node.children:result.update(leaves(n,path))
    else:result[path]=node.blob
    return result

def check():
    mirror=np.array([-1.,1.,1.])
    for x in np.linspace(.002,.08,10):
        for y in (.06,.11,.15):
            p=np.array([x,y,.025]);n=np.array([.6,.6,.529150262]);n/=np.linalg.norm(n)
            left=strand_normal(p,n,1.,0);right=strand_normal(p*mirror,n*mirror,1.,0)
            assert np.allclose(left*mirror,right),'Unequal strand relief between sides'
            assert abs(np.linalg.norm(left)-1)<1e-6 and np.dot(left,n)>.86
            assert np.allclose(strand_normal(p,n,0.,0),n)
            assert np.allclose(strand_normal(p,n,1.,3),n)
    source=(OUT/'original.dfm').read_bytes()
    packed=DataFolder(root=OUT/'stage').data_path(REL).read_bytes()
    before=read_tree(source)[1][0];after=read_tree(packed)[1][0]
    texture=child(child(after,'Texture library'),'hatcher_hair_v1.tga')
    mip_nodes=[n for n in texture.children if n.name.startswith('MIP')]
    assert 1<=len(mip_nodes)<=10
    assert [n.name for n in mip_nodes]==['MIP'+str(i) for i in range(len(mip_nodes))]
    for i,node in enumerate(mip_nodes):
        assert len(node.name)==4,'Native TGA loader rejects multi-digit mip indices'
        image=Image.open(BytesIO(node.blob))
        assert image.size==(max(1,1024>>i),)*2
        assert node.blob[2]==2 and node.blob[16] in (24,32)
    oldleaves=leaves(before);newleaves=leaves(after)
    for path,value in oldleaves.items():
        if '/MultiLevel/' not in path and not path.endswith('/Material count'):
            assert newleaves[path]==value,path
    report=[]
    for old in child(before,'MultiLevel').children:
        if not old.name.startswith('Mesh'):continue
        new=child(child(after,'MultiLevel'),old.name);a=child(old,'Geometry');b=child(new,'Geometry')
        p=arr(b,'Points','<f4',3);n=arr(b,'Vertex_normals','<f4',3);pi=arr(b,'Point_indices','<u4').ravel()
        assert len(p)==len(n) and np.isfinite(p).all() and np.isfinite(n).all()
        assert pi.max()<len(p) and len(pi)<65536
        for uv in ('UV0','UV1'):
            values=arr(b,uv,'<f4',2);indices=arr(b,uv+'_indices','<u4').ravel()
            assert len(indices)==len(pi) and indices.max()<len(values) and np.isfinite(values).all()
        for name in ('Point_indices','UV0','UV0_indices','UV1','UV1_indices','Point_bone_count','Bone_id_chain','Bone_weight_chain'):
            assert blob(b,name).startswith(blob(a,name)),name
        changed={'Points','Vertex_normals','Point_indices','UV0','UV0_indices','UV1','UV1_indices','Point_bone_count','Point_bone_first','Bone_id_chain','Bone_weight_chain'}
        for node in a.children:
            if node.name not in changed:assert blob(b,node.name)==node.blob,node.name
        count=arr(b,'Point_bone_count','<u4').ravel();weights=arr(b,'Bone_weight_chain','<f4').ravel()
        assert len(count)==len(p) and count.sum()==len(weights) and np.isfinite(weights).all()
        assert (count>0).all() and (weights>=0).all()
        cursor=0
        for size in count:
            assert abs(float(weights[cursor:cursor+size].sum())-1)<.001
            cursor+=int(size)
        groups=[g for g in child(new,'Face_groups').children if g.children]
        assert int(arr(child(new,'Face_groups'),'Count','<u4')[0,0])==len(groups)
        facepoints=set();total=0
        for group in groups:
            tri=np.asarray(triangles(group));assert tri.max()<len(pi);total+=len(tri)
            if blob(group,'Material_name').rstrip(b'\0')!=b'hatcher_hair_v1':
                original_group=child(child(old,'Face_groups'),group.name)
                original_tri={tuple(t) for t in triangles(original_group)}
                assert all(tuple(t) in original_tri for t in tri)
                facepoints.update(pi[tri].ravel().tolist())
        originalp=arr(a,'Points','<f4',3);originaln=arr(a,'Vertex_normals','<f4',3)
        ix=list(facepoints)
        assert np.array_equal(p[ix],originalp[ix]) and np.array_equal(n[ix],originaln[ix])
        if old.name in ('Mesh0','Mesh1','Mesh2'):
            motion=arr(b,'Hair_motion_weights','<f4').ravel()
            assert len(motion)==len(p) and np.isfinite(motion).all()
            assert (motion>=0).all() and (motion<=1).all() and (motion[ix]==0).all()
            bone=int(arr(b,'Hair_motion_bone','<u4')[0,0])
            assert bone in arr(b,'Bone_id_chain','<u4')
        report.append(dict(lod=old.name,triangles=total,points=len(p),groups=len(groups)))
    result=dict(ok=True,sha256=hashlib.sha256(packed).hexdigest(),lods=report)
    (OUT/'validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result));return result

if __name__=='__main__':check()
