"""Adaptive curved contours for three explicitly approved hero bodies (+2000 triangles each)."""
import argparse
from collections import defaultdict, Counter
import copy
import gzip
import json
import numpy as np
import contours as core

OUT = core.OUT.parent/'hero_bodies'
TARGETS = ('li_hatcher_body', 'pl_trent_body', 'pl_male2_journeyman_body')


def region(name, a, b, groups):
    p = (a+b)*.5
    if min(a[1], b[1]) < -.10: return None
    if name == 'li_hatcher_body':
        if min(a[1],b[1])>.40 and .125<abs(p[0])<.225 and max(abs(a[0]),abs(b[0]))<.245:
            return 'vest_upper_edge'
        if min(a[1], b[1]) > .17 and max(abs(a[0]), abs(b[0])) < .245 and 'hatcher_body_2' in groups:
            return 'vest_collar' if p[1] > .43 else 'vest_edge'
        return None
    if min(abs(a[0]), abs(b[0])) > .23 and max(a[1], b[1]) < .18:
        return 'sleeve_end'
    if min(a[1], b[1]) < .145: return None
    if p[1] > .53: return 'collar'
    if abs(p[0]) > .205: return 'sleeve'
    # The open front and lower hem contain nearly coincident cloth layers.
    # Their flat cut is authored; rounding it can expose the hidden lining.
    if min(a[1],b[1]) < .32 or abs(p[0]) < .125: return None
    return 'jacket'


def refine(name, records, fs, groups, profiles, limit):
    original_count = len(records)
    for i, record in enumerate(records): record['support'] = {i}
    bounds = np.array([r['ref'] for r in records])
    lo, hi = bounds.min(0), bounds.max(0)
    native = core.load_json(core.OUT/name/'before.json.gz')
    paths = []
    if name == 'li_hatcher_body':
        # Manually traced outer and inner edges of the native upper collar lip.
        # Corresponding stations preserve its authored thickness and open front.
        native_points = np.array(native['points'])
        traced = [('collar',[708,360,359,358,104,105,106,107,589]),
                  ('collar',[364,363,362,361,113,108,109,110,111])]
        # Shoulder top trim crosses body_1/body_2; following only the vest atlas
        # misses its actual top cap. Trace both lip rails and their mirrored pair.
        for ids in ([59,64,69,78,82],[67,66,68,77,71,72],
                    [317,321,325,334,338],[323,324,326,333,327,329]):
            traced.append(('vest_upper',ids))
        for kind,ids in traced:
            line = native_points[ids]
            stations = np.r_[0,np.cumsum(np.linalg.norm(np.diff(line,axis=0),axis=1))]
            stations /= stations[-1]
            curve = line.copy(); values = stations.copy()
            for _ in range(4):
                curve = np.vstack((curve[0],np.stack((.75*curve[:-1]+.25*curve[1:],.25*curve[:-1]+.75*curve[1:]),axis=1).reshape(-1,3),curve[-1]))
                values = np.r_[values[0],np.stack((.75*values[:-1]+.25*values[1:],.25*values[:-1]+.75*values[1:]),axis=1).ravel(),values[-1]]
            paths.append((kind,line,stations,curve,values))
    cuff_profiles = []
    if name != 'li_hatcher_body':
        for center,axis in profiles:
            delta = bounds-center; along = delta@axis
            radius = np.linalg.norm(delta-np.outer(along,axis),axis=1)
            ring = np.unique(bounds[(abs(along)<.0025)&(radius>.025)&(radius<.09)&(bounds[:,0]*np.sign(center[0])>.23)].round(6),axis=0)
            assert len(ring)>=6, 'Missing accepted sleeve end'
            ring -= np.outer((ring-center)@axis,axis)
            cuff_profiles.append(core.profile_from_ring(ring))
    move_cache = {}
    def move(p):
        key = core.key(p)
        if key in move_cache: return move_cache[key]
        delta = np.zeros(3)
        if name == 'li_hatcher_body' and p[1]>.40:
            contributions=[]
            for kind,line,stations,curve,values in paths:
                if kind=='collar' and not (p[1]>.465 and abs(p[0]-.004084)<.125):continue
                if kind=='vest_upper' and not (.125<abs(p[0])<.225):continue
                edge=np.diff(line,axis=0); t=np.clip(np.einsum('ij,ij->i',p-line[:-1],edge)/(edge*edge).sum(1),0,1)
                nearest=line[:-1]+t[:,None]*edge; distances=np.linalg.norm(nearest-p,axis=1); i=distances.argmin()
                d=distances[i]
                if d>=.025:continue
                u=stations[i]+t[i]*(stations[i+1]-stations[i])
                target=np.array([np.interp(u,values,curve[:,k]) for k in range(3)])
                weight=1-core.smooth(.002,.025,d)
                contributions.append((target-nearest[i],weight))
            if contributions:
                delta=sum(d*w for d,w in contributions)/sum(w for _,w in contributions)*max(w for _,w in contributions)
                if np.linalg.norm(delta)>.004:delta*=.004/np.linalg.norm(delta)
        elif cuff_profiles:
            delta=max((core.profile_delta(p,pr) for pr in cuff_profiles),key=lambda d:np.linalg.norm(d))
        move_cache[key]=delta
        return delta
    for r in records: r['p']=np.clip(r['ref']+move(r['ref']),lo,hi)
    counts = Counter()
    for iteration in range(10):
        remaining = limit-sum(map(len, fs))
        if remaining < 2: break
        edges = defaultdict(list)
        for gi, group in enumerate(fs):
            for tri in group:
                for a,b in zip(tri, tri[1:]+tri[:1]):
                    edge = core.edge_key(records[a], records[b])
                    if edge[0] != edge[1]: edges[edge].append((a,b,gi))
        candidates = []
        for key, pairs in edges.items():
            a,b,_ = pairs[0]; ra,rb = records[a],records[b]
            tag = region(name, ra['ref'], rb['ref'], {core.blob(groups[g],'Material_name').rstrip(b'\0').decode() for _,_,g in pairs})
            if tag is None: continue
            pa,pb = ra['p'],rb['p']; edge = pb-pa; linear = (pa+pb)*.5
            if np.linalg.norm(edge) < .003: continue
            # Interpolate the authored normal field on each side, then share the
            # geometric result across UV/material/normal seams. Do not weld UVs.
            delta = np.zeros(3)
            for x,y,_ in pairs:
                rx,ry = records[x],records[y]
                n0,n1 = rx['n'],ry['n']; v = ry['p']-rx['p']
                if n0@n1 < .15: continue  # hard folds and opposing cap normals
                delta += ((v@n1)*n1-(v@n0)*n0)/8
            delta /= len(pairs)
            # End-plane continuity matters more than rounding a cap into a dome.
            if tag == 'sleeve_end':
                for center,axis in profiles:
                    if np.sign(center[0]) == np.sign(linear[0]) and abs((linear-center)@axis) < .03:
                        delta -= axis*(delta@axis)
            length = np.linalg.norm(delta)
            if length > .003: delta *= .003/length
            ref = (ra['ref']+rb['ref'])*.5
            explicit = tag == 'sleeve_end' or (name == 'li_hatcher_body' and np.linalg.norm(move(ref))>1e-9)
            pos = ref+move(ref) if explicit else linear+delta
            displacement = pos-ref
            if np.linalg.norm(displacement) > .006:
                pos = ref+displacement*(.006/np.linalg.norm(displacement))
            pos = np.clip(pos,lo,hi)
            error = np.linalg.norm(pos-linear)
            if error < .00004: continue  # no density increase on flat cloth
            priority = 5 if tag in ('sleeve_end','vest_upper_edge') else (3 if name=='li_hatcher_body' else 2) if 'collar' in tag else 1
            candidates.append((priority*error,key,pos,tag,len(pairs)))
        selected = {}; budget = min(remaining,700)
        for _,key,pos,tag,cost in sorted(candidates,key=lambda c:-c[0]):
            if cost > budget: continue
            selected[key] = (pos,tag); budget -= cost; counts[tag] += cost
        if not selected: break
        mids = {}
        def midpoint(a,b):
            pair = tuple(sorted((a,b)))
            if pair in mids: return mids[pair]
            ra,rb = records[a],records[b]; pos,tag = selected[core.edge_key(ra,rb)]
            weights = defaultdict(float)
            for record in (ra,rb):
                for bone,w in record['skin'].items(): weights[bone] += .5*w
            weights = dict(sorted(weights.items(),key=lambda x:-x[1])[:4]); total = sum(weights.values())
            i = len(records)
            records.append(dict(ref=(ra['ref']+rb['ref'])*.5,p=pos.copy(),n=core.unit(ra['n']+rb['n']),
                uv=(ra['uv']+rb['uv'])*.5,uv1=(ra['uv1']+rb['uv1'])*.5,
                skin={k:w/total for k,w in weights.items()},support=ra['support']|rb['support'],original=False,tag=tag))
            mids[pair] = i
            return i
        for gi,group in enumerate(fs):
            output = []
            for tri in group:
                a,b,c = tri
                es = [core.edge_key(records[x],records[y]) in selected for x,y in ((a,b),(b,c),(c,a))]
                n = sum(es)
                if n == 0: output.append(tri)
                elif n == 3:
                    ab,bc,ca = midpoint(a,b),midpoint(b,c),midpoint(c,a)
                    output.extend(((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))
                elif n == 1:
                    k = es.index(True); a,b,c = tri[k:]+tri[:k]; m = midpoint(a,b)
                    output.extend(((a,m,c),(m,b,c)))
                else:
                    k = (es.index(False)+1)%3; a,b,c = tri[k:]+tri[:k]
                    ab,bc = midpoint(a,b),midpoint(b,c)
                    output.extend(((ab,b,bc),(a,ab,c),(ab,bc,c)))
            fs[gi] = output
    # Thin folded clothing must not invert. Reduce only a problematic sample and
    # all its geometric seam copies; unrelated accepted vertices stay put.
    flat = np.array([t for g in fs for t in g])
    ref = np.array([r['ref'] for r in records])
    n0 = np.cross(ref[flat[:,1]]-ref[flat[:,0]],ref[flat[:,2]]-ref[flat[:,0]])
    constrained = set()
    for _ in range(20):
        p = np.array([r['p'] for r in records])
        n1 = np.cross(p[flat[:,1]]-p[flat[:,0]],p[flat[:,2]]-p[flat[:,0]])
        bad = (np.einsum('ij,ij->i',n0,n1) <= 0) & (np.linalg.norm(n0,axis=1) > 1e-12)
        if not bad.any(): break
        keys = {core.key(records[i]['ref']) for i in flat[bad].ravel()}
        for i,r in enumerate(records):
            if core.key(r['ref']) in keys:
                r['p'] = (r['p']+r['ref'])*.5; constrained.add(i)
    else: raise ValueError('Could not preserve face orientation')
    moved=sum(int(np.linalg.norm(r['p']-r['ref'])>1e-10) for r in records[:original_count])
    return dict(added_triangles_by_region=dict(counts),orientation_limited_vertices=len(constrained),
                original_vertices_unchanged=original_count-moved,moved_contour_vertices=moved,
                max_curve_offset_m=max(np.linalg.norm(r['p']-r['ref']) for r in records))


def build(name):
    assert name in TARGETS and not core.excluded_name(name)
    folder = OUT/name; folder.mkdir(parents=True,exist_ok=True)
    path = core.GAME/'DATA/CHARACTERS/BODIES'/(name+'.dfm'); live = path.read_bytes()
    accepted = core.OUT.parent/('bracer_starts' if name == 'li_hatcher_body' else 'contours_2k')/name/'report.json'
    assert core.digest(live) == json.loads(accepted.read_text())['output_sha256'], 'Accepted model changed: '+name
    header,roots = core.read_tree(live); root = roots[0]; mesh = core.mesh_of(root)
    (folder/'previous_mesh0.utf.gz').write_bytes(gzip.compress(core.write_tree(header,[mesh]),mtime=0))
    before = core.export(root,folder/'before.json.gz')
    records,groups,fs = core.as_records(root); oldfs = copy.deepcopy(fs); count = sum(map(len,fs))
    profiles = [(r[0],r[1]) for r in core.rims(core.load_json(core.OUT/name/'before.json.gz'))]
    changes = refine(name,records,fs,groups,profiles,count+2000)
    checks = core.validate_local(records,fs,oldfs,before)
    core.write_mesh(mesh,records,groups,fs)
    for record in records: record['p']=record['p'].astype('<f4').astype(float)
    checks=core.validate_local(records,fs,oldfs,before)  # Actual serialized precision.
    output = core.write_tree(header,roots); patch = core.write_tree(header,[mesh])
    (folder/'mesh0.utf.gz').write_bytes(gzip.compress(patch,mtime=0))
    core.export(root,folder/'after.json.gz')
    old = {p:v for p,_,v in core.leaves(live)[1]}; new = {p:v for p,_,v in core.leaves(output)[1]}
    assert all('/MultiLevel/Mesh0/' in p for p in set(old)|set(new) if old.get(p) != new.get(p))
    report = dict(name=name,algorithm_revision=4,source=str(path),previous_sha256=core.digest(live),
        output_sha256=core.digest(output),patch_sha256=core.digest(patch),triangles_before=count,
        triangles_after=sum(map(len,fs)),triangle_limit=count+2000,changes=changes,checks=checks,
        only_mesh0=True,game_animation_validated=False)
    (folder/'report.json').write_text(json.dumps(report,indent=2))
    print(name,count,'->',report['triangles_after'],changes,flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--name',action='append'); args = ap.parse_args()
    for name in args.name or TARGETS: build(name)
    (OUT/'inventory.json').write_text(json.dumps([json.loads(p.read_text()) for p in sorted(OUT.glob('*/report.json'))],indent=2))
