"""Sew authored coat shoulders to clipped native forearms, preserving cuff UVs."""
import math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import hassler_native_step03 as s3

CUT=.30
def key(p):return tuple(np.round(p,7))
def bounded(w):
    w=w.copy();w[np.argsort(w)[:-4]]=0;return w/w.sum()

def edge_loops(edges):
    graph={}
    for a,b in edges:graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    assert all(len(ns)==2 for ns in graph.values()),[(p,len(ns)) for p,ns in graph.items() if len(ns)!=2]
    pending=set(graph);loops=[]
    while pending:
        start=next(iter(pending));loop=[start];previous=None;current=start
        while True:
            nxt=next(n for n in graph[current] if n!=previous)
            if nxt==start:break
            loop.append(nxt);previous,current=current,nxt
        pending-=set(loop);loops.append(loop)
    return loops

def clip(records):
    out=[]
    for a,b in zip(records,records[1:]+records[:1]):
        da=CUT-a[0][2];db=CUT-b[0][2]
        if da>=-1e-8:out.append(a)
        if (da>1e-8 and db<-1e-8) or (da<-1e-8 and db>1e-8):
            t=da/(da-db);out.append(tuple(x+(y-x)*t for x,y in zip(a,b)))
    return out

def prepare(base,names,g):
    """Split at an actual native sleeve section, not a guessed circular cuff."""
    weights=np.zeros((len(base.data.vertices),len(names)))
    for v in base.data.vertices:
        for a in v.groups:weights[v.index,names.index(base.vertex_groups[a.group].name)]=a.weight
    limbs=[i for i,n in enumerate(names) if n in ('LUpArm','RUpArm','LLowArm','RLowArm','LHand','RHand')]
    uv=base.data.uv_layers.active;records=[];cutedges=[]
    native_offset=len(g.mats)
    for mat in base.data.materials:g.mats.append(mat)
    for f in base.data.polygons:
        pp=[np.array(base.data.vertices[i].co,dtype=float) for i in f.vertices]
        if min(p[2] for p in pp)>=CUT or np.mean(weights[list(f.vertices)][:,limbs].sum(1))<.01:continue
        rr=clip([(p,weights[i],np.array(uv.data[li].uv)) for p,i,li in zip(pp,f.vertices,f.loop_indices)])
        if len(rr)<3 or min(abs(a[0][0]) for a in rr)<=.19:continue
        records.append((f.material_index,rr))
        for a,b in zip(rr,rr[1:]+rr[:1]):
            if abs(a[0][2]-CUT)<1e-7 and abs(b[0][2]-CUT)<1e-7:cutedges.append((key(a[0]),key(b[0])))
    loops=edge_loops(set(tuple(sorted(e)) for e in cutedges));assert len(loops)==2
    # Keep the complete lower torso/belt. Native arm faces are incorporated into
    # the coat below; original upper torso/sleeve faces are archived with step 04.
    keep=[]
    for f in base.data.polygons:
        pp=[base.data.vertices[i].co for i in f.vertices]
        belt=f.material_index==1 and all(uv.data[li].uv.x<.2 for li in f.loop_indices) and all(-.02<p.z<.3 for p in pp)
        arm=min(abs(p.x) for p in pp)>.19 and np.mean(weights[list(f.vertices)][:,limbs].sum(1))>.01
        if belt or (not arm and max(p.z for p in pp)<=.235):keep.append(f.index)
    return records,loops,native_offset,keep

def root_boundaries(g):
    adjacent={}
    for _,f in g.faces:
        for a,b in zip(f,f[1:]+f[:1]):adjacent[tuple(sorted((a,b)))]=adjacent.get(tuple(sorted((a,b))),0)+1
    edges=[e for e,count in adjacent.items() if count==1 and all(.34<g.p[i][2]<.57 and abs(g.p[i][0])>.12 for i in e)]
    loops=edge_loops(edges);assert len(loops)==2
    return loops

def insert_root(g,a,b,t):
    p=g.p[a]*(1-t)+g.p[b]*t;idx=g.vertex(p);g.w[idx]=bounded(g.w[a]*(1-t)+g.w[b]*t)
    for fi,((mat,f),uv) in enumerate(zip(g.faces,g.uv)):
        for j,(x,y) in enumerate(zip(f,f[1:]+f[:1])):
            if {x,y}=={a,b}:
                k=t if x==a else 1-t
                q=np.array(uv[j])*(1-k)+np.array(uv[(j+1)%len(uv)])*k
                g.faces[fi]=(mat,f[:j+1]+[idx]+f[j+1:]);g.uv[fi]=uv[:j+1]+[tuple(q)]+uv[j+1:]
                return idx
    raise AssertionError('Missing shoulder stitch edge')

def sew(g,base,names):
    records,cutloops,offset,keep=prepare(base,names,g)
    roots=root_boundaries(g);cuts=[];reports=[];centers={}
    for root in roots:
        sign=1 if np.mean([g.p[i][0] for i in root])>0 else -1
        end=next(loop for loop in cutloops if np.mean(np.array(loop)[:,0])*sign>0)
        center=np.mean([g.p[i] for i in root],axis=0);ec=np.mean(np.array(end),axis=0)
        centers[sign]=ec
        yr=np.ptp(np.array([g.p[i] for i in root])[:,1])*.5;zr=np.ptp(np.array([g.p[i] for i in root])[:,2])*.5
        def angle_root(i):
            p=g.p[i]-center;return math.atan2(p[2]/zr,p[1]/yr)%(2*math.pi)
        def angle_end(p):return math.atan2(sign*(p[0]-ec[0]),p[1]-ec[1])%(2*math.pi)
        rr=sorted((angle_root(i),i) for i in root);ee=sorted((angle_end(p),p) for p in end)
        # Include every native cut vertex at the shoulder too, then subdivide
        # native boundary edges at the remaining angles. This avoids T junctions.
        for angle,p in ee:
            if min(abs((a-angle+math.pi)%(2*math.pi)-math.pi) for a,i in rr)<1e-7:continue
            j=next((j for j,(a,i) in enumerate(rr) if a>angle),len(rr))-1
            a,ia=rr[j];b,ib=rr[(j+1)%len(rr)]
            distance=(b-a)%(2*math.pi);t=((angle-a)%(2*math.pi))/distance
            idx=insert_root(g,ia,ib,t);rr.append((angle,idx));rr.sort()
        endweights={}
        for mat,poly in records:
            for p,w,uv in poly:
                if abs(p[2]-CUT)<1e-7:endweights[key(p)]=w
        endpoint=[]
        for angle,idx in rr:
            j=next((j for j,(a,p) in enumerate(ee) if a>angle+1e-8),len(ee))-1
            a,pa=ee[j];b,pb=ee[(j+1)%len(ee)]
            t=((angle-a)%(2*math.pi))/((b-a)%(2*math.pi));t=float(np.clip(t,0,1))
            p=np.array(pa)*(1-t)+np.array(pb)*t;w=bounded(endweights[pa]*(1-t)+endweights[pb]*t)
            eid=g.vertex(p);g.w[eid]=w;endpoint.append(eid);cuts.append((pa,pb,t,eid))
        rows=[[i for a,i in rr]]
        for t in (.16,.34,.55,.78,1.):
            row=[]
            for (_,a),b in zip(rr,endpoint):
                if t==1:row.append(b);continue
                p=g.p[a]*(1-t)+g.p[b]*t
                # Gentle sleeve-cap ease; preserve the measured shoulder and
                # native elbow cross-sections rather than inserting cylinders.
                c=center*(1-t)+ec*t;radial=p-c;radial/=max(np.linalg.norm(radial),1e-8)
                p+=radial*.008*math.sin(math.pi*t)
                idx=g.vertex(p);native_w=g.surface.nearest_weights(p)
                w=g.w[a]*(1-t)**2+native_w*(1-(1-t)**2);g.w[idx]=bounded(w);row.append(idx)
            rows.append(row)
        for ri,(a,b) in enumerate(zip(rows,rows[1:])):
            for j in range(len(a)):
                k=(j+1)%len(a);aa=rr[j][0];bb=rr[k][0]+(2*math.pi if k==0 else 0)
                ids=[a[j],b[j],b[k],a[k]]
                g.face(ids,0,[(.34+angle/(2*math.pi)*.22,.67+(g.p[idx][2]-.13)*.45)
                              for idx,angle in zip(ids,(aa,aa,bb,bb))])
        reports.append({'side':sign,'shoulder_stitch_vertices':[i for a,i in rr],
                        'native_forearm_stitch_vertices':endpoint,'rows':len(rows),'cut_height_m':CUT})
    # Insert all new cut points directly into the clipped native face edges.
    for material,poly in records:
        ids=[];uvs=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            p,w,uv=a;q,v,vu=b;ka,kb=key(p),key(q)
            idx=g.vertex(p);g.w[idx]=bounded(w);ids.append(idx);uvs.append(uv)
            extra=[]
            if abs(p[2]-CUT)<1e-7 and abs(q[2]-CUT)<1e-7:
                for ca,cb,t,eid in cuts:
                    if ca==ka and cb==kb:factor=t
                    elif ca==kb and cb==ka:factor=1-t
                    else:continue
                    if 1e-7<factor<1-1e-7:extra.append((factor,eid))
            for t,eid in sorted(set(extra)):
                ids.append(eid);uvs.append(uv*(1-t)+vu*t)
        # Native green sleeves use the coat fabric. Bracers retain their actual
        # original UV charts and materials, including seams around the cuffs.
        if material==1:
            mat=0
            sign=1 if np.mean([g.p[i][0] for i in ids])>0 else -1;ec=centers[sign]
            angles=[]
            for i in ids:
                p=g.p[i];cx=abs(ec[0])+(CUT-p[2])*.50
                angles.append(math.atan2(abs(p[0])-cx,p[1]-ec[1])%(2*math.pi))
            reference=angles[0];angles=[reference+(a-reference+math.pi)%(2*math.pi)-math.pi for a in angles]
            uvs=[(.34+a/(2*math.pi)*.22,.67+(g.p[i][2]-.13)*.45) for a,i in zip(angles,ids)]
        else:mat=offset+material
        if len(ids)>4:
            center=g.vertex(np.mean([g.p[i] for i in ids],axis=0))
            g.w[center]=bounded(np.mean([g.w[i] for i in ids],axis=0));center_uv=np.mean(uvs,axis=0)
            for j,(a,b) in enumerate(zip(ids,ids[1:]+ids[:1])):
                g.face([center,a,b],mat,[center_uv,uvs[j],uvs[(j+1)%len(ids)]])
        else:g.face(ids,mat,uvs)
    # Shoulder insertion created conforming n-gons with collinear stitches.
    # Explicit centroid fans retain those stitches without zero-area ear clips.
    old_faces,old_uv=g.faces,g.uv;g.faces=[];g.uv=[]
    for (mat,ids),uvs in zip(old_faces,old_uv):
        collinear_quad=len(ids)==4 and any(abs(np.cross(np.array(uvs[(i+1)%4])-uvs[i],np.array(uvs[(i+2)%4])-uvs[i]))<1e-11 for i in range(4))
        if len(ids)<=4 and not collinear_quad:g.face(ids,mat,uvs);continue
        center=g.vertex(np.mean([g.p[i] for i in ids],axis=0))
        g.w[center]=bounded(np.mean([g.w[i] for i in ids],axis=0));center_uv=np.mean(uvs,axis=0)
        for j,(a,b) in enumerate(zip(ids,ids[1:]+ids[:1])):
            g.face([center,a,b],mat,[center_uv,uvs[j],uvs[(j+1)%len(ids)]])
    # The cut used to sew in the native forearm is not decorative piping.
    for mat,f in g.faces:
        for a,b in zip(f,f[1:]+f[:1]):
            if min(abs(g.p[i][0]) for i in (a,b))>.19 and max(g.p[i][2] for i in (a,b))<.32:
                g.no_trim.add(tuple(sorted((a,b))))
    return reports,keep
