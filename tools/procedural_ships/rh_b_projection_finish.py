"""Assemble only distant geometry; preserve near mesh, HPs, rig and wire bytes."""
import copy
import json
import hashlib
import struct
import numpy as np
import rh_b_projection_prepare as p

f,v,OUT=p.f,p.v,p.OUT


def flat(nodes):return {path.lower():n.blob for path,n in f.mesh.walk(nodes) if n.blob is not None}


def main():
    source=OUT/'before.cmp'
    header,nodes=f.mesh.read_tree(source.read_bytes());before=copy.deepcopy(nodes)
    names=f.component_map(nodes);atlas=json.loads((OUT/'atlas.json').read_text())
    levels=json.loads((OUT/'projected_geometry.json').read_text())
    lib=f.mesh.child(nodes[0],'VMeshLibrary')
    # Keep Level0 and the static wire's VMeshData byte-for-byte, not a repack.
    retained=set()
    for path,node in f.mesh.walk(nodes):
        if path.lower().endswith('/vwiredata') or '/level0/' in path.lower() and path.lower().endswith('/vmeshref'):
            retained.add(struct.unpack_from('<I',node.blob,4)[0])
    lib.children=[n for n in lib.children if f.mesh.crc(n.name) in retained]
    for level,parts in enumerate(levels,1):
        for file,gs in parts.items():
            groups=[]
            for g in gs:
                t=np.array(g['corners'],dtype='<f4').astype(float)
                valid=np.linalg.norm(np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]),axis=1)>1e-8
                if valid.any():groups.append(dict(g,material=g['material'] or atlas['material_crc'],corners=t[valid]))
            blob,verts=f.mesh.pack(f.merge(groups))
            name='rh_b_photo_'+hashlib.sha256((file+str(level)).encode()+blob).hexdigest()[:20]+'.vms'
            lib.children.append(f.folder(name,f.mesh.Node('VMeshData',blob)))
            ml=f.mesh.child(f.mesh.child(nodes[0],file),'MultiLevel')
            ref=f.mesh.child(f.mesh.child(f.mesh.child(ml,'Level'+str(level)),'VMeshPart'),'VMeshRef')
            ref.blob=f.fresh_ref(name,blob,verts)
    dest=OUT/'rh_concept_b.cmp';dest.write_bytes(f.mesh.write_tree(header,nodes))
    nodes=f.mesh.read_tree(dest.read_bytes())[1];old=flat(before);now=flat(nodes)
    protected={k:b for k,b in old.items() if '/vmeshlibrary/' not in k and not any('/level'+str(i)+'/' in k for i in (1,2))}
    assert all(now[k]==b for k,b in protected.items()),'Protected leaf changed'
    for key in retained:
        get=lambda ns:next(n for n in f.mesh.child(ns[0],'VMeshLibrary').children if f.mesh.crc(n.name)==key)
        assert get(before).children[0].blob==get(nodes).children[0].blob
    assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(nodes))
    materials=f.audit.material_table([f.SHARED_MAT,OUT/'rh_concept_b_lods.mat'])
    max_v=max_i=0
    for path,node in f.mesh.walk(nodes):
        if not path.lower().endswith('/vmeshdata'):continue
        verts,groups,indices=f.audit.decode(node.blob);at=0
        max_v=max(max_v,len(verts));max_i=max(max_i,len(indices))
        assert len(verts)<=65535 and len(indices)<=65535 and np.isfinite(verts).all()
        for mat,lo,hi,count,_ in groups:
            ids=indices[at:at+count]+lo;at+=count
            assert mat in materials and (not materials[mat]['texture'] or materials[mat]['image'] is not None),hex(mat)
            assert count%3==0 and ids.min()>=lo and ids.max()<=hi<len(verts)
        assert at==len(indices)
    decoded=[f.local_geometry(nodes,i) for i in range(3)]
    for level in decoded:
        for groups in level.values():
            for g in groups:
                t=g['corners'];assert np.isfinite(t).all()
                assert np.allclose(np.linalg.norm(t[...,3:6],axis=-1),1,atol=1e-4)
                if g['material']==atlas['material_crc']:assert t[...,6:].min()>=0 and t[...,6:].max()<=1
    assert v.hp.hardpoint_records(before)==v.hp.hardpoint_records(nodes)
    companion=v.OUT/'rh_concept_b.sur';(OUT/companion.name).write_bytes(companion.read_bytes())
    config=(v.OUT/'shiparch_fragment.ini').read_text(encoding='utf8')
    config=config.replace('material_library = ships\\rheinland\\rh_pir_playerships.mat',
                          'material_library = ships\\rheinland\\rh_pir_playerships.mat\nmaterial_library = ships\\rheinland\\rh_concept_b\\rh_concept_b_lods.mat',1)
    assert 'rh_concept_b_lods.mat' in config
    (OUT/'shiparch_fragment.ini').write_text(config,encoding='utf8')
    data=json.loads((v.OUT/'blender_data.json').read_text());data['cmp_sha256']=f.digest(dest)
    data['levels']=[{names[file]:gs for file,gs in level.items()} for level in decoded]
    p.dump('blender_data.json',data)
    meta=json.loads((v.OUT/'input_manifest.json').read_text())
    for k in ('source','shared_mat','game_cmp'):assert f.digest(v.Path(meta[k]))==meta[k+'_sha256']
    assert f.digest(source)==f.digest(v.DEST)
    report=dict(cmp_sha256=f.digest(dest),source_sha256=f.digest(source),
        lod_triangles=[sum(len(g['corners']) for gs in level.values() for g in gs) for level in decoded],
        near_mesh_bytes_unchanged=True,rig_and_animations_bytes_unchanged=True,
        hardpoint_bytes_unchanged=True,hardpoints=len(v.hp.hardpoint_records(nodes)),
        wire_bytes_unchanged=True,sur_sha256=f.digest(companion),materials_external=True,
        max_vmesh_vertices=max_v,max_vmesh_indices=max_i,game_and_shared_mat_unchanged=True)
    p.dump('validation.json',report);print(json.dumps(report,indent=2))


if __name__=='__main__':main()
