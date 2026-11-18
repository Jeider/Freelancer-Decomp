"""Verify actual exported displacement and UV correspondence to native surfaces."""
import json
import numpy as np
from native_common import sha
from depot_surface_audit import OUT,ORIGINAL,CURRENT

BUILD=OUT/'modeled'


def main(source_root=OUT,original_path=ORIGINAL,current_path=CURRENT,door_groups=None):
    OUT=source_root;BUILD=OUT/'modeled'
    native=json.loads((BUILD/'native_validation.json').read_text())
    before=np.load(OUT/'original_geometry.npz');after=np.load(BUILD/'exported_geometry.npz')
    stats=json.loads((BUILD/'geometry_validation.json').read_text());changed={r['group'] for r in stats['groups']}
    report=[]
    for key in before.files:
        a=before[key].astype(float);b=after[key].astype(float)
        assert np.isfinite(b).all()
        assert np.max(abs(np.linalg.norm(b[:,:,3:6],axis=2)-1))<.002
        if key not in changed:
            assert np.allclose(a,b,atol=4e-6,rtol=0),key
            continue
        vertices=np.unique(b.reshape(-1,b.shape[-1]),axis=0)
        best=np.full(len(vertices),float('inf'));depth=np.zeros(len(vertices));uv1_error=np.zeros(len(vertices))
        # Original degenerate UV faces cannot be inverted. Their unchanged
        # position/UV tuples are validated directly instead of by barycentrics.
        native_tuples={tuple(np.r_[v[:3],v[6:]]) for v in a.reshape(-1,a.shape[-1])}
        for i,v in enumerate(vertices):
            if tuple(np.r_[v[:3],v[6:]]) in native_tuples:best[i]=0.
        chart_normals={i:np.array(c['normal']) for c in stats['displacement_charts'][key] for i in c['triangles']}
        for ti,t in enumerate(a):
            matrix=np.vstack((t[:,6:8].T,np.ones(3)))
            if abs(np.linalg.det(matrix))<1e-12:continue
            weights=np.c_[vertices[:,6:8],np.ones(len(vertices))]@np.linalg.inv(matrix).T
            valid=np.min(weights,axis=1)>=-3e-5
            if not valid.any():continue
            ids=np.where(valid)[0];projected=weights[ids]@t
            normal=chart_normals.get(ti)
            if normal is None:
                normal=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);normal/=max(np.linalg.norm(normal),1e-20)
            delta=vertices[ids,:3]-projected[:,:3];d=delta@normal
            tangent=np.linalg.norm(delta-d[:,None]*normal,axis=1)
            score=tangent+np.maximum(abs(d)-.30,0)
            better=score<best[ids];chosen=ids[better]
            best[chosen]=score[better];depth[chosen]=abs(d[better])
            if b.shape[-1]>8:uv1_error[chosen]=np.max(abs(vertices[chosen,8:]-projected[better,8:]),axis=1)
        assert np.max(best)<.00015,(key,float(np.max(best)))
        assert np.max(uv1_error)<.00015,(key,float(np.max(uv1_error)))
        assert np.max(depth)<.301,(key,float(np.max(depth)))
        assert np.count_nonzero(depth>.005)>4,key
        report.append(dict(group=key,tested_vertices=len(vertices),max_tangential_error=float(best.max()),
            max_secondary_uv_error=float(uv1_error.max()),max_normal_displacement=float(depth.max()),
            vertices_displaced_over_5mm=int(np.count_nonzero(depth>.005))))
    pins=json.loads((OUT/'sources.json').read_text())
    assert sha(original_path.read_bytes())==pins['original_sha256']
    assert sha(current_path.read_bytes())==pins['installed_sha256']
    (BUILD/'surface_validation.json').write_text(json.dumps(dict(groups=report,all_passed=True,
        cmp_sha256=native['exported_sha256'],
        sources_unchanged=True,method='Each exported vertex matched by UV barycentrics to a compatible original triangle, with normal-only geometric displacement and secondary UV validation.'),indent=2)+'\n')
    door_features=[f for f in json.loads((BUILD/'features.json').read_text())['features'] if f.get('door_detail')]
    if door_features:
        coverage=[]
        for feature in door_features:
            rows=[r for r in stats['coverage'] if r['feature']==feature['id'] and r['applied']]
            total=sum(r['coverage'] for r in rows)
            assert abs(total-4)<.0001,(feature['id'],total)
            coverage.append(dict(feature=feature['id'],label=feature['label'],complete_placements=round(total),charts=rows))
        placements=[]
        for key,center in (door_groups or [('room_05',5.43),('room_02',2.57)]):
            original=before[key].reshape(-1,before[key].shape[-1])
            exported=after[key].reshape(-1,after[key].shape[-1])
            for xsign in (-1,1):
                for zsign in (-1,1):
                    def select(v):
                        return v[(abs(v[:,0]-xsign*center)<.78)&(v[:,1]>=0)&(v[:,1]<2.68)&(abs(v[:,2]-zsign*9.796)<.15)]
                    old=select(original);new=select(exported)
                    plane=float(np.median(old[:,2]))
                    delta=abs(new[:,2]-plane)
                    count=int(np.count_nonzero(delta>.005))
                    assert count>100,(key,xsign,zsign,count)
                    placements.append(dict(group=key,x=xsign*center,z=plane,displaced_corners_over_5mm=count,
                        max_depth=float(delta.max())))
        previous_path=BUILD/'door_detail/before_source.json'
        previous=json.loads(previous_path.read_text()) if previous_path.exists() else dict(
            triangles=pins['source_triangles'],sha256=pins['installed_sha256'],source=str(current_path))
        (BUILD/'door_validation.json').write_text(json.dumps(dict(all_passed=True,
            cmp_sha256=native['exported_sha256'],previous=previous,
            added_triangles=stats['result_triangles']-previous['triangles'],
            feature_coverage=coverage,world_placements=placements,
            method='Every authored door contour has four full UV placements; each of eight world-space door/panel locations has exported geometric displacement. Image-contour quality is assessed separately in textured renders.'),indent=2)+'\n')
    print('SURFACE_CHECK_PASS',len(report),'groups;',sum(r['vertices_displaced_over_5mm'] for r in report),'vertices with real displacement')


if __name__=='__main__':main()
