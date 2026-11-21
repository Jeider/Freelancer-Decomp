"""Build a native salted DFM, mipmapped diffuse and character material sidecars."""
import sys,json,gzip,struct,uuid,io,copy,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'tools/hatcher_hair')]
import contours as c
from build import Node
from hands import skeleton
import importlib.util
sys.path.insert(0,str(ROOT/'tools/room_materials'))
spec=importlib.util.spec_from_file_location('hassler_surface_generator',ROOT/'tools/room_materials/generate.py');surface=importlib.util.module_from_spec(spec);spec.loader.exec_module(surface)
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'game';STAGE=OUT/'stage';REL='CHARACTERS/BODIES/rh_hassler_body.dfm'
sha=lambda b:hashlib.sha256(b).hexdigest()
def branch(n,children):
    result=Node(n);result.children=children;return result
def array(n,values,dtype):return Node(n,np.asarray(values,dtype=dtype).tobytes())
def bind_matrix(data):
    m=np.eye(4);m[:3,:3]=np.array(data[:9]).reshape(3,3);m[:3,3]=data[9:];return m

def dds(path):
    image=Image.open(path).convert('RGB');levels=[];header=None
    while True:
        stream=io.BytesIO();image.save(stream,format='DDS',pixel_format='DXT1');raw=stream.getvalue()
        if header is None:header=bytearray(raw[:128])
        levels.append(raw[128:])
        if image.size==(1,1):break
        image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.BOX)
    struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,28,len(levels));struct.pack_into('<I',header,108,0x401008)
    return bytes(header)+b''.join(levels)

def mesh_node(level,data,materials):
    records=data['records'];n=len(records);identity=np.arange(n,dtype='<u4');first=[];counts=[];ids=[];weights=[]
    for p,no,uv,skin in records:
        first.append(len(ids));counts.append(len(skin));ids.extend(b for b,w in skin);weights.extend(w for b,w in skin)
    assert max(counts)<=4 and len(records)<65536
    geometry=branch('Geometry',[array('Points',[r[0] for r in records],'<f4'),array('Vertex_normals',[r[1] for r in records],'<f4'),array('Point_indices',identity,'<u4'),array('UV0',[r[2] for r in records],'<f4'),array('UV0_indices',identity,'<u4'),array('UV1',[r[2] for r in records],'<f4'),array('UV1_indices',identity,'<u4'),array('Point_bone_first',first,'<u4'),array('Point_bone_count',counts,'<u4'),array('Bone_id_chain',ids,'<u4'),array('Bone_weight_chain',weights,'<f4')])
    groups=[branch(f'Group{j}',[Node('Material_name',(materials[int(mi)]['name']+'\0').encode()),array('Face_indices',faces,'<u2')]) for j,(mi,faces) in enumerate(sorted(data['groups'].items(),key=lambda q:int(q[0])))]
    return branch(f'Mesh{level}',[branch('Face_groups',[array('Count',[len(groups)],'<u4')]+groups),geometry])

def main():
    report=json.loads((OUT/'export.json').read_text(encoding='utf8'));source=TOP.parent/'source/rh_male_elite_body.dfm';raw=source.read_bytes();header,roots=c.read_tree(raw);root=roots[0];bones=skeleton(root);names=[b['name'] for b in bones];assert names==report['bone_names']
    lods=[]
    for lod in report['lods']:
        packed=Path(lod['path']).read_bytes();assert sha(packed)==lod['sha256'];data=json.loads(gzip.decompress(packed));lods.append(mesh_node(lod['level'],data,report['materials']))
    c.child(root,'MultiLevel').children=[array('Fractions',[1,1,.6,.3,.1],'<f4')]+lods+[array('Enhanced geometry',[1],'<u4')]
    materials=[];textures=[];texture_ids={};sidecars={};profiles=[];decoded=OUT/'decoded';decoded.mkdir(exist_ok=True)
    for m in report['materials']:
        path=Path(m['texture']);assert sha(path.read_bytes())==m['texture_sha256'];payload=dds(path);key=sha(payload)
        if key not in texture_ids:
            texture_ids[key]=m['name']+'.tga';textures.append(branch(texture_ids[key],[Node('MIPS',payload)]))
        texture=texture_ids[key];m['game_texture']=texture;m['dds_sha256']=key
        image=Image.open(io.BytesIO(payload)).convert('RGB');image.save(decoded/(texture+'.png'))
        original=np.asarray(Image.open(path).convert('RGB'),dtype=float);error=np.asarray(image,dtype=float)-original;assert np.sqrt(np.mean(error**2))<8
        materials.append(branch(m['name'],[Node('Type',b'DcDt\0'),Node('Dt_name',texture.encode()+b'\0'),array('Dt_flags',[64],'<u4')]))
        rough=max(.45,min(.9,m['roughness']));packed,_,_=surface.derive(payload,'cloth',rough)
        token=sha(packed)[:32]+'.dds';sidecars[token]=packed
        strength=.25 if m['size']>16 else 0.;specular=.22+.25*m['metallic']
        if 'native green cloth' in m['source_material'] or 'rear dart panel' in m['source_material']:
            rough=.9;specular=.10
        profiles.append(f'{strength:.4f} {rough:.4f} {specular:.4f} -0.2500 {token} {m["name"]}|{texture}')
    c.child(root,'Material library').children=[array('Material count',[len(materials)],'<u4')]+materials;c.child(root,'Texture library').children=textures
    # Keep the accepted lower head while using the shared head DFM unchanged.
    oldbind={b['name']:bind_matrix(b['native_bind']) for b in bones};newbind={n:bind_matrix(report['native_inverse_bind'][n]) for n in names}
    sphere=c.child(c.child(c.child(root,'Cmpnd'),'Cons'),'Sphere');joint=bytearray(sphere.blob);changes=[]
    for at in range(0,len(joint),212):
        parent=joint[at:at+64].split(b'\0')[0].decode();name=joint[at+64:at+128].split(b'\0')[0].decode()
        if name not in newbind or parent not in newbind:continue
        oldlocal=oldbind[parent]@np.linalg.inv(oldbind[name]);newlocal=newbind[parent]@np.linalg.inv(newbind[name]);delta=newlocal[:3,3]-oldlocal[:3,3]
        if np.linalg.norm(delta)>1e-7:
            original=np.array(struct.unpack_from('<3f',joint,at+128));assert np.linalg.norm(original-oldlocal[:3,3])<1e-5
            struct.pack_into('<3f',joint,at+128,*(original+delta));changes.append({'bone':name,'parent':parent,'translation_delta':delta.tolist()})
    sphere.blob=bytes(joint);assert [v['bone'] for v in changes]==(['Body_Head'] if abs(report['head_offset_m'])>1e-7 else [])
    if abs(report['head_offset_m'])<1e-7:
        assert all(np.array_equal(oldbind[n],newbind[n]) for n in names),'Native rig must be restored exactly'
    salt=uuid.uuid4().hex[:12];mapping={};parts=[n for n in root.children if n.name.lower().endswith('.3db')]
    for index,(part,bone) in enumerate(zip(parts,bones)):
        c.put(part,'Bone to root',np.array(report['native_inverse_bind'][bone['name']],dtype='<f4').tobytes());c.put(part,'Lod Bits',bytes([31]))
        old=part.name;part.name=f'hassler_{salt}_{index:02d}.3db';mapping[old]=part.name
    for part in c.child(root,'Cmpnd').children:
        for leaf in part.children:
            if leaf.name=='File name':leaf.blob=mapping[leaf.blob.rstrip(b'\0').decode()].encode()+b'\0'
    skeleton_name=c.child(c.child(root,'Skeleton'),'Name');oldname=skeleton_name.blob.rstrip(b'\0').decode();skeleton_name.blob=f'hassler_{salt}.cmp\0'.encode();mapping[oldname]=skeleton_name.blob.rstrip(b'\0').decode()
    payload=c.write_tree(header,roots);target=c.DataFolder(root=STAGE).sync_data_file(REL,payload)
    from hassler_runtime_pose import read_rig
    rb,rj,rm=read_rig(target)
    (OUT/'rig_for_preview.json').write_text(json.dumps({'bones':rb,'joints':rj,'bind':rm},default=lambda a:a.tolist()),encoding='utf8')
    # Decode the actual saved DFM for preview and validation, never the input mesh.
    checked=c.read_tree(target.read_bytes())[1][0];ml=c.child(checked,'MultiLevel');exported=[]
    for i,node in enumerate(n for n in ml.children if n.name.startswith('Mesh')):
        geo=c.child(node,'Geometry');p=c.arr(geo,'Points','<f4',3);n=c.arr(geo,'Vertex_normals','<f4',3);uv=c.arr(geo,'UV0','<f4',2);first=c.arr(geo,'Point_bone_first','<u4').ravel();counts=c.arr(geo,'Point_bone_count','<u4').ravel();ids=c.arr(geo,'Bone_id_chain','<u4').ravel();ws=c.arr(geo,'Bone_weight_chain','<f4').ravel()
        skin=[{int(b):float(w) for b,w in zip(ids[f:f+k],ws[f:f+k])} for f,k in zip(first,counts)]
        groups=[{'name':c.blob(g,'Material_name').rstrip(b'\0').decode(),'faces':c.triangles(g)} for g in c.child(node,'Face_groups').children if g.children]
        fs=np.array([f for g in groups for f in g['faces']]);assert fs.min()>=0 and fs.max()<len(p)<65536;assert np.isfinite(p).all() and np.isfinite(uv).all();assert np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-4
        assert max(counts)<=4 and all(abs(sum(s.values())-1)<1e-5 for s in skin)
        data={'points':p.tolist(),'normals':n.tolist(),'uv':uv.tolist(),'skin':skin,'groups':groups};(OUT/f'decoded_mesh{i}.json.gz').write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))
        exported.append({'vertices':len(p),'triangles':len(fs),'material_groups':len(groups)})
        assert len(fs)==report['lods'][i]['triangles']
    for m in report['materials']:
        rel='DATA_EXTRA/ROOM_MATERIALS/'+profiles[report['materials'].index(m)].split()[4];dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(sidecars[dest.name])
    result={'body':'rh_hassler_body','relative':REL,'dfm':str(target),'sha256':sha(payload),'bytes':len(payload),'source_blend':report['source'],'source_blend_sha256':report['source_sha256'],'skeleton_source':str(source),'skeleton_source_sha256':sha(raw),'private_resource_salt':salt,'resource_mapping':mapping,'joint_changes':changes,'lods':exported,'materials':report['materials'],'profiles':profiles,'sidecars':{n:sha(b) for n,b in sidecars.items()},'head_offset_m':report['head_offset_m'],'shared_head_hands_unchanged':True,'native_export_validated':True,'game_installed':False}
    (OUT/'native_build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:result[k] for k in ('body','bytes','lods','joint_changes')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
