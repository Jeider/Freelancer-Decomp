"""Constrained panel triangulation in Blender; shared across depot families.

All contours of a surface are constraints in a single CDT, avoiding repeated
polygon fragmentation. UV seams/material boundaries remain source boundaries.
"""
import sys,json,collections,math,itertools
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blender_workspace import configure
configure('base_interiors')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from depot_surface_audit import OUT
from relief_mesh import intersect, area

BUILD=OUT/'modeled'


def cross2(a,b):return a[0]*b[1]-a[1]*b[0]


def offset_polygon(p,d):
    result=[]
    for i,b in enumerate(p):
        a=p[i-1];c=p[(i+1)%len(p)]
        u=b-a;v=c-b;u/=np.linalg.norm(u);v/=np.linalg.norm(v)
        nu=np.array([-u[1],u[0]]);nv=np.array([-v[1],v[0]])
        try:q=np.linalg.solve(np.stack((nu,nv)),np.array([nu@b+d,nv@b+d]))
        except np.linalg.LinAlgError:q=b+nu*d
        assert np.linalg.norm(q-b)<d*20
        result.append(q)
    return np.array(result)


def height(p,feature):
    boundary=feature['outer'];inside=False;x,y=p
    dist=float('inf')
    for a,b in zip(boundary,np.roll(boundary,-1,axis=0)):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        ab=b-a;t=np.clip((p-a)@ab/(ab@ab),0,1)
        dist=min(dist,float(np.linalg.norm(p-a-ab*t)))
    if dist<2e-8:return 0.
    if not inside:return 0.
    return feature['depth_world']*min(1.,dist/feature['bevel'])


def charts(t):
    parents=list(range(len(t)));owners=collections.defaultdict(list);normals={}
    def find(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for i,tri in enumerate(t):
        if tri.shape[-1]<8 or area(tri[:,6:8])<1e-9:continue
        n=np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]);length=np.linalg.norm(n)
        if length<1e-9:continue
        n/=length
        if abs(n[1])>.85:continue
        if np.min(tri[:,3:6]@tri[:,3:6].T)<.997:continue
        if n@tri[:,3:6].mean(0)<0:n=-n
        normals[i]=n
        for a,b in ((0,1),(1,2),(2,0)):
            key=tuple(sorted(tuple(np.round(tri[k,[0,1,2,6,7]],5)) for k in (a,b)))
            for j in owners[key]:
                if normals[j]@n>.99999:parents[find(i)]=find(j)
            owners[key].append(i)
    groups=collections.defaultdict(list)
    for i in normals:groups[find(i)].append(i)
    return [(ids,normals[ids[0]]) for ids in groups.values()]


def chart_boundary(triangles,normal):
    edges=collections.defaultdict(list)
    for tri in triangles:
        for a,b,c in ((0,1,2),(1,2,0),(2,0,1)):
            key=tuple(sorted(tuple(np.round(tri[k,[0,1,2,6,7]],5)) for k in (a,b)))
            edges[key].append((tri[a,:3],tri[b,:3],tri[c,:3]))
    result=[]
    for owners in edges.values():
        if len(owners)!=1:continue
        a,b,c=owners[0];direction=b-a;direction/=np.linalg.norm(direction)
        inward=np.cross(normal,direction)
        if inward@(c-a)<0:inward=-inward
        result.append((a,b,inward))
    return result


def triangulate(t,fs,normal,boundary,rim=.018):
    uv=t[:,6:8];input_vertices=[v.tolist() for v in uv];edges=[(0,1),(1,2),(2,0)]
    for f in fs:
        for polygon in (f['outer'],f['inner']):
            start=len(input_vertices);input_vertices.extend(polygon.tolist())
            edges.extend((start+i,start+(i+1)%len(polygon)) for i in range(len(polygon)))
    # A contour may meet an existing opening or a material/UV seam. Retain a
    # narrow native rim there, rather than displacing an unsupported edge.
    to_uv=np.linalg.pinv((t[1:,:3]-t[0,:3]).T).T@(uv[1:]-uv[0])
    for a,b,inward in boundary:
        q=np.asarray([a,b])+inward*rim
        xy=uv[0]+(q-t[0,:3])@to_uv
        if np.any(xy.max(0)<uv.min(0)-1e-5) or np.any(xy.min(0)>uv.max(0)+1e-5):continue
        start=len(input_vertices);input_vertices.extend(xy.tolist());edges.append((start,start+1))
    verts,_,faces,*_=delaunay_2d_cdt([Vector(p) for p in input_vertices],edges,[],0,1e-8)
    verts=np.asarray(verts,dtype=float)
    inv=np.linalg.inv(np.vstack((uv.T,np.ones(3))))
    weights=np.c_[verts,np.ones(len(verts))]@inv.T
    ids=np.asarray([face for face in faces if len(face)==3 and np.min(weights[list(face)].mean(0))>=-2e-7],dtype=int)
    if len(ids)==0:raise RuntimeError('CDT lost source triangle')
    out=[];uv_area=0.;deep_area=0.
    for tri in ids:
        w=weights[tri];points=verts[tri]
        if np.min(w)<-2e-5:raise RuntimeError(('CDT crossed source boundary',w.min()))
        # Snap only numerical noise on source borders; retain exact UVs elsewhere.
        w[abs(w)<2e-7]=0;w/=w.sum(1)[:,None]
        values=w@t;h=np.array([sum(height(p,f) for f in fs) for p in points])
        for vi,p in enumerate(values[:,:3]):
            distance=float('inf')
            for a,b,_ in boundary:
                ab=b-a;q=np.clip((p-a)@ab/(ab@ab),0,1)
                distance=min(distance,float(np.linalg.norm(p-a-ab*q)))
            h[vi]*=min(1.,distance/rim)
        values[:,:3]+=h[:,None]*normal
        uv_area+=area(values[:,6:8])
        cross=np.cross(values[1,:3]-values[0,:3],values[2,:3]-values[0,:3]);length=np.linalg.norm(cross)
        if length<1e-9:continue
        if cross@normal<0:values=values[[0,2,1]];cross=-cross
        values[:,3:6]=cross/length
        if np.max(abs(h))>1e-5:deep_area+=length*.5
        out.append(values)
    assert abs(uv_area-area(uv))<max(2e-7,area(uv)*1e-4),(uv_area,area(uv))
    return out,deep_area,abs(uv_area-area(uv))


def build(source_root=OUT):
    source_root=Path(source_root);BUILD=source_root/'modeled'
    report=json.loads((source_root/'surfaces.json').read_text(encoding='utf8'))
    definition=json.loads((BUILD/'features.json').read_text(encoding='utf8'))
    features=definition['features']
    data=np.load(source_root/'original_geometry.npz');result={k:data[k] for k in data.files}
    omitted=collections.defaultdict(set)
    for record in definition.get('redundant_source_faces',[]):
        t=data[record['group']];a=t[record['drop']];b=t[record['keep']]
        matches=[b[list(p)] for p in itertools.permutations(range(3))
                 if np.allclose(a[:,6:],b[list(p),6:],atol=1e-7,rtol=0)]
        assert len(matches)==1,('Redundant source UV mismatch',record)
        b=matches[0]
        assert np.allclose(a[:,3:6],b[:,3:6],atol=1e-6,rtol=0)
        assert np.linalg.norm(a[:,:3]-b[:,:3],axis=1).max()<record['max_position_delta']
        omitted[record['group']].add(record['drop'])
    summaries=[];coverage=[];errors=[];displacement_charts={}
    for f in features:
        f['outer']=np.asarray(f['points_px'],float)/768
        f['bevel']=f['bevel_px']/768
        f['inner']=offset_polygon(f['outer'],f['bevel'])
    for g in report['groups']:
        if g['part'] not in ('Root','room'):continue
        number=report['materials'][g['material']]['number']
        fs=[f for f in features if f['material']==number]
        if not fs:continue
        key=g['key'];t=data[key].astype(float);chart_list=charts(t);selected={};area_added=0.
        chart_list=[([i for i in ids if i not in omitted[key]],n) for ids,n in chart_list]
        chart_list=[(ids,n) for ids,n in chart_list if ids]
        displacement_charts[key]=[dict(triangles=ids,normal=n.tolist()) for ids,n in chart_list]
        for ci,(ids,normal) in enumerate(chart_list):
            accepted=[]
            for f in fs:
                overlap=sum(area(intersect(f['outer'],tri[:,6:8] if cross2(tri[1,6:8]-tri[0,6:8],tri[2,6:8]-tri[0,6:8])>0 else tri[::-1,6:8])) for tri in t[ids])
                fraction=overlap/area(f['outer'])
                if fraction<1e-5:continue
                full=fraction>=.01
                coverage.append(dict(group=key,chart=ci,feature=f['id'],label=f['label'],coverage=fraction,
                    applied=full,reason='Clipped to native UV placement with original boundary rim retained' if full else 'Negligible intersection; retained original'))
                if full:accepted.append(f)
            if not accepted:continue
            boundary_edges=chart_boundary(t[ids],normal)
            for ti in ids:
                tri=t[ti];uv=tri[:,6:8];boundary=uv if cross2(uv[1]-uv[0],uv[2]-uv[0])>0 else uv[::-1]
                hits=[f for f in accepted if area(intersect(f['outer'],boundary))>1e-10]
                if not hits:continue
                generated,changed_area,error=triangulate(tri,hits,normal,boundary_edges)
                selected[ti]=generated;area_added+=changed_area;errors.append(error)
        if not selected:continue
        out=[]
        for i,tri in enumerate(t):
            if i not in omitted[key]:out.extend(selected[i] if i in selected else [tri])
        result[key]=np.asarray(out,dtype='<f4')
        summaries.append(dict(group=key,material=number,source_triangles=len(t),result_triangles=len(out),
            replaced_source_triangles=len(selected),relief_surface_area=area_added))
        print('MODELED',key,number,len(t),'->',len(out),'source faces',len(selected),flush=True)
    np.savez_compressed(BUILD/'geometry.npz',**result)
    stats=dict(original_triangles=sum(len(data[k]) for k in data.files),
        result_triangles=sum(len(v) for v in result.values()),groups=summaries,coverage=coverage,displacement_charts=displacement_charts,
        max_uv_coverage_error=max(errors,default=0),
        method='Simultaneous constrained Delaunay triangulation of original triangle plus all contour and bevel edges; barycentric transfer of every source attribute.',
        old_relief_reused=False,redundant_source_faces_removed=definition.get('redundant_source_faces',[]))
    (BUILD/'geometry_validation.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf8')
    print('GEOMETRY_COMPLETE',stats['result_triangles'],flush=True)


if __name__=='__main__':
    if '--probe' in sys.argv:print(delaunay_2d_cdt.__doc__)
    else:build()
