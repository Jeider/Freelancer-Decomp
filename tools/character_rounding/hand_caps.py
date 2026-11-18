"""Explicit continuous fingertip topology, fitted to the actual finger surface."""
import math
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.geometry import closest_point_on_tri,barycentric_transform


def rebuild(mesh,data,chains,origins,width):
    bm=bmesh.new();bm.from_mesh(mesh);deform=bm.verts.layers.deform.active;uv=bm.loops.layers.uv.active
    source=np.array(data['points']);source_faces=[t for g in data['groups'] for t in g['faces']]
    for finger,chain in chains.items():
        axis=origins[chain[3]]-origins[chain[2]];length=np.linalg.norm(axis);axis/=length
        plane=origins[chain[2]]+axis*(length*.52)
        selected=[f for f in bm.faces if all(sum(v[deform].get(i,0) for i in chain)>.35 for v in f.verts)]
        geom=set(selected)
        for f in selected:geom.update(f.edges);geom.update(f.verts)
        result=bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=plane,plane_no=axis,clear_outer=True,clear_inner=False)
        edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
        assert len(edges)>=6,(finger,len(edges))
        graph={}
        for e in edges:
            a,b=e.verts;graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
        assert all(len(ns)==2 for ns in graph.values())
        first=edges[0].verts[0];ring=[first];prev=None;current=first
        while True:
            nxt=next(v for v in graph[current] if v!=prev)
            if nxt==first:break
            ring.append(nxt);prev,current=current,nxt
        assert len(ring)==len(graph)
        edge=next(e for e in ring[0].link_edges if ring[1] in e.verts)
        if any(loop.vert==ring[0] and loop.link_loop_next.vert==ring[1] for loop in edge.link_loops):ring.reverse()
        center=np.array([v.co[:] for v in ring]).mean(0)
        side=width-axis*np.dot(width,axis);side/=np.linalg.norm(side);up=np.cross(axis,side)
        radial=np.array([v.co[:] for v in ring])-center
        ra=max(abs(radial@side));rb=max(abs(radial@up))
        theta=np.arctan2((radial@up)/rb,(radial@side)/ra)
        # The final reach comes from the original mesh, never an arbitrary bone
        # length. The old cap's lateral offset is retained to keep grips aligned.
        ids=[i for i,w in enumerate(data['skin']) if w.get(str(chain[2]),0)>.6]
        candidates=source[ids];z=(candidates-center)@axis;reach=float(z.max())
        depth=min((ra+rb)*.5,reach*.65)
        capbase=reach-depth
        previous=ring
        source_triangles=[]
        for t in source_faces:
            ix=[data['point_indices'][i] for i in t]
            if max(data['skin'][i].get(str(chain[2]),0) for i in ix)<.4:continue
            vs=[Vector(source[i]) for i in ix];us=[Vector((*data['uv'][data['uv_indices'][i]],0)) for i in t]
            source_triangles.append((vs,us))
        def texture(face):
            face.material_index=0
            facecenter=face.calc_center_median()
            for loop in face.loops:
                query=loop.vert.co*.999+facecenter*.001;best=None
                for vs,us in source_triangles:
                    point=closest_point_on_tri(query,*vs);dist=(query-point).length_squared
                    if best is None or dist<best[0]:best=(dist,barycentric_transform(point,*vs,*us))
                loop[uv].uv=best[1].xy
        for axial,radius in [(capbase,1.),(capbase+depth*.5,math.sqrt(.75)),(capbase+depth*.8660254,.5)]:
            new=[]
            for angle in theta:
                p=center+axis*axial+(side*(ra*math.cos(angle))+up*(rb*math.sin(angle)))*radius
                v=bm.verts.new(p);v[deform][chain[2]]=1;new.append(v)
            for j in range(len(ring)):
                k=(j+1)%len(ring);face=bm.faces.new((previous[j],previous[k],new[k],new[j]));texture(face)
            previous=new
        tip=bm.verts.new(center+axis*reach);tip[deform][chain[2]]=1
        for j in range(len(ring)):
            face=bm.faces.new((previous[j],previous[(j+1)%len(ring)],tip));texture(face)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
    bm.to_mesh(mesh);bm.free();mesh.update()
