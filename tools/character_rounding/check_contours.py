"""Validate reconstructed DFM bytes, native protected regions and skin data."""
import copy
import gzip
import json
import struct
import argparse
from collections import Counter
import numpy as np
from contours import (OUT, OLD, GAME, digest, mesh_of, read_tree, write_tree, child,
                      arr, blob, triangles, leaves, load_policy, excluded_name,
                      load_json, original, as_records)


def reconstruct(name, live, previous=False):
    folder=OUT/name
    patch_path=folder/('previous_mesh0.utf.gz' if previous else 'mesh0.utf.gz')
    if not patch_path.exists():
        report=json.loads((folder/'report.json').read_text())
        assert digest(live)==report['previous_sha256' if previous else 'output_sha256'],'Compiled patch was cleaned after installation; live file does not match'
        return live
    patch=gzip.decompress(patch_path.read_bytes())
    roots=read_tree(patch)[1]
    assert len(roots)==1 and roots[0].name=='Mesh0'
    if not previous:assert digest(patch)==json.loads((folder/'report.json').read_text())['patch_sha256']
    header,objects=read_tree(live);root=objects[0];ml=child(root,'MultiLevel')
    if write_tree(header,[mesh_of(root)])==patch:return live
    ml.children=[roots[0] if m.name=='Mesh0' else m for m in ml.children]
    return write_tree(header,objects)


def check(name):
    folder=OUT/name;r=json.loads((folder/'report.json').read_text());addon=OUT.name=='bracer_starts'
    hero=OUT.name=='hero_bodies'
    limit=r['triangle_limit'] if addon or hero else load_policy()['max_mesh0_triangles']
    if addon:assert limit==r['triangles_before']+100<=2100
    if hero:assert limit==r['triangles_before']+2000<=4100
    assert not excluded_name(name)
    live=(GAME/'DATA/CHARACTERS/BODIES'/(name+'.dfm')).read_bytes()
    assert digest(live) in (r['previous_sha256'],r['output_sha256']),name+' independently changed'
    previous=reconstruct(name,live,previous=True)
    assert digest(previous)==r['previous_sha256'],'Rollback patch mismatch'
    output=reconstruct(name,live)
    assert digest(output)==r['output_sha256'],'Reconstructed DFM hash mismatch'
    old={p:v for p,_,v in leaves(previous)[1]};new={p:v for p,_,v in leaves(output)[1]}
    changed=[p for p in set(old)|set(new) if old.get(p)!=new.get(p)]
    assert all('/MultiLevel/Mesh0/' in p for p in changed)
    root=read_tree(output)[1][0];mesh=mesh_of(root);geo=child(mesh,'Geometry')
    p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3);pi=arr(geo,'Point_indices','<u4').ravel()
    uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
    first=arr(geo,'Point_bone_first','<u4').ravel();count=arr(geo,'Point_bone_count','<u4').ravel()
    bones=arr(geo,'Bone_id_chain','<u4').ravel();weights=arr(geo,'Bone_weight_chain','<f4').ravel()
    assert len(p)==len(n)==len(first)==len(count) and len(pi)==len(ui)<65536
    assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all() and np.isfinite(weights).all()
    assert np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-3,'Invalid vertex normals'
    assert pi.max()<len(p) and ui.max()<len(uv) and weights.min()>=0
    assert 0<count.min()<=count.max()<=4
    valid={int(arr(part,'Index','<u4')[0,0]) for part in child(root,'Cmpnd').children if part.children and any(c.name=='Index' for c in part.children)}
    assert set(map(int,bones))<=valid
    for f,c in zip(first,count):assert f+c<=len(weights) and abs(float(weights[f:f+c].sum())-1)<1e-4
    groups=[g for g in child(mesh,'Face_groups').children if g.children]
    fs=[triangles(g) for g in groups];flat=np.array([t for g in fs for t in g])
    assert len(flat)==r['triangles_after']<=limit and flat.min()>=0 and flat.max()<len(pi)
    source_path,source=(None,previous) if addon or hero else original(name)
    src=read_tree(source)[1][0];src_records,src_groups,src_faces=as_records(src)
    dst_records,_,_=as_records(root)
    assert len(src_groups)==len(groups)
    if hero and name=='li_hatcher_body':
        for source_group,source_faces,output_faces in zip(src_groups,src_faces,fs):
            if blob(source_group,'Material_name').rstrip(b'\0')==b'hatcher_body_4':
                assert source_faces==[tuple(t) for t in output_faces], 'Accepted Hatcher belt retessellated'
    protected=0
    protected_outside=0
    def in_region(pos):
        for pr in r.get('profiles',[]):
            center=np.array(pr['center']);axis=np.array(pr['axis']);d=pos-center;t=d@axis
            if pos[0]*pr['side']>.17 and abs(t)<.065 and np.linalg.norm(d-axis*t)<.105:return True
        return False
    for i,a in enumerate(src_records):
        b=dst_records[i]
        assert np.array_equal(a['uv'],b['uv']) and np.array_equal(a['uv1'],b['uv1'])
        assert a['skin']==b['skin'],'Existing skin weights changed'
        if hero:
            assert np.array_equal(a['n'],b['n']),'Accepted normal field changed'
            x,y,z=a['p']
            allowed=((y>.465 and abs(x-.004084)<.125) or (y>.40 and .125<abs(x)<.225)) if name=='li_hatcher_body' else (abs(x)>.20 and -.10<y<.16)
            if not allowed:
                assert np.array_equal(a['p'],b['p']),'Vertex outside the approved contour band changed'
                protected_outside+=1
        if addon and not in_region(a['p']):
            assert np.array_equal(a['p'],b['p']) and np.array_equal(a['n'],b['n']),'Point outside upper bracer changed'
            protected_outside+=1
        if a['p'][1]<-.10:
            assert np.array_equal(a['p'],b['p']) and np.array_equal(a['n'],b['n'])
            protected+=1
    # No geometry refinement at all on a protected lower-body triangle.
    for original_group,new_group in zip(src_faces,fs):
        old_lower={tuple(t) for t in original_group if max(src_records[i]['p'][1] for i in t)<-.10}
        new_lower={tuple(t) for t in new_group if max(dst_records[i]['p'][1] for i in t)<-.10}
        assert old_lower==new_lower
    exported=load_json(folder/'after.json.gz')
    assert np.array_equal(p,np.array(exported['points'],dtype='<f4'))
    assert fs==[g['faces'] for g in exported['groups']]
    if addon:
        for old_group,new_group in zip(src_faces,fs):
            def crosses_region(t):
                p=np.array([src_records[i]['p'] for i in t])
                probes=list(p)+[p.mean(0)]+[(a+b)/2 for a,b in zip(p,np.roll(p,-1,axis=0))]
                return any(in_region(q) for q in probes)
            untouched={tuple(t) for t in old_group if not crosses_region(t)}
            assert untouched<={tuple(t) for t in new_group},'Unrelated surface retessellated'
        assert all(in_region(rec['p']) for rec in dst_records[len(src_records):]),'New vertex outside the upper bracer band'
        def boundary(records,groups):
            edges=Counter()
            for group in groups:
                for tri in group:
                    for a,b in zip(tri,tri[1:]+tri[:1]):
                        pa,pb=records[a]['p'],records[b]['p']
                        k=tuple(sorted((tuple(pa.round(5)),tuple(pb.round(5)))))
                        if k[0]!=k[1]:edges[k]+=1
            return Counter({k:v for k,v in edges.items() if v==1})
        old_open=boundary(src_records,src_faces);new_open=boundary(dst_records,fs)
        assert len(new_open)<=len(old_open),'New open mesh edges: '+str((len(old_open),len(new_open)))
        old_degenerate=sum(np.linalg.norm(np.cross(src_records[t[1]]['p']-src_records[t[0]]['p'],src_records[t[2]]['p']-src_records[t[0]]['p']))<1e-12 for g in src_faces for t in g)
        new_degenerate=sum(np.linalg.norm(np.cross(dst_records[t[1]]['p']-dst_records[t[0]]['p'],dst_records[t[2]]['p']-dst_records[t[0]]['p']))<1e-12 for g in fs for t in g)
        assert new_degenerate<=old_degenerate,'New degenerate faces'
    def wrist_boundaries(records,groups):
        edges=Counter()
        for group in groups:
            for tri in group:
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    pa=records[a]['p'];pb=records[b]['p']
                    if min(abs(pa[0]),abs(pb[0]))>.20 and max(pa[1],pb[1])<.08:
                        edge=tuple(sorted((tuple(pa.round(5)),tuple(pb.round(5)))))
                        if edge[0]!=edge[1]:edges[edge]+=1
        return sum(v==1 for v in edges.values())
    before_boundary=wrist_boundaries(src_records,src_faces);after_boundary=wrist_boundaries(dst_records,fs)
    if before_boundary==0:assert after_boundary==0,'Opened a previously closed wrist surface'
    # Unchanged lower body also stays identical under synthetic bone transforms.
    # This is an LBS consistency test, not playback of a game animation.
    def posed(record):
        q=np.zeros(3)
        for bone,w in record['skin'].items():
            angle=((bone%7)-3)*.12;c,s=np.cos(angle),np.sin(angle)
            rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
            q+=w*(rotation@record['p']+np.array([0,(bone%3)*.007,0]))
        return q
    pose_error=max((np.linalg.norm(posed(a)-posed(dst_records[i])) for i,a in enumerate(src_records) if a['p'][1]<-.10),default=0)
    assert pose_error==0
    seam_pose_error=0.
    if hero:
        def posed_seams(records):
            clusters={};error=0.
            for record in records:
                key=tuple(record['p'].round(6));point=posed(record)
                if key in clusters:error=max(error,float(np.linalg.norm(point-clusters[key])))
                else:clusters[key]=point
            return error
        seam_pose_error=posed_seams(dst_records)
        assert seam_pose_error<=posed_seams(src_records)+1e-5,'New animated seam separation'
    lo=np.array([a['p'] for a in src_records]);bounds_change=np.maximum(lo.min(0)-p.min(0),p.max(0)-lo.max(0))
    assert bounds_change.max()<2e-6,'Expanded original bounding box'
    lods={m.name:sum(len(triangles(g)) for g in child(m,'Face_groups').children if g.children)
          for m in child(root,'MultiLevel').children if m.name.startswith('Mesh')}
    return dict(name=name,triangles=len(flat),vertices=len(p),skin_influences=len(weights),
                max_influences=int(count.max()),protected_lower_vertices=protected,protected_outside_vertices=protected_outside,
                wrist_boundary_edges_before=before_boundary,wrist_boundary_edges_after=after_boundary,
                lower_body_pose_error_m=float(pose_error),seam_pose_error_m=seam_pose_error,bounding_growth_m=float(max(0,bounds_change.max())),
                lod_triangles=lods,output_sha256=r['output_sha256'],rollback_verified=True,
                only_mesh0_changed=True,game_animation_validated=False)


def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('--package',choices=['contours_2k','bracer_starts','hero_bodies'],default='contours_2k');args=ap.parse_args()
    OUT=OUT.parent/args.package
    inventory=json.loads((OLD/'inventory.json').read_text())
    if args.package=='bracer_starts':
        from bracer_starts import TARGETS
        expected=set(TARGETS)
    elif args.package=='hero_bodies':
        from hero_bodies import TARGETS
        expected=set(TARGETS)
    else:expected={r['name'] for r in inventory if not excluded_name(r['name'])}
    reports={p.parent.name for p in OUT.glob('*/report.json')}
    assert expected==reports,'Incomplete or unexpected model set'
    results=[];errors=[]
    for name in sorted(expected):
        try:results.append(check(name))
        except Exception as error:errors.append(dict(name=name,error=repr(error)))
    result=dict(valid=len(results),errors=errors,results=results,game_animation_validated=False)
    (OUT/'validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(valid=len(results),errors=errors,max_triangles=max(r['triangles'] for r in results),
                         max_bounding_growth_m=max(r['bounding_growth_m'] for r in results)),indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
