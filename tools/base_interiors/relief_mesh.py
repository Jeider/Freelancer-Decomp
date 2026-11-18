"""Sparse, replacement geometry from reviewed convex UV contours.

No uniform subdivision. Original triangles outside the selected features remain
unchanged. Each clipped triangle retains both UVs by source barycentrics.
"""
import math
import numpy as np
EPS=1e-10
def signed(p,a,b):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def area(poly):
    if len(poly)<3:return 0.
    p=np.asarray(poly);return abs(float(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))))*.5
def clip(poly,a,b,inside=True):
    if len(poly)==0:return []
    out=[];prev=poly[-1];dp=signed(prev,a,b)*(1 if inside else -1)
    for cur in poly:
        dc=signed(cur,a,b)*(1 if inside else -1)
        if (dc>=-EPS)!=(dp>=-EPS):out.append(prev+(cur-prev)*(dp/(dp-dc)))
        if dc>=-EPS:out.append(cur)
        prev,dp=cur,dc
    return out
def intersect(poly,boundary):
    result=list(poly)
    for a,b in zip(boundary,np.roll(boundary,-1,axis=0)):
        result=clip(result,a,b)
        if len(result)<3:return []
    return result

def refine(corners,features,rotation):
    out=[];hits={};affected=0;skipped=0;max_depth=0.;max_uv_error=0.;max_area_error=0.;examples=[]
    # A quad may have unequal UV scale in its two source triangles. A separate
    # per-triangle depth opens a visible diagonal crack through an inset. Use
    # one depth metric for each connected planar UV patch instead.
    parents=list(range(len(corners)));edge_owner={};metrics={};geonormals={}
    def find(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for ti,c in enumerate(corners):
        t=c.astype(float);n=t[:,3:6];n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
        if area(t[:,6:8])<.000015 or np.min(n@n.T)<.997 or abs((n.mean(0)@rotation)[1])>.70:continue
        basis=np.linalg.solve(t[1:,6:8]-t[0,6:8],t[1:,:3]-t[0,:3]);metrics[ti]=np.linalg.norm(basis,axis=1)
        gn=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);gn/=max(np.linalg.norm(gn),1e-12);geonormals[ti]=gn
        for a,b in ((0,1),(1,2),(2,0)):
            key=tuple(sorted(tuple(np.round(t[k,[0,1,2,6,7]],6)) for k in (a,b)))
            for other in edge_owner.get(key,[]):
                if abs(gn@geonormals[other])>.9999:parents[find(ti)]=find(other)
            edge_owner.setdefault(key,[]).append(ti)
    patch_metrics={}
    for ti,units in metrics.items():patch_metrics.setdefault(find(ti),[]).append(units)
    patch_metrics={k:np.median(v,axis=0) for k,v in patch_metrics.items()}
    depth_consistency={};max_depth_seam=0.
    for ti,original in enumerate(corners):
        t=original.astype(float);uv=t[:,6:8];uv_area=area(uv)
        normals=t[:,3:6];normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
        if uv_area<.000015 or np.min(normals@normals.T)<.997 or abs((normals.mean(0)@rotation)[1])>.70:
            out.append(original);skipped+=1;continue
        if signed(uv[2],uv[0],uv[1])<0:uv=uv[::-1]
        basis=np.linalg.solve(t[1:,6:8]-t[0,6:8],t[1:,:3]-t[0,:3])
        units=patch_metrics[find(ti)];scale=math.sqrt(units[0]*units[1])
        mat=np.vstack((t[:,6:8].T,np.ones(3)))
        sign=1 if np.dot(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]),normals.mean(0))>=0 else -1
        remaining=[list(np.column_stack((uv,np.zeros(3))))];generated=[];did_hit=False
        def emit(poly):
            nonlocal max_uv_error
            if area(poly)<1e-10:return
            poly=np.asarray(poly)
            weights=np.linalg.solve(mat,np.vstack((poly[:,:2].T,np.ones(len(poly))))).T
            values=weights@t
            nn=weights@normals;nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-12)
            values[:,:3]+=nn*poly[:,2,None]
            values[:,3:6]=nn
            max_uv_error=max(max_uv_error,float(abs(values[:,6:8]-poly[:,:2]).max()))
            for j in range(1,len(poly)-1):
                tri=values[[0,j,j+1]].copy();cross=np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]);length=np.linalg.norm(cross)
                if length<1e-10:continue
                if np.ptp(poly[:,2])>1e-10:
                    face=cross/length
                    if face@nn.mean(0)<0:face=-face
                    tri[:,3:6]=face
                if np.dot(cross,nn.mean(0))*sign<0:tri=tri[[0,2,1]]
                generated.append(tri)
        for fi,f in enumerate(features):
            base=np.asarray(f['uv']);tiles=[]
            for u in range(math.floor(uv[:,0].min()),math.ceil(uv[:,0].max())):
                for v in range(math.floor(uv[:,1].min()),math.ceil(uv[:,1].max())):tiles.append((u,v))
            assert len(tiles)<256,'Unexpected repeated atlas; needs explicit review'
            for tile in tiles:
                outer=base+tile
                if np.any(outer.min(0)>uv.max(0)) or np.any(outer.max(0)<uv.min(0)):continue
                if area(intersect(outer,uv))<1e-9:continue
                did_hit=True;rest_pieces=[]
                for piece in remaining:
                    if area(intersect(piece,outer))<1e-10:rest_pieces.append(piece);continue
                    rest=piece
                    for a,b in zip(outer,np.roll(outer,-1,axis=0)):
                        outside=clip(rest,a,b,False)
                        if area(outside)>1e-10:rest_pieces.append(outside)
                        rest=clip(rest,a,b)
                        if len(rest)<3:break
                remaining=rest_pieces
                # Bounded by the narrowest projected feature dimension, so small
                # louvre grooves cannot become deep stretched wedges.
                span=(outer.max(0)-outer.min(0))*units
                depth=np.sign(f['depth_uv'])*min(abs(f['depth_uv'])*scale,float(span.min())*.22)
                key=(find(ti),fi,tile)
                if key in depth_consistency:max_depth_seam=max(max_depth_seam,abs(depth-depth_consistency[key]))
                depth_consistency[key]=depth
                max_depth=max(max_depth,abs(depth))
                mid=outer.mean(0);weights=np.linalg.solve(mat,np.r_[mid,1])
                if weights.min()>-1e-6:
                    center=weights@t[:,:3];normal=weights@normals;normal/=np.linalg.norm(normal)
                    size=max(np.linalg.norm((outer-mid)@basis,axis=1).max()*2,.01)
                    examples.append(dict(center=center.tolist(),normal=normal.tolist(),tangent=basis[0].tolist(),size=float(size),label=f['label'],depth=float(depth)))
                inner=outer.mean(0)+(outer-outer.mean(0))*f['inset']
                emit(intersect(np.column_stack((inner,np.full(len(inner),depth))),uv))
                for j in range(len(outer)):
                    k=(j+1)%len(outer)
                    emit(intersect(np.array([[*outer[j],0],[*outer[k],0],[*inner[k],depth],[*inner[j],depth]]),uv))
                hits[f['label']]=hits.get(f['label'],0)+1
        if not did_hit:out.append(original);continue
        for piece in remaining:emit(piece)
        err=abs(sum(area(tri[:,6:8]) for tri in generated)-uv_area)
        max_area_error=max(max_area_error,err)
        assert err<max(2e-8,uv_area*2e-5),('UV coverage changed; overlapping contours or holes',err,uv_area)
        out.extend(generated);affected+=1
    result=np.asarray(out,dtype='<f4')
    assert np.isfinite(result).all()
    return result,dict(source_triangles=len(corners),result_triangles=len(result),source_triangles_with_relief=affected,
                       curved_small_or_horizontal_triangles_preserved=skipped,hits=hits,max_depth=max_depth,
                       max_uv_transfer_error=max_uv_error,max_uv_coverage_error=max_area_error,
                       planar_patch_count=len(patch_metrics),max_connected_patch_depth_discontinuity=max_depth_seam,
                       inspection_candidates=sorted(examples,key=lambda q:-q['size'])[:3])
