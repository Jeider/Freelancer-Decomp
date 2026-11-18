"""Local epaulette profile study on the installed extra-LOD character bodies."""
import argparse,copy,gzip,json,shutil,uuid
from collections import defaultdict
from pathlib import Path
import numpy as np
import contours as c

OUT=c.ROOT/'out/character_rounding/epaulettes'
TARGETS={'rh_reichman_body':1,'rh_deidrich_body':0}


def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


def lod_root(root,index):
    out=copy.deepcopy(root);ml=c.child(out,'MultiLevel')
    ml.children=[c.child(ml,f'Mesh{index}')];ml.children[0].name='Mesh0'
    return out


def shoulder(name,p):
    return p[1]>.49 and abs(p[0])>(.14 if name=='rh_reichman_body' else .11)


def audit():
    assert shutil.disk_usage(c.ROOT).free>2*1024**3
    for name,gi in TARGETS.items():
        folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
        src=c.GAME/'DATA/CHARACTERS/BODIES'/f'{name}.dfm';raw=src.read_bytes()
        h,roots=c.read_tree(raw);r=roots[0];ml=c.child(r,'MultiLevel')
        assert c.blob(ml,'Enhanced geometry')==b'\1\0\0\0'
        pins=dict(source=str(src),source_sha256=c.digest(raw),group=gi,triangle_limit=2100,
                  lods={n.name:dict(sha256=c.digest(c.write_tree(h,[n])),triangles=sum(len(c.triangles(g)) for g in c.child(n,'Face_groups').children if g.children))
                        for n in ml.children if n.name.startswith('Mesh')})
        if (folder/'source.json').exists():assert json.loads((folder/'source.json').read_text())==pins,'Source changed'
        dump(folder/'source.json',pins)
        c.export(r,folder/'before.json.gz');c.export(lod_root(r,1),folder/'native.json.gz')
        print('AUDITED',name,[v['triangles'] for v in pins['lods'].values()],flush=True)


class Patch:
    def __init__(self,name,root):
        self.gi=TARGETS[name];rr,gg,ff=c.as_records(lod_root(root,1));self.triangles=[]
        selected=[t for t in ff[self.gi] if all(shoulder(name,rr[i]['p']) for i in t)]
        normals=defaultdict(list);positions={};edges=defaultdict(int)
        for t in selected:
            for i in t:
                k=c.key(rr[i]['p']);positions[k]=rr[i]['p'];normals[k].append(rr[i]['n'])
            for a,b in zip(t,t[1:]+t[:1]):edges[c.edge_key(rr[a],rr[b])]+=1
        boundary=defaultdict(set)
        for (a,b),count in edges.items():
            if count==1:boundary[a].add(b);boundary[b].add(a)
        self.moves={}
        for k,p in positions.items():
            q=p.copy();neighbors=boundary.get(k,set())
            if len(neighbors)==2 and abs(p[0])>.155:
                q=.85*p+.075*sum((positions[n] for n in neighbors),np.zeros(3))
                delta=q-p;q=p+delta*min(1,.0035/max(np.linalg.norm(delta),1e-12))
            self.moves[k]=q
        for t in selected:
            p=np.array([rr[i]['p'] for i in t]);uv=np.array([rr[i]['uv'] for i in t])
            matrix=np.vstack((uv.T,np.ones(3)))
            if abs(np.linalg.det(matrix))<1e-9:continue
            n=np.array([c.unit(np.mean(normals[c.key(rr[i]['p'])],axis=0)) for i in t])
            v=np.array([self.moves[c.key(rr[i]['p'])] for i in t]);control={}
            for a,b in ((0,1),(1,0),(0,2),(2,0),(1,2),(2,1)):
                control[a,b]=(2*v[a]+v[b]-np.dot(v[b]-v[a],n[a])*n[a])/3
            e=np.mean(list(control.values()),axis=0);center=e+.5*(e-v.mean(0))
            self.triangles.append((p,np.linalg.inv(matrix),v,n,control,center))

    def sample(self,p,uv):
        candidates=[]
        for tri in self.triangles:
            w=tri[1]@np.r_[uv,1]
            if w.min()>=-2e-5 and w.max()<=1.00002:
                error=np.linalg.norm(w@tri[0]-p)
                if error<.013:candidates.append((error,w,tri))
        if not candidates:return None
        _,w,tri=min(candidates,key=lambda v:v[0]);w=np.maximum(w,0);w/=w.sum()
        def evaluate(weights):
            v,n,controls,center=tri[2:]
            q=sum((weights[i]**3*v[i] for i in range(3)),np.zeros(3))
            q+=sum((3*weights[a]**2*weights[b]*value for (a,b),value in controls.items()),np.zeros(3))
            return q+6*np.prod(weights)*center
        q=evaluate(w);eps=1e-4
        a=(evaluate(w+np.array([-eps,eps,0]))-evaluate(w-np.array([-eps,eps,0])))/(2*eps)
        b=(evaluate(w+np.array([-eps,0,eps]))-evaluate(w-np.array([-eps,0,eps])))/(2*eps)
        n=c.unit(np.cross(a,b));native=c.unit(w@tri[3])
        if n@native<0:n=-n
        delta=q-w@tri[0];size=np.linalg.norm(delta)
        if size>.009:q=w@tri[0]+delta*.009/size
        return q,n


def refine(name,records,groups,fs,patch,limit):
    gi=TARGETS[name];source_count=len(records)
    selected={i for t in fs[gi] if all(shoulder(name,records[j]['p']) for j in t) for i in t}
    samples={i:patch.sample(records[i]['p'],records[i]['uv']) for i in selected}
    samples={i:v for i,v in samples.items() if v is not None}
    # One position for all UV/material seam copies, including the cloth attachment.
    target=defaultdict(list)
    for i,(p,n) in samples.items():target[c.key(records[i]['p'])].append(p)
    target={k:np.mean(v,axis=0) for k,v in target.items()}
    for i,r in enumerate(records):
        r['support']={i}
        if c.key(r['ref']) in target:r['p']=target[c.key(r['ref'])].copy()
        # Retain the authored normal field and hard boundaries. Per-patch
        # analytic normals would introduce visible triangular shading seams.
    # Reichman's existing local tessellation already uses his full budget.
    # Dietrich gets only samples where the curved gold plate needs them.
    splits=0
    for iteration in range(3):
        budget=limit-sum(map(len,fs))
        if budget<2:break
        edges=defaultdict(list);gold=set()
        for group_id,faces in enumerate(fs):
            for t in faces:
                for a,b in zip(t,t[1:]+t[:1]):
                    k=c.edge_key(records[a],records[b]);edges[k].append((a,b))
                    if group_id==gi and a in selected and b in selected:gold.add(k)
        candidates=[]
        for k in gold:
            pair=next(((a,b) for a,b in edges[k] if a in selected and b in selected),None)
            if pair is None:continue
            a,b=pair;ra,rb=records[a],records[b]
            ref=(ra['ref']+rb['ref'])*.5;uv=(ra['uv']+rb['uv'])*.5;sample=patch.sample(ref,uv)
            if sample is None:continue
            error=np.linalg.norm(sample[0]-(ra['p']+rb['p'])*.5)
            if error<.00022 or np.linalg.norm(ra['ref']-rb['ref'])<.009:continue
            candidates.append((error,k,sample,len(edges[k])))
        wanted={}
        for error,k,sample,cost in sorted(candidates,key=lambda row:-row[0]):
            if cost<=budget:wanted[k]=sample;budget-=cost;splits+=1
        if not wanted:break
        mids={}
        def mid(a,b):
            pair=tuple(sorted((a,b)))
            if pair in mids:return mids[pair]
            ra,rb=records[a],records[b];pos,normal=wanted[c.edge_key(ra,rb)];skin=defaultdict(float)
            for r in (ra,rb):
                for bone,w in r['skin'].items():skin[bone]+=.5*w
            skin=dict(sorted(skin.items(),key=lambda item:-item[1])[:4]);total=sum(skin.values())
            i=len(records);records.append(dict(ref=(ra['ref']+rb['ref'])*.5,p=pos.copy(),
                n=c.unit(ra['n']+rb['n']),
                uv=(ra['uv']+rb['uv'])*.5,uv1=(ra['uv1']+rb['uv1'])*.5,
                skin={k:v/total for k,v in skin.items()},support=ra['support']|rb['support'],original=False))
            if a in selected and b in selected:selected.add(i)
            mids[pair]=i;return i
        for group_id,faces in enumerate(fs):
            result=[]
            for t in faces:
                flags=[c.edge_key(records[a],records[b]) in wanted for a,b in zip(t,t[1:]+t[:1])]
                count=sum(flags);a,b,d=t
                if count==0:result.append(t)
                elif count==3:
                    ab,bd,da=mid(a,b),mid(b,d),mid(d,a)
                    result.extend(((a,ab,da),(ab,b,bd),(da,bd,d),(ab,bd,da)))
                elif count==1:
                    k=flags.index(True);a,b,d=t[k:]+t[:k];m=mid(a,b);result.extend(((a,m,d),(m,b,d)))
                else:
                    k=(flags.index(False)+1)%3;a,b,d=t[k:]+t[:k];ab,bd=mid(a,b),mid(b,d)
                    result.extend(((ab,b,bd),(a,ab,d),(ab,bd,d)))
            fs[group_id]=result
    # Keep the complete UV seam together if a very thin lip limits the movement.
    flat=np.array([t for faces in fs for t in faces]);reference=np.array([r['ref'] for r in records])
    n0=np.cross(reference[flat[:,1]]-reference[flat[:,0]],reference[flat[:,2]]-reference[flat[:,0]])
    constrained=set()
    for iteration in range(20):
        p=np.array([r['p'] for r in records]);n1=np.cross(p[flat[:,1]]-p[flat[:,0]],p[flat[:,2]]-p[flat[:,0]])
        bad=(np.einsum('ij,ij->i',n0,n1)<=0)&(np.linalg.norm(n0,axis=1)>1e-12)
        if not bad.any():break
        keys={c.key(records[i]['ref']) for i in flat[bad].ravel()}
        for i,r in enumerate(records):
            if c.key(r['ref']) in keys:r['p']=(r['p']+r['ref'])*.5;constrained.add(i)
    else:raise ValueError('Could not preserve orientation')
    return dict(original_records=source_count,curve_splits=splits,gold_samples=len(samples),
                orientation_limited_vertices=len(constrained),max_displacement=float(max(np.linalg.norm(r['p']-r['ref']) for r in records)))


def build(name):
    folder=OUT/name;pins=json.loads((folder/'source.json').read_text());raw=Path(pins['source']).read_bytes()
    assert c.digest(raw)==pins['source_sha256'];h,roots=c.read_tree(raw);root=roots[0]
    records,groups,fs=c.as_records(root);oldfs=copy.deepcopy(fs);before=c.load_json(folder/'before.json.gz')
    changes=refine(name,records,groups,fs,Patch(name,root),pins['triangle_limit'])
    for r in records:r['p']=r['p'].astype('<f4').astype(float)
    checks=c.validate_local(records,fs,oldfs,before)
    c.write_mesh(c.mesh_of(root),records,groups,fs)
    output=c.write_tree(h,roots)
    old={p:v for p,_,v in c.leaves(raw)[1]};new={p:v for p,_,v in c.leaves(output)[1]}
    assert all('/MultiLevel/Mesh0/' in p for p in set(old)|set(new) if old.get(p)!=new.get(p))
    c.export(root,folder/'after.json.gz')
    patch=c.write_tree(h,[c.mesh_of(root)])
    (folder/'mesh0.utf.gz').write_bytes(gzip.compress(patch,mtime=0))
    parent_faces=[];offset=0
    for old,updated in zip(oldfs,fs):
        lookup={frozenset(t):offset+i for i,t in enumerate(old)}
        parent_faces.extend(lookup[frozenset().union(*(records[i]['support'] for i in t))] for t in updated)
        offset+=len(old)
    dump(folder/'topology.json',dict(geometry_sha256=c.digest(patch),face_parent_flat=parent_faces))
    dump(folder/'report.json',dict(name=name,source_sha256=pins['source_sha256'],geometry_sha256=c.digest(patch),
        triangles_before=sum(map(len,oldfs)),triangles_after=sum(map(len,fs)),triangle_limit=pins['triangle_limit'],
        changes=changes,checks=checks,lower_lods_and_non_mesh_data_unchanged=True,installed=False))
    print('MODELED',name,sum(map(len,oldfs)),'->',sum(map(len,fs)),changes,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--audit',action='store_true');args=ap.parse_args()
    if args.audit:audit()
    else:
        for name in TARGETS:build(name)
