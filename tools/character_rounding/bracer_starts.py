"""Locate raised upper bracer rims, then refine only those local contours."""
import argparse
from collections import defaultdict
import json
import math
import copy
import gzip
from pathlib import Path
import numpy as np
import contours as core
from cuff_ends import rims

ROOT=core.ROOT
BASE=core.OUT
OUT=ROOT/'out/character_rounding/bracer_starts'

# Authored selections after checking the textured body atlas. Values identify
# the proximal cuff row, measured from each native wrist along its local axis.
# Discovery alone also returns ordinary sleeve/elbow rows; those are not edits.
TARGETS={
    'br_darcy_body':.148,'br_female_elite_body':.130,'br_female_guard_body':.148,
    'br_male_elite_body':.138,'br_male_guard_body':.174,
    'li_female_elite_body':.133,'li_female_guard_body':.148,'li_hatcher_body':.148,
    'li_male_elite_body':.206,'li_male_guard_body':.162,
    'li_tilton_body':.171,'li_tilton_body_alt':.171,
    'ku_female_elite_body':.133,'ku_female_guard_body':.132,'ku_male_elite_body':.167,
    'rh_female_elite_body':.148,'rh_female_guard_body':.133,'rh_male_elite_body':.171,
    'rh_reichman_body':.179,'rh_deidrich_body':.167,
    'pl_male1_journeyman_body':.104,'pl_male3_journeyman_body':.104,
    'ku_male_guard_body':None,'rh_male_guard_body':None,'pl_female2_journeyman_body':None,
    'pl_female1_journeyman_body':None,'br_quigly_body':.117,'li_scrote_body':.167,
}


def locate(data, angle=35, alignment=.38, plane_limit=.012):
    p=np.array(data['points']);pi=np.array(data['point_indices']);edges=defaultdict(list)
    points={core.key(v):v for v in p}
    for group in data['groups']:
        for tri in group['faces']:
            v=p[pi[tri]];normal=core.unit(np.cross(v[1]-v[0],v[2]-v[0]))
            for a,b in zip(v,np.roll(v,-1,axis=0)):
                ka,kb=core.key(a),core.key(b)
                if ka!=kb:edges[tuple(sorted((ka,kb)))].append(normal)
    found=[]
    for wrist in rims(data):
        center,axis=wrist[:2];side=int(np.sign(center[0]));graph=defaultdict(set);eligible={}
        for (ka,kb),normals in edges.items():
            a,b=points[ka],points[kb];v=b-a;length=np.linalg.norm(v)
            t=np.array([(a-center)@axis,(b-center)@axis])
            radial=np.array([a-center-axis*t[0],b-center-axis*t[1]])
            if min(a[0]*side,b[0]*side)<.16 or not .045<t.mean()<.30:continue
            if abs(t[1]-t[0])>length*alignment+.001:continue
            if not (.012<np.linalg.norm(radial,axis=1).min() and np.linalg.norm(radial,axis=1).max()<.10):continue
            sharp=angle==0 or len(normals)==1 or any(x@y<math.cos(math.radians(angle)) for i,x in enumerate(normals) for y in normals[i+1:])
            if not sharp:continue
            graph[ka].add(kb);graph[kb].add(ka);eligible[(ka,kb)]=length
        seen=set()
        for start in graph:
            if start in seen:continue
            stack=[start];component=set()
            while stack:
                k=stack.pop()
                if k in component:continue
                component.add(k);stack.extend(graph[k]-component)
            seen|=component
            if not 4<=len(component)<=32:continue
            vertices=np.array([points[k] for k in sorted(component)])
            c=vertices.mean(0);_,_,axes=np.linalg.svd(vertices-c);n=axes[-1]
            if n@axis<0:n=-n
            plane_error=max(abs((vertices-c)@n));u=axes[0];w=np.cross(n,u)
            angles=np.sort(np.arctan2((vertices-c)@w,(vertices-c)@u));gap=max(np.diff(np.r_[angles,angles[0]+2*np.pi]))
            radii=np.linalg.norm((vertices-c)-np.outer((vertices-c)@n,n),axis=1)
            if n@axis<.75 or plane_error>plane_limit or gap>2.05 or radii.min()<.018 or radii.max()>.085:continue
            edges_in=[e for e in eligible if e[0] in component and e[1] in component]
            found.append(dict(side=side,center=c.tolist(),axis=n.tolist(),points=vertices.tolist(),
                              edges=[[list(a),list(b)] for a,b in edges_in],
                              radius_min=float(radii.min()),radius_max=float(radii.max()),
                              plane_error_m=float(plane_error),along_wrist_m=float((c-center)@axis)))
    return found


def plane_rings(data):
    p=np.array(data['points']);pi=np.array(data['point_indices']);points={core.key(v):v for v in p}
    graph=defaultdict(set)
    for group in data['groups']:
        for tri in group['faces']:
            for a,b in zip(tri,tri[1:]+tri[:1]):
                ka,kb=core.key(p[pi[a]]),core.key(p[pi[b]])
                graph[ka].add(kb);graph[kb].add(ka)
    output=[]
    for wrist in rims(data):
        center,axis=wrist[:2];side=int(np.sign(center[0]))
        nodes={k for k,v in points.items() if v[0]*side>.17 and .055<(v-center)@axis<.275
               and np.linalg.norm(v-center-axis*((v-center)@axis))<.12}
        done=set()
        for a in sorted(nodes):
            neighbours=sorted(graph[a]&nodes)
            for j,b in enumerate(neighbours):
                for c in neighbours[j+1:]:
                    n=core.unit(np.cross(points[b]-points[a],points[c]-points[a]))
                    if abs(n@axis)<.8:continue
                    if n@axis<0:n=-n
                    selected={k for k in nodes if abs((points[k]-points[a])@n)<.002}
                    if not 4<=len(selected)<=20:continue
                    # Require a connected circumference, not points from another sleeve row.
                    comp=set();stack=[a]
                    while stack:
                        k=stack.pop()
                        if k in comp:continue
                        comp.add(k);stack.extend((graph[k]&selected)-comp)
                    token=tuple(sorted(comp))
                    if token in done or len(comp)<4:continue
                    done.add(token);v=np.array([points[k] for k in token]);cc=v.mean(0)
                    _,_,axes=np.linalg.svd(v-cc);nn=axes[-1]
                    if nn@axis<0:nn=-nn
                    u=axes[0];w=np.cross(nn,u);xy=np.column_stack(((v-cc)@u,(v-cc)@w))
                    ang=np.sort(np.arctan2(xy[:,1],xy[:,0]));gap=max(np.diff(np.r_[ang,ang[0]+2*np.pi]));rad=np.linalg.norm(xy,axis=1)
                    if gap>1.9 or rad.min()<.018 or rad.max()>.085 or nn@axis<.75:continue
                    output.append(dict(side=side,center=cc.tolist(),axis=nn.tolist(),points=v.tolist(),edges=[],
                        radius_min=float(rad.min()),radius_max=float(rad.max()),plane_error_m=float(max(abs((v-cc)@nn))),along_wrist_m=float((cc-center)@axis)))
    return output


def audit():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for entry in json.loads((BASE/'inventory.json').read_text()):
        name=entry['name']
        if core.excluded_name(name):continue
        data=core.load_json(BASE/name/'before.json.gz')
        found=locate(data)+locate(data,20,.65,.018)+locate(data,0,.5,.02)+plane_rings(data)
        unique=[]
        for r in found:
            same=next((s for s in unique if s['side']==r['side'] and abs(s['along_wrist_m']-r['along_wrist_m'])<.015),None)
            if same:
                if len(r['points'])>len(same['points']):same.update(r)
            else:unique.append(r)
        found=sorted(unique,key=lambda x:(x['side'],x['along_wrist_m']))
        records.append(dict(name=name,triangles=entry['triangles_after'],rims=found))
        if found:print(name,[(v['side'],round(v['along_wrist_m'],3),len(v['points'])) for v in found],flush=True)
    (OUT/'audit.json').write_text(json.dumps(records,indent=2))
    print('Audited',len(records),'models; candidates',sum(bool(r['rims']) for r in records),flush=True)


def profiles_for(name,records):
    native=core.load_json(BASE/name/'before.json.gz');p=np.array(native['points']);pi=native['point_indices']
    lookup=defaultdict(list)
    for i,j in enumerate(pi):lookup[core.key(p[j])].append(i)
    candidates=next(r['rims'] for r in json.loads((OUT/'audit.json').read_text()) if r['name']==name)
    result=[]
    for side in (-1,1):
        if name=='pl_female2_journeyman_body' and side<0:continue  # the raised silver bracer is asymmetric
        if name in ('ku_male_guard_body','rh_male_guard_body','pl_female1_journeyman_body'):
            # Nonplanar, slanted upper rims: use the endpoints of the long
            # forearm walls. A planar-ring detector correctly rejects them.
            wrist=next(w for w in rims(native) if np.sign(w[0][0])==side);cen,ax=wrist[:2];ends=set()
            for group in native['groups']:
                for tri in group['faces']:
                    for a,b in zip(tri,tri[1:]+tri[:1]):
                        a,b=p[pi[a]],p[pi[b]]
                        if min(a[0]*side,b[0]*side)<.17:continue
                        if (a-cen)@ax>(b-cen)@ax:a,b=b,a
                        if (a-cen)@ax<.05 and .085<(b-cen)@ax<.28:ends.add(core.key(b))
            ring={'points':sorted(ends)}
        elif name=='pl_female2_journeyman_body':
            sets=[]
            for suffix in ('_3','_4'):
                group=next(g for g in native['groups'] if g['name'].endswith(suffix))
                sets.append({core.key(p[pi[i]]) for tri in group['faces'] for i in tri if p[pi[i],0]*side>.17 and .05<p[pi[i],1]<.25})
            inner=sets[0]&sets[1];assert len(inner)>=5
            ring={'points':[q for q in sets[1] if min(np.linalg.norm(np.array(q)-a) for a in inner)<.016]}
        else:
            ring=min((r for r in candidates if r['side']==side),key=lambda r:abs(r['along_wrist_m']-TARGETS[name]))
            assert abs(ring['along_wrist_m']-TARGETS[name])<.025,(name,side)
        # First logical vertices retain native indices in the accepted 2k mesh.
        v=[records[lookup[core.key(q)][0]].get('shape_ref',records[lookup[core.key(q)][0]]['ref']) for q in ring['points']]
        profile=core.profile_from_ring(v);profile['side']=side
        if name=='br_male_elite_body':profile.update(cap_plane=.025,cap_alignment=.5)
        if name in ('li_scrote_body','br_quigly_body','rh_male_guard_body','pl_female2_journeyman_body'):
            profile.update(cap_plane=.030,cap_alignment=.4)
        result.append(profile)
    return result


def shift(p,profile):
    delta=p-profile['center'];axis=profile['axis'];t=delta@axis
    if p[0]*profile['side']<.17 or abs(t)>.050:return np.zeros(3)
    x,y=delta@profile['u'],delta@profile['w'];radius=np.hypot(x,y)
    if not .012<radius<.095:return np.zeros(3)
    direction=np.array([x,y])/radius;native=np.inf
    for a,b in zip(profile['polygon'],np.roll(profile['polygon'],-1,axis=0)):
        edge=b-a;den=direction[0]*edge[1]-direction[1]*edge[0]
        if abs(den)<1e-10:continue
        dist=(a[0]*edge[1]-a[1]*edge[0])/den
        f=((direction*dist-a)@edge)/max(edge@edge,1e-12)
        if dist>0 and -1e-6<=f<=1+1e-6:native=min(native,dist)
    target=np.interp(np.arctan2(y,x),profile['angle'],profile['radius'],period=2*np.pi)
    ratio=np.clip(target/native,.70,1) if np.isfinite(native) else 1
    fade=1-core.smooth(.008,.050,abs(t))
    # One radial scale for outer and inset lip prevents inconsistent clamping.
    return (ratio-1)*fade*(x*profile['u']+y*profile['w'])


def cap_faces(records,fs,profiles):
    result={}
    for gi,group in enumerate(fs):
        for fi,tri in enumerate(group):
            v=np.array([records[i].get('shape_ref',records[i]['ref']) for i in tri]);side=-1 if v[:,0].mean()<0 else 1
            pr=next((pr for pr in profiles if pr['side']==side),None)
            if pr is None:continue
            if min(v[:,0]*pr['side'])<.17:continue
            off=v-pr['center'];along=off@pr['axis'];rad=np.linalg.norm(off-np.outer(along,pr['axis']),axis=1)
            normal=core.unit(np.cross(v[1]-v[0],v[2]-v[0]))
            if max(abs(along))<pr.get('cap_plane',.016) and rad.min()>.018 and rad.max()<.09 and abs(normal@pr['axis'])>pr.get('cap_alignment',.75):
                result[(gi,fi)]=pr['side']
    return result


def remesh_caps(records,fs,profiles):
    selected=cap_faces(records,fs,profiles);changed=set();removed=0;added=0
    for gi,group in enumerate(fs):
        output=[t for fi,t in enumerate(group) if (gi,fi) not in selected]
        for side in (-1,1):
            cap=[t for fi,t in enumerate(group) if selected.get((gi,fi))==side]
            if not cap:continue
            pr=next(pr for pr in profiles if pr['side']==side);edges=defaultdict(list);lookup={}
            for tri in cap:
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    ka,kb=core.key(records[a]['shape_ref']),core.key(records[b]['shape_ref'])
                    lookup[ka]=a;lookup[kb]=b
                    if ka!=kb:edges[tuple(sorted((ka,kb)))].append((a,b))
            graph=defaultdict(set)
            for (a,b),pairs in edges.items():
                if len(pairs)==1:graph[a].add(b);graph[b].add(a)
            loops=[];seen=set()
            for start in graph:
                if start in seen:continue
                comp=set();stack=[start]
                while stack:
                    k=stack.pop()
                    if k in comp:continue
                    comp.add(k);stack.extend(graph[k]-comp)
                seen|=comp
                if any(len(graph[k])!=2 for k in comp):continue
                loop=[start];prev=None;cur=start
                while True:
                    nxt=next(k for k in graph[cur] if k!=prev)
                    if nxt==start:break
                    loop.append(nxt);prev,cur=cur,nxt
                loops.append([lookup[k] for k in loop])
            if len(loops)!=2:
                output.extend(cap);continue
            def radius(loop):return np.mean([np.linalg.norm(records[i]['shape_ref']-pr['center']) for i in loop])
            inner,outer=sorted(loops,key=radius)
            # Different sample spacing on a thin lip can put an inner sample
            # outside a chord of the rounded outer ring. Keep a small positive
            # thickness, moving every seam copy of that inner sample together.
            outerxy=np.array([[(records[i]['p']-pr['center'])@pr['u'],(records[i]['p']-pr['center'])@pr['w']] for i in outer])
            corrections={}
            for i in inner:
                d=records[i]['p']-pr['center'];xy=np.array([d@pr['u'],d@pr['w']]);rr=np.linalg.norm(xy)
                if rr<1e-8:continue
                direction=xy/rr;nearest=np.inf
                for a,b in zip(outerxy,np.roll(outerxy,-1,axis=0)):
                    edge=b-a;den=direction[0]*edge[1]-direction[1]*edge[0]
                    if abs(den)<1e-12:continue
                    distance=(a[0]*edge[1]-a[1]*edge[0])/den
                    f=((distance*direction-a)@edge)/max(edge@edge,1e-12)
                    if distance>0 and -1e-6<=f<=1+1e-6:nearest=min(nearest,distance)
                change=max(0,rr-nearest+.0004)
                if 0<change<.004:
                    corrections[core.key(records[i]['ref'])]=-change*(direction[0]*pr['u']+direction[1]*pr['w'])
            for r in records:
                if core.key(r['ref']) in corrections:r['p']=r['p']+corrections[core.key(r['ref'])]
            def angle(i):
                d=records[i]['shape_ref']-pr['center'];return float(np.arctan2(d@pr['w'],d@pr['u'])%(2*np.pi))
            # Dynamic programming triangulates the thin annulus with positive
            # projected area. Angular zippering alone can cross a very narrow,
            # non-concentric lip. Preserve the actual boundary traversal.
            def orient(loop):
                area=sum(np.cross(records[a]['p']-pr['center'],records[b]['p']-pr['center'])@pr['axis'] for a,b in zip(loop,loop[1:]+loop[:1]))
                return loop if area>0 else list(reversed(loop))
            inner,outer=orient(inner),orient(outer)
            _,si,so=min((np.linalg.norm(records[a]['p']-records[b]['p']),i,j) for i,a in enumerate(inner) for j,b in enumerate(outer))
            inner=inner[si:]+inner[:si];outer=outer[so:]+outer[:so];ni,no=len(inner),len(outer)
            costs={(0,0):0.};parents={}
            for i in range(ni+1):
                for j in range(no+1):
                    if (i,j) not in costs:continue
                    for ii,jj,t in ([(i+1,j,(inner[i%ni],outer[j%no],inner[(i+1)%ni]))] if i<ni else [])+([(i,j+1,(inner[i%ni],outer[j%no],outer[(j+1)%no]))] if j<no else []):
                        p0,p1,p2=[records[k]['p'] for k in t];area=np.cross(p1-p0,p2-p0)@pr['axis']
                        if area<=1e-12:continue
                        quality=(np.dot(p1-p0,p1-p0)+np.dot(p2-p1,p2-p1)+np.dot(p0-p2,p0-p2))/area
                        cost=costs[i,j]+quality
                        if cost<costs.get((ii,jj),np.inf):costs[ii,jj]=cost;parents[ii,jj]=((i,j),t)
            if (ni,no) not in costs:output.extend(cap);continue
            new=[];at=(ni,no)
            while at!=(0,0):at,t=parents[at];new.append(t)
            new.reverse()
            sign=np.sign(sum(np.cross(records[t[1]]['shape_ref']-records[t[0]]['shape_ref'],records[t[2]]['shape_ref']-records[t[0]]['shape_ref'])@pr['axis'] for t in cap))
            handed=np.sign(sum(np.dot(np.cross(records[t[1]]['shape_ref']-records[t[0]]['shape_ref'],records[t[2]]['shape_ref']-records[t[0]]['shape_ref']),sum((records[i]['n'] for i in t),np.zeros(3))) for t in cap))
            duplicates={}
            def area(loop):
                xy=np.array([[(records[i]['p']-pr['center'])@pr['u'],(records[i]['p']-pr['center'])@pr['w']] for i in loop]);nxt=np.roll(xy,-1,axis=0)
                return abs(float(np.sum(xy[:,0]*nxt[:,1]-xy[:,1]*nxt[:,0])))*.5
            triangle_area=sum(abs(np.cross(records[t[1]]['p']-records[t[0]]['p'],records[t[2]]['p']-records[t[0]]['p'])@pr['axis'])*.5 for t in new)
            if abs(triangle_area-(area(outer)-area(inner)))>=1e-7:
                # Deeply slanted or cut-away cuff: retain its authored surface.
                # The orientation guard below limits the local displacement.
                output.extend(cap);continue
            for t in new:
                p=np.array([records[i]['p'] for i in t]);cross=np.cross(p[1]-p[0],p[2]-p[0])
                if cross@pr['axis']*sign<0:t=(t[0],t[2],t[1])
                out=[]
                for i in t:
                    if i not in duplicates:
                        r=dict(records[i]);r['n']=pr['axis']*sign*handed;r['cap_side']=side
                        duplicates[i]=len(records);records.append(r)
                    out.append(duplicates[i])
                output.append(tuple(out));changed.add(tuple(out))
            removed+=len(cap);added+=len(new)
        fs[gi]=output
    return changed,removed,added


def refine(records,fs,profiles):
    original_count=len(records);old_count=sum(map(len,fs));used={-1:0,1:0};cache={}
    def move(p,shape=None):
        if shape is None:shape=p
        k=(tuple(p),tuple(shape))
        if k not in cache:
            profile=next((pr for pr in profiles if pr['side']==(-1 if p[0]<0 else 1)),None)
            if profile is None:return np.zeros(3)
            t=abs((shape-profile['center'])@profile['axis'])
            fade=1-core.smooth(.018,.050,t)
            cache[k]=shift(shape,profile)+(shape-p)*fade if p[0]*profile['side']>.17 else np.zeros(3)
        return cache[k]
    for i,r in enumerate(records):
        r.setdefault('shape_ref',r['ref']);r['support']={i};r['p']=r['ref']+move(r['ref'],r['shape_ref'])
    for iteration in range(3):
        edges=defaultdict(list);cap_edges=defaultdict(int);caps=cap_faces(records,fs,profiles)
        for gi,group in enumerate(fs):
            for fi,tri in enumerate(group):
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    ek=core.edge_key(records[a],records[b])
                    if ek[0]!=ek[1]:
                        edges[ek].append((a,b))
                        if (gi,fi) in caps:cap_edges[ek]+=1
        candidates=[]
        for ek,pairs in edges.items():
            if cap_edges[ek]==len(pairs):continue  # spend samples on contours, not cap diagonals
            if caps and iteration<2 and not 0<cap_edges[ek]<len(pairs):continue
            a,b=pairs[0];ra,rb=records[a],records[b];ref=(ra['ref']+rb['ref'])/2
            if min(abs(ra['ref'][0]),abs(rb['ref'][0]))<.17:continue
            side=1 if ref[0]>0 else -1;pr=next((pr for pr in profiles if pr['side']==side),None)
            if pr is None:continue
            if min(ra['ref'][0]*side,rb['ref'][0]*side)<.17:continue
            t=abs((ref-pr['center'])@pr['axis'])
            if t>.030:continue
            off=ref-pr['center'];radial=off-pr['axis']*(off@pr['axis'])
            if np.linalg.norm(radial)>.095:continue
            shape=(ra['shape_ref']+rb['shape_ref'])/2
            pos=ref+move(ref,shape);error=np.linalg.norm(pos-(ra['p']+rb['p'])/2)
            length=np.linalg.norm(ra['ref']-rb['ref'])
            if error<.00008 or length<.005:continue
            priority=error*(1+4*(1-core.smooth(.005,.030,t)))
            if 0<cap_edges[ek]<len(pairs):priority*=50
            candidates.append((priority,ek,pos,len(pairs),side))
        selected={}
        for _,ek,pos,cost,side in sorted(candidates,key=lambda x:-x[0]):
            if used[side]+cost>50:continue
            selected[ek]=pos;used[side]+=cost
        if not selected:break
        mids={}
        def midpoint(a,b):
            ik=tuple(sorted((a,b)))
            if ik in mids:return mids[ik]
            ra,rb=records[a],records[b];weights=defaultdict(float)
            for r in (ra,rb):
                for bone,w in r['skin'].items():weights[bone]+=.5*w
            weights=dict(sorted(weights.items(),key=lambda x:-x[1])[:4]);total=sum(weights.values())
            i=len(records);records.append(dict(ref=(ra['ref']+rb['ref'])/2,p=selected[core.edge_key(ra,rb)].copy(),
                n=core.unit(ra['n']+rb['n']),uv=(ra['uv']+rb['uv'])/2,uv1=(ra['uv1']+rb['uv1'])/2,
                skin={k:v/total for k,v in weights.items()},support=ra['support']|rb['support'],original=False,shape_ref=(ra['shape_ref']+rb['shape_ref'])/2))
            mids[ik]=i;return i
        for gi,group in enumerate(fs):
            output=[]
            for tri in group:
                a,b,c=tri;es=[core.edge_key(records[x],records[y]) in selected for x,y in ((a,b),(b,c),(c,a))];n=sum(es)
                if n==0:output.append(tri)
                elif n==3:
                    ab=midpoint(a,b);bc=midpoint(b,c);ca=midpoint(c,a)
                    output.extend(((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))
                elif n==1:
                    k=es.index(True);a,b,c=tri[k:]+tri[:k];m=midpoint(a,b);output.extend(((a,m,c),(m,b,c)))
                else:
                    k=(es.index(False)+1)%3;a,b,c=tri[k:]+tri[:k];ab=midpoint(a,b);bc=midpoint(b,c)
                    output.extend(((ab,b,bc),(a,ab,c),(ab,bc,c)))
            fs[gi]=output
    cap_tris,removed,added=remesh_caps(records,fs,profiles)
    allfaces=np.array([t for g in fs for t in g if t not in cap_tris]);ref=np.array([r['ref'] for r in records]);desired=np.array([r['p'] for r in records])
    orient_ref=np.array([r['shape_ref'] for r in records])
    normal0=np.cross(orient_ref[allfaces[:,1]]-orient_ref[allfaces[:,0]],orient_ref[allfaces[:,2]]-orient_ref[allfaces[:,0]])
    # A shared strength keeps thin nested rim loops coherent if a native cap is
    # nearly degenerate. Never independently displace UV/normal seam copies.
    strength=1.
    for _ in range(12):
        p=ref+(desired-ref)*strength;n=np.cross(p[allfaces[:,1]]-p[allfaces[:,0]],p[allfaces[:,2]]-p[allfaces[:,0]])
        if not np.any((np.einsum('ij,ij->i',normal0,n)<=0)&(np.linalg.norm(normal0,axis=1)>1e-12)):break
        strength*=.5
    else:raise ValueError('Cannot preserve orientation')
    for r,pos in zip(records,p):r['p']=pos
    assert sum(map(len,fs))-old_count==sum(used.values())+added-removed<=100
    assert all(np.array_equal(r['p'],r['ref']) for r in records[:original_count] if np.linalg.norm(move(r['ref'],r['shape_ref']))==0)
    return dict(extra_triangles=sum(map(len,fs))-old_count,split_triangles_by_side=used,strength=strength,cap_triangles_removed=removed,cap_triangles_added=added,
                moved_vertices=int(sum(np.linalg.norm(r['p']-r['ref'])>1e-10 for r in records[:original_count])))


def build(name):
    folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
    live=(core.GAME/'DATA/CHARACTERS/BODIES'/(name+'.dfm')).read_bytes()
    previous=json.loads((BASE/name/'report.json').read_text());assert core.digest(live)==previous['output_sha256'],'Live model changed: '+name
    header,roots=core.read_tree(live);root=roots[0];mesh=core.mesh_of(root)
    (folder/'previous_mesh0.utf.gz').write_bytes(gzip.compress(core.write_tree(header,[mesh]),mtime=0))
    before=core.export(root,folder/'before.json.gz');records,groups,fs=core.as_records(root);oldfs=copy.deepcopy(fs)
    validation_before=before
    if name=='li_hatcher_body':
        # Recover exact source parameters for the already tessellated upper lip.
        # Its earlier per-vertex fold protection left an uneven cap; applying
        # another displacement to that cap compounds the defect.
        native=core.read_tree(core.original(name)[1])[1][0]
        rr,gg,ff=core.as_records(native);data=core.load_json(BASE/name/'before.json.gz');pp,belt=core.features(name,data,rr)
        core.refine(name,rr,ff,pp,belt,2000)
        assert ff==fs and len(rr)==len(records),'Accepted topology changed'
        assert all(np.max(abs(r['p'].astype('<f4')-old['p']))<1e-7 for r,old in zip(rr,records)),'Accepted shape changed'
        for r,s in zip(records,rr):r['shape_ref']=s['ref'].copy()
        validation_before=copy.deepcopy(before);validation_before['points']=[r['shape_ref'].tolist() for r in records]
    profiles=profiles_for(name,records);changes=refine(records,fs,profiles)
    cap_tris={t for g in fs for t in g if all('cap_side' in records[i] for i in t)}
    checks=core.validate_local(records,[[t for t in g if t not in cap_tris] for g in fs],oldfs,validation_before)
    checks['remeshed_cap_triangles']=len(cap_tris)
    core.write_mesh(mesh,records,groups,fs);output=core.write_tree(header,roots)
    patch=core.write_tree(header,[mesh]);(folder/'mesh0.utf.gz').write_bytes(gzip.compress(patch,mtime=0))
    core.export(root,folder/'after.json.gz')
    old={p:v for p,_,v in core.leaves(live)[1]};new={p:v for p,_,v in core.leaves(output)[1]}
    assert all('/MultiLevel/Mesh0/' in p for p in set(old)|set(new) if old.get(p)!=new.get(p))
    report=dict(name=name,algorithm_revision=1,previous_sha256=core.digest(live),output_sha256=core.digest(output),
        patch_sha256=core.digest(patch),triangles_before=sum(map(len,oldfs)),triangles_after=sum(map(len,fs)),
        triangle_limit=sum(map(len,oldfs))+100,changes=changes,checks=checks,only_mesh0=True,
        game_animation_validated=False,profiles=[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in pr.items()} for pr in profiles])
    (folder/'report.json').write_text(json.dumps(report,indent=2));print(name,report['triangles_before'],'->',report['triangles_after'],changes,flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--audit',action='store_true');parser.add_argument('--name',action='append');args=parser.parse_args()
    if args.audit:audit()
    else:
        for name in args.name or TARGETS:build(name)
        (OUT/'inventory.json').write_text(json.dumps([json.loads(p.read_text()) for p in sorted(OUT.glob('*/report.json'))],indent=2))
