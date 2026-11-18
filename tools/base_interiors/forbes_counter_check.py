"""Check native UVs, tangent frames and continuity across the counter sectors."""
import json,collections
import numpy as np
from native_common import dump,sha
from forbes_counter_audit import OUT,SOURCE,RETAIL


def area(t):
    u=t[:,1,6:8]-t[:,0,6:8];v=t[:,2,6:8]-t[:,0,6:8]
    return abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])*.5


def normalize(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-20)


def check_seams(a,b,parents,weights,selected):
    owners=collections.defaultdict(list);maximum=0.;count=0
    for i in selected:
        for x,y,z in ((0,1,2),(1,2,0),(2,0,1)):
            key=tuple(sorted(tuple(np.round(a[i,k,:3],5)) for k in (x,y)))
            owners[key].append((i,x,y,z))
    for edge,records in owners.items():
        if len(records)!=2:continue
        start=np.array(edge[0]);end=np.array(edge[1]);delta=end-start;curves=[]
        for i,x,y,z in records:
            ids=np.flatnonzero(parents==i);w=weights[ids].reshape(-1,3);v=b[ids].reshape(-1,b.shape[-1])
            on=abs(w[:,z])<2e-6;projected=w[on]@a[i,:,:3];positions=v[on,:3]
            fractions=np.clip((projected-start)@delta/(delta@delta),0,1)
            order=np.argsort(fractions);fractions=fractions[order];positions=positions[order]
            unique=np.r_[True,np.diff(fractions)>2e-6];curves.append((fractions[unique],positions[unique]))
        query=np.unique(np.r_[curves[0][0],curves[1][0]])
        assert all(len(s)>=2 for s,p in curves)
        samples=[np.array([np.interp(query,s,p[:,axis]) for axis in range(3)]).T for s,p in curves]
        gap=float(np.linalg.norm(samples[0]-samples[1],axis=1).max());maximum=max(maximum,gap);count+=1
    assert maximum<.0003,('New counter seam',maximum)
    return dict(shared_edges=count,max_gap_world_units=maximum)


def main():
    build=OUT/'modeled';native=json.loads((build/'native_validation.json').read_text())
    stats=json.loads((build/'geometry_validation.json').read_text());definition=json.loads((build/'features.json').read_text())
    before=np.load(OUT/'original_geometry.npz');after=np.load(build/'exported_geometry.npz');changed=set(definition['source_groups'])
    report=[]
    assert set(before.files)==set(after.files)
    for key in before.files:
        a=before[key].astype(float);b=after[key].astype(float)
        for repair in stats.get('source_uv_repairs',[]):
            if repair['group']!=key:continue
            v=a[repair['triangle'],repair['corner']]
            assert np.array_equal(v[8:10],repair['before'])
            for i,j in repair['matching_source_corners']:
                assert np.array_equal(a[i,j,:3],v[:3]) and np.array_equal(a[i,j,6:8],v[6:8])
                assert np.array_equal(a[i,j,8:10],repair['after'])
            v[8:10]=repair['after']
        assert np.isfinite(b).all(),key
        assert np.max(abs(np.linalg.norm(b[:,:,3:6],axis=-1)-1))<.002,key
        if key not in changed:
            assert np.allclose(a,b,atol=4e-6,rtol=0),key
            continue
        parents=np.array(stats['source_triangle_indices'][key]);assert len(parents)==len(b)
        all_weights=np.zeros((len(b),3,3));max_tangent=0.;max_uv=0.;max_depth=0.;moved=0;uv_errors=[]
        selected=definition['source_groups'][key]
        for i,t in enumerate(a):
            ids=np.flatnonzero(parents==i);out=b[ids]
            if i not in selected:
                assert len(ids)==1 and np.allclose(out[0],t,atol=4e-6,rtol=0),(key,i)
                continue
            matrix=np.vstack((t[:,6:8].T,np.ones(3)))
            w=np.c_[out[:,:,6:8].reshape(-1,2),np.ones(len(out)*3)]@np.linalg.inv(matrix).T
            assert w.min()>-3e-5,(key,i,float(w.min()))
            all_weights[ids]=w.reshape(-1,3,3);v=out.reshape(-1,out.shape[-1]);base=w@t
            directions=normalize(w@np.array(stats['displacement_directions'][key][str(i)]))
            delta=v[:,:3]-base[:,:3];depth=np.einsum('ij,ij->i',delta,directions)
            error=np.linalg.norm(delta-depth[:,None]*directions,axis=1)
            max_tangent=max(max_tangent,float(error.max()));max_depth=max(max_depth,float(abs(depth).max()))
            max_uv=max(max_uv,float(abs(v[:,6:-4]-base[:,6:-4]).max()));moved+=int(np.count_nonzero(abs(depth)>.003))
            uv_errors.append(abs(area(out).sum()-area(t[None])[0]))
            assert np.max(abs(np.linalg.norm(v[:,-4:-1],axis=1)-1))<.002
            assert np.max(abs(np.einsum('ij,ij->i',v[:,3:6],v[:,-4:-1])))<.0002
            assert np.all(abs(v[:,-1])==1)
        assert max_tangent<.0001,(key,max_tangent)
        assert max_uv<.0001,(key,max_uv)
        assert max_depth<.06 and moved>100,(key,max_depth,moved)
        assert max(uv_errors)<2e-6,(key,max(uv_errors))
        seams=check_seams(a,b,parents,all_weights,selected)
        report.append(dict(group=key,max_non_normal_displacement=max_tangent,max_uv_transfer_error=max_uv,
            max_depth_world_units=max_depth,displaced_corners=moved,max_uv_area_error=max(uv_errors),seams=seams))
    # Every authored front profile is applied on both mirrored outer halves.
    front=[r for r in stats['coverage'] if r['group']=='BAR_08']
    assert all(1.98<r['coverage']<2.001 for r in front),[(r['label'],r['coverage']) for r in front if not 1.98<r['coverage']<2.001]
    pins=json.loads((OUT/'sources.json').read_text())
    assert sha(SOURCE.read_bytes())==pins['installed_sha256'] and sha(RETAIL.read_bytes())==pins['original_sha256']
    dump(build/'surface_validation.json',dict(all_passed=True,cmp_sha256=native['exported_sha256'],groups=report,
        changed_groups_only=sorted(changed),front_profiles_applied_to_both_halves=True,
        all_other_native_geometry_preserved=True,all_true_uv_channels_preserved_except_documented_repair=True,
        source_uv_repairs=stats.get('source_uv_repairs',[]),tangent_frames_valid=True,sources_unchanged=True))
    print('COUNTER_CHECK_PASS',report,flush=True)


if __name__=='__main__':main()
