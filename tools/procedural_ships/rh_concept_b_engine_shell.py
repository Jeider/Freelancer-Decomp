"""Replace notched RH B engine barrels with complete closed ten-sided shells."""
import collections
import copy
import json
from pathlib import Path
import numpy as np
import rh_concept_b_final as f

PANEL=f.mesh.crc('pir_r_panel01_256')
GRILL=f.mesh.crc('engine_grill01')


def key(v):return tuple(np.round(v,4))


def topology(triangles):
    edges=collections.Counter()
    oriented=collections.Counter()
    for t in triangles:
        ids=[key(v) for v in t[:,:3]]
        for a,b in zip(ids,ids[1:]+ids[:1]):
            edges[tuple(sorted((a,b)))]+=1;oriented[(a,b)]+=1
    return dict(boundary_edges=sum(n==1 for n in edges.values()),
                nonmanifold_edges=sum(n!=2 for n in edges.values()),
                winding_errors=sum(oriented[(a,b)]!=oriented[(b,a)] for a,b in edges))


def ring(points,z,radius):
    candidates=points[(abs(points[:,2]-z)<.00015)&(np.linalg.norm(points[:,:2],axis=1)>radius-.02)]
    if radius<.7:candidates=candidates[np.linalg.norm(candidates[:,:2],axis=1)<.65]
    assert len(candidates)==10,(z,radius,len(candidates))
    angles=np.arctan2(candidates[:,1],candidates[:,0])%(2*np.pi)
    angles[angles>2*np.pi-.001]=0
    return candidates[np.argsort(angles)]


def quad(points,uv,outward):
    out=[]
    for ids in ((0,1,2),(0,2,3)):
        t=np.zeros((3,8));t[:,:3]=points[list(ids)];t[:,6:8]=uv[list(ids)]
        n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])
        if n@outward<0:t=t[[0,2,1]];n=-n
        assert np.linalg.norm(n)>1e-8
        t[:,3:6]=n/np.linalg.norm(n);out.append(t)
    return out


def rebuild(groups):
    a=next(g['corners'] for g in groups if g['material']==PANEL)
    grill=copy.deepcopy(next(g for g in groups if g['material']==GRILL))
    assert set(g['material'] for g in groups)=={PANEL,GRILL}
    # Find the separate twelve-triangle support by vertex connectivity, rather
    # than slicing through the cylinder with an arbitrary height threshold.
    touching=collections.defaultdict(set)
    for i,t in enumerate(a):
        for v in t[:,:3]:touching[key(v)].add(i)
    ids=set(np.flatnonzero(a[...,1].max(1)>.8).tolist());pending=list(ids)
    while pending:
        i=pending.pop()
        for v in a[i,:,:3]:
            for j in touching[key(v)]-ids:ids.add(j);pending.append(j)
    assert len(ids)==12,('Unexpected engine support topology',len(ids))
    support=a[sorted(ids)].copy();body=np.delete(a,sorted(ids),axis=0)
    points=np.unique(np.concatenate((body[...,:3].reshape(-1,3),grill['corners'][...,:3].reshape(-1,3))).round(6),axis=0)
    front=ring(points,-1.3928,.75);rear=ring(points,1.85,.75)
    inner_rear=ring(points,1.85,.5775);inner_front=ring(points,.8033,.5775)
    nose=body[body[...,2].max(1)<-1.3927].copy()
    rim=body[np.all(abs(body[...,2]-1.85)<.0001,axis=1)].copy()
    assert len(nose)==30 and len(rim)==20,(len(nose),len(rim))
    shell=[];inside=[]
    for i in range(10):
        j=(i+1)%10
        q=np.array([front[i],front[j],rear[j],rear[i]])
        # Same narrow engineering strip as the original barrel; a full axial
        # chart per facet keeps the panel pattern at its original physical scale.
        uv=np.array([[.998,.860],[.998,.998],[.002,.998],[.002,.860]])
        radial=q.mean(0);radial[2]=0
        shell+=quad(q,uv,radial)
        q=np.array([inner_front[i],inner_front[j],inner_rear[j],inner_rear[i]])
        width=np.linalg.norm(q[1]-q[0]);length=float((q[2]-q[1])[2])
        uv=np.array([[.32,.860],[.32,.860+width*.30],[.32-length*.30,.860+width*.30],[.32-length*.30,.860]])
        inside+=quad(q,uv,-radial)
    shell=np.array(shell);inside=np.array(inside)
    barrel=np.concatenate((nose,shell,rim,inside,grill['corners']))
    topo=topology(barrel)
    assert not any(topo.values()),topo
    assert not any(topology(support).values()),topology(support)
    stretch=[f.b.prev.distortion(t) for t in shell]
    assert max(stretch)<1.12,max(stretch)
    result=[grill,dict(material=PANEL,corners=np.concatenate((nose,shell,rim,inside,support)),unused=204)]
    return result,dict(before_triangles=sum(len(g['corners']) for g in groups),
        after_triangles=sum(len(g['corners']) for g in result),facets=10,
        support_triangles_preserved=12,nose_triangles_preserved=30,rim_triangles_preserved=20,
        grill_triangles_preserved=len(grill['corners']),topology=topo,
        max_barrel_uv_stretch=max(stretch),outer_radius_xy=[.75,.75])


def rebuild_engines(local):
    reports={}
    for file in local:
        if '_engine_' not in file.lower():continue
        local[file],reports[file]=rebuild(local[file])
    assert len(reports)==2
    return reports


def main():
    import rh_concept_b_hp_prototype as p
    source_hash=f.digest(p.DEST)
    header,nodes=f.mesh.read_tree(p.DEST.read_bytes())
    frozen={k:p.leaves(nodes,k) for k in ('/hardpoints/','/animation/','/cmpnd/')}
    names=f.component_map(nodes);local=f.local_geometry(nodes)
    previous=copy.deepcopy(local)
    reports=rebuild_engines(local)
    f.write_geometry(nodes,[local])
    for file in names:
        ml=f.mesh.child(f.mesh.child(nodes[0],file),'MultiLevel')
        f.mesh.child(ml,'Switch2').blob=np.array([0,100000],'<f4').tobytes()
    raw=f.mesh.write_tree(header,nodes)
    reopened=f.mesh.read_tree(raw)[1];decoded=f.local_geometry(reopened)
    assert all(p.leaves(reopened,k)==v for k,v in frozen.items())
    for file in previous:
        if file in reports:continue
        assert len(previous[file])==len(decoded[file])
        for a,b in zip(previous[file],decoded[file]):
            assert a['material']==b['material'] and np.allclose(a['corners'],b['corners'],atol=1e-6),file
    assert f.digest(p.DEST)==source_hash,'CMP changed during update; preserve user edits'
    p.DEST.write_bytes(raw)
    payload={names[k]:[dict(g,corners=g['corners']) for g in v] for k,v in decoded.items()}
    (p.OUT/'geometry.json').write_text(json.dumps(payload,default=p.serial,separators=(',',':')))
    report=json.loads((p.OUT/'prototype.json').read_text())
    report.update(cmp_sha256=f.digest(p.DEST),hardpoints=f.hp_world(reopened),hardpoint_nodes=p.hardpoint_records(reopened),
        triangles=sum(len(g['corners']) for gs in decoded.values() for g in gs),
        engine_shells=reports,engine_revision_source_sha256=source_hash)
    (p.OUT/'prototype.json').write_text(json.dumps(report,indent=2))
    print('UPDATED PROTOTYPE',report['triangles'],'triangles',reports,flush=True)


if __name__=='__main__':main()
