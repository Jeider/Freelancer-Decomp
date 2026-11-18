"""Stage reviewed Mesh0 edits while retaining the installed lower LODs and rig."""
import gzip,json,uuid
from pathlib import Path
import numpy as np
import epaulettes as e


def posed(records):
    result=[]
    for r in records:
        q=np.zeros(3)
        for bone,w in r['skin'].items():
            angle=((bone%7)-3)*.12;cs,sn=np.cos(angle),np.sin(angle)
            rot=np.array([[cs,-sn,0],[sn,cs,0],[0,0,1]])
            q+=w*(rot@r['p']+np.array([0,(bone%3)*.007,0]))
        result.append(q)
    return np.array(result)


def seam_error(records):
    clusters={};error=0.;pose=posed(records)
    for i,r in enumerate(records):
        key=e.c.key(r['p'])
        if key in clusters:error=max(error,float(np.linalg.norm(pose[i]-pose[clusters[key]])))
        else:clusters[key]=i
    return error


def main():
    for name in e.TARGETS:
        folder=e.OUT/name;pins=json.loads((folder/'source.json').read_text());report=json.loads((folder/'report.json').read_text())
        raw=Path(pins['source']).read_bytes();assert e.c.digest(raw)==pins['source_sha256']
        h,roots=e.c.read_tree(raw);root=roots[0];before,oldgroups,oldfaces=e.c.as_records(root)
        old_nodes={n.name:e.c.write_tree(h,[n]) for n in root.children}
        original_ml={n.name:e.c.write_tree(h,[n]) for n in e.c.child(root,'MultiLevel').children}
        patch=gzip.decompress((folder/'mesh0.utf.gz').read_bytes());assert e.c.digest(patch)==report['geometry_sha256']
        replacement=e.c.read_tree(patch)[1][0];assert replacement.name=='Mesh0'
        ml=e.c.child(root,'MultiLevel');ml.children=[replacement if n.name=='Mesh0' else n for n in ml.children]
        # Skeleton object names and indices remain semantic. Salt only the
        # private resource filename referenced by each Cmpnd part.
        salt=uuid.uuid4().hex[:10];mapping={};cmpnd=e.c.child(root,'Cmpnd')
        for part in cmpnd.children:
            fields={n.name:n for n in part.children}
            if 'File name' not in fields:continue
            leaf=fields['File name'];old=leaf.blob.rstrip(b'\0').decode()
            if old not in mapping:mapping[old]=f'epaulette_{salt}_{len(mapping):02d}.3db'
            e.c.child(root,old).name=mapping[old];leaf.blob=mapping[old].encode()+b'\0'
        for node in root.children:
            if node.name in ('MultiLevel','Cmpnd'):continue
            source_name=next((k for k,v in mapping.items() if v==node.name),node.name)
            current_name=node.name;node.name=source_name
            assert e.c.write_tree(h,[node])==old_nodes[source_name],source_name
            node.name=current_name
        for n in ml.children:
            if n.name!='Mesh0':assert e.c.write_tree(h,[n])==original_ml[n.name]
        payload=e.c.write_tree(h,roots);decoded=e.c.read_tree(payload)[1][0];after,groups,faces=e.c.as_records(decoded)
        assert len(groups)==len(oldgroups)
        assert [e.c.blob(g,'Material_name') for g in groups]==[e.c.blob(g,'Material_name') for g in oldgroups]
        assert e.c.digest(e.c.write_tree(h,[e.c.mesh_of(decoded)]))==report['geometry_sha256']
        changed=0;protected=0
        for i,(a,b) in enumerate(zip(before,after)):
            assert np.array_equal(a['uv'],b['uv']) and a['skin']==b['skin']
            if not e.shoulder(name,a['p']):
                assert np.array_equal(a['p'],b['p']) and np.array_equal(a['n'],b['n']),'Edit outside epaulette'
                protected+=1
            elif not np.array_equal(a['p'],b['p']):changed+=1
        assert changed>0
        for r in after:
            assert np.isfinite(r['p']).all() and np.isfinite(r['uv']).all()
            assert abs(np.linalg.norm(r['n'])-1)<.001
            assert 1<=len(r['skin'])<=4 and abs(sum(r['skin'].values())-1)<.0001 and min(r['skin'].values())>=0
        flat=np.array([f for group in faces for f in group]);p=np.array([r['p'] for r in after]);n=np.array([r['n'] for r in after])
        cross=np.cross(p[flat[:,1]]-p[flat[:,0]],p[flat[:,2]]-p[flat[:,0]])
        assert np.linalg.norm(cross,axis=1).min()>1e-12
        assert len(flat)==report['triangles_after']<=report['triangle_limit'] and flat.max()<65536
        oldflat=np.array([t for group in oldfaces for t in group]);op=np.array([r['p'] for r in before]);on=np.array([r['n'] for r in before])
        oldcross=np.cross(op[oldflat[:,1]]-op[oldflat[:,0]],op[oldflat[:,2]]-op[oldflat[:,0]])
        negative=int(np.count_nonzero(np.einsum('ij,ij->i',cross,n[flat].sum(1))<0))
        original_negative=int(np.count_nonzero(np.einsum('ij,ij->i',oldcross,on[oldflat].sum(1))<0))
        assert negative<=original_negative
        oldseam=seam_error(before);newseam=seam_error(after);assert newseam<=oldseam+1e-5,(name,oldseam,newseam)
        lower=[i for i,r in enumerate(before) if r['p'][1]<-.1]
        assert np.array_equal(posed(before)[lower],posed(after)[lower])
        for a,b in zip(oldfaces,faces):
            protected_faces={tuple(t) for t in a if not any(e.shoulder(name,before[i]['p']) for i in t)}
            assert protected_faces<={tuple(t) for t in b}
        relative=f'CHARACTERS/BODIES/{name}.dfm';target=e.c.DataFolder(root=e.OUT/'stage').sync_data_file(relative,payload)
        assert e.c.digest(target.read_bytes())==e.c.digest(payload)
        e.dump(folder/'native_validation.json',dict(source_sha256=pins['source_sha256'],dfm_sha256=e.c.digest(payload),geometry_sha256=report['geometry_sha256'],
            dfm=str(target),relative=relative,export_salt=salt,private_resource_mapping=mapping,
            triangles=len(flat),vertices=len(after),material_groups=len(groups),protected_vertices=protected,
            no_new_degenerate_or_inverted_faces=True,preexisting_normal_disagreements=original_negative,
            original_uv_and_weights_preserved=True,lower_lods_and_marker_unchanged=True,materials_textures_rig_unchanged=True,
            synthetic_pose_seam_error_before_m=oldseam,synthetic_pose_seam_error_after_m=newseam,
            lower_body_pose_error_m=0,all_passed=True,installed=False,game_animation_validated=False))
        assert e.c.digest(Path(pins['source']).read_bytes())==pins['source_sha256']
        print('STAGED_AND_VERIFIED',name,len(flat),'triangles',len(after),'vertices','seam',newseam,flush=True)


if __name__=='__main__':main()
