"""Conforming UV-only subdivisions without welding nearby unrelated surfaces."""
import collections
import numpy as np
from scipy.spatial import cKDTree


def canonical(groups,tolerance=1e-8,pairs=None):
    lengths=[len(g['corners']) for g in groups];a=np.concatenate([g['corners'] for g in groups]).copy()
    pts,inv=np.unique(a[...,:3].reshape(-1,3),axis=0,return_inverse=True)
    parent=np.arange(len(pts))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,j in (cKDTree(pts).query_pairs(tolerance) if pairs is None else pairs):
        i,j=root(i),root(j)
        if i!=j:parent[max(i,j)]=min(i,j)
    owners=np.array([root(i) for i in range(len(pts))]);ids=owners[inv].reshape(-1,3)
    a[...,:3]=pts[ids];result=[];seen=set();at=0
    for g,count in zip(groups,lengths):
        keep=[]
        for i in range(at,at+count):
            key=tuple(sorted(int(x) for x in ids[i]));p=a[i,:,:3]
            if len(set(key))<3 or key in seen:continue
            if np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))<=1e-15:continue
            seen.add(key);keep.append(a[i])
        if keep:result.append(dict(g,corners=np.array(keep)))
        at+=count
    return result


def conform(groups):
    # Keep double precision until all triangles sharing a cut edge have the same
    # edge vertices. Early five-decimal rounding turns near-parallel bevels into
    # false T junctions and produces overlapping slivers.
    xyz=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
    points=np.unique(xyz,axis=0);tree=cKDTree(points);result=[]
    splits=0
    for g in groups:
        out=[]
        for tri in g['corners']:
            loop=[]
            for a,b in zip(tri,np.roll(tri,-1,axis=0)):
                loop.append(a);d=b[:3]-a[:3];length=np.linalg.norm(d)
                if length<1e-12:continue
                candidates=points[tree.query_ball_point((a[:3]+b[:3])/2,length/2+1e-8)]
                t=(candidates-a[:3])@d/(length*length)
                error=np.linalg.norm(candidates-(a[:3]+t[:,None]*d),axis=1)
                ids=np.where((t>1e-8)&(t<1-1e-8)&(error<4e-8))[0]
                for ix in ids[np.argsort(t[ids])]:
                    v=a+(b-a)*t[ix];v[:3]=candidates[ix];loop.append(v)
            if len(loop)==3:out.append(tri)
            else:
                splits+=1;center=tri.mean(0)
                for a,b in zip(loop,loop[1:]+loop[:1]):
                    if np.linalg.norm(np.cross(a[:3]-center[:3],b[:3]-center[:3]))>1e-15:
                        out.append(np.array([center,a,b]))
        result.append(dict(g,corners=np.array(out)))
    return result,splits


def clean(groups,source,closed):
    groups=canonical(groups)
    groups,splits=conform(groups)
    groups=canonical(groups)
    # Only repair near-coincident intersections when they actually create
    # overlapping edge fans. Leave already manifold tiny edges to the
    # topology-preserving collapse below.
    if closed:
        p=np.concatenate([g['corners'][...,:3] for g in groups])
        pts,ix=np.unique(p.reshape(-1,3),axis=0,return_inverse=True)
        edge_counts=collections.Counter(tuple(sorted((int(a),int(b))))
            for face in ix.reshape(-1,3) for a,b in zip(face,np.roll(face,-1)))
        near=[(a,b) for (a,b),n in edge_counts.items()
              if n>2 and np.linalg.norm(pts[a]-pts[b])<2e-6]
        if near:groups=canonical(groups,pairs=near)
    lengths=[len(g['corners']) for g in groups];tri=np.concatenate([g['corners'] for g in groups]).copy()
    material=np.concatenate([np.full(len(g['corners']),g['material'],dtype=np.int64) for g in groups])
    vertices,ids=np.unique(tri[...,:3].reshape(-1,3),axis=0,return_inverse=True)
    ids=ids.reshape(-1,3);alive=np.ones(len(ids),bool)
    original=np.unique(np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in source]).round(5),axis=0)
    dist=cKDTree(original).query(vertices)[0];preferred=dist<1e-8
    incident=collections.defaultdict(set)
    for i,face in enumerate(ids):
        for v in face:incident[int(v)].add(i)
    def neighbors(v):
        return {int(x) for i in incident[v] if alive[i] for x in ids[i] if x!=v}
    def remove(i):
        alive[i]=False
        for v in ids[i]:incident[int(v)].discard(i)
    collapses=0;maximum_move=0.;flips=0
    for iteration in range(10):
        p=vertices[ids].astype('<f4').astype(float)
        ar=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)
        bad=np.where(alive&(ar<=1.1e-8))[0]
        if not len(bad):break
        progressed=False
        for i in bad:
            if not alive[i]:continue
            face=ids[i]
            repaired=False
            # An inserted cut can make a long, almost-collinear face whose
            # short edge cannot legally collapse. Flip its shared diagonal
            # within the same continuous UV chart instead of deleting it.
            for edge in np.argsort([-np.linalg.norm(vertices[a]-vertices[b])
                                    for a,b in zip(face,np.roll(face,-1))]):
                a,b,c=map(int,np.roll(face,-int(edge)))
                adjacent=[k for k in incident[a]&incident[b] if alive[k] and k!=i]
                if len(adjacent)!=1:continue
                j=adjacent[0]
                if material[i]!=material[j]:continue
                d=next((int(v) for v in ids[j] if v not in (a,b)),None)
                if d is None or d==c or d in neighbors(c):continue
                attrs={int(v):tri[i,k].copy() for k,v in enumerate(ids[i])}
                compatible=True
                for k,v in enumerate(ids[j]):
                    if int(v) in attrs and np.max(abs(attrs[int(v)][6:8]-tri[j,k,6:8]))>1e-5:
                        compatible=False;break
                    attrs[int(v)]=tri[j,k].copy()
                if not compatible:continue
                new=np.array([[c,d,b],[d,c,a]])
                xyz=vertices[new].astype('<f4').astype(float)
                cross=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
                ref=vertices[ids[j]];n=np.cross(ref[1]-ref[0],ref[2]-ref[0]);nl=np.linalg.norm(n)
                if nl<1e-10 or np.any(cross@n<=0):continue
                if np.min(np.linalg.norm(cross,axis=1))<=1.1e-8:continue
                if abs(float((vertices[c]-ref[0])@n))/nl>3e-6:continue
                for k,newface in zip((i,j),new):
                    for v in ids[k]:incident[int(v)].discard(k)
                    ids[k]=newface;tri[k]=np.array([attrs[int(v)] for v in newface])
                    for v in newface:incident[int(v)].add(k)
                flips+=1;progressed=True;repaired=True;break
            if repaired:continue
            candidates=sorted((np.linalg.norm(vertices[a]-vertices[b]),int(a),int(b))
                for a,b in zip(face,np.roll(face,-1)))
            for distance,a,b in candidates:
                if a==b:remove(i);progressed=True;break
                if distance>.003:continue
                shared=incident[a]&incident[b]
                opposite={int(v) for k in shared if alive[k] for v in ids[k] if v not in (a,b)}
                if neighbors(a)&neighbors(b)!=opposite:continue
                if preferred[b] and not preferred[a]:a,b=b,a
                elif preferred[a] and preferred[b] and distance>1e-7:continue
                affected=list(incident[b]);maximum_move=max(maximum_move,float(distance))
                for k in affected:
                    if not alive[k]:continue
                    ids[k][ids[k]==b]=a;incident[a].add(k)
                    if len(set(ids[k]))<3:remove(k)
                incident[b].clear();progressed=True;collapses+=1;break
        if not progressed:break
    vertices=vertices.astype('<f4').astype(float)
    tri[...,:3]=vertices[ids]
    # A shared float32 position is written identically in every UV chart.
    result=[];at=0
    for g,count in zip(groups,lengths):
        a=tri[at:at+count][alive[at:at+count]]
        if len(a):result.append(dict(g,corners=a))
        at+=count
    # Distinct UV vertices are irrelevant to topology; test the welded positions.
    flat=tri[alive,...,:3].reshape(-1,3)
    _,remap=np.unique(flat,axis=0,return_inverse=True);faces=remap.reshape(-1,3)
    edges=collections.Counter(tuple(sorted((int(a),int(b)))) for f in faces for a,b in zip(f,np.roll(f,-1)))
    bad_edges=sum(count!=2 for count in edges.values())
    if closed:assert bad_edges==0,('UV subdivision topology',bad_edges)
    return result,dict(tjunction_splits=splits,micro_edge_collapses=collapses,
        micro_diagonal_flips=flips,maximum_micro_collapse_distance=maximum_move,nonmanifold_edges=bad_edges)
