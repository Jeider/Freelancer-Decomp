"""RH B 07: compact original placements, closed engines, straight neck and UVs.

No roof-to-tail beam: the user explicitly postponed it. No animation retiming.
"""
import collections
import copy
import json
import shutil

import numpy as np
import rh_concept_b_attachments as prior
from rh_redesign_paths import CONCEPT_B_COMPACT as OUT

old,native,mesh,audit,base=prior.old,prior.native,prior.mesh,prior.audit,prior.base
volume=prior.previous
PANEL,PANEL2,DARK,WEAPON=prior.PANEL,prior.PANEL2,prior.DARK,prior.WEAPON
DEST=OUT/'rh_concept_b_lod0.cmp'
FLOOR=-1.15
ENGINE_X=1.8205
ROOT=np.array([2.25,-.50,7.30]);ELBOW=np.array([3.05,-.50,7.30])
OLD_ROOT=np.array([2.65,-.50,7.30]);OLD_ELBOW=np.array([3.90,-.50,7.30])
WING_SHIFT=.85
TAIL_DROP=0.
SOURCE_SCENE=[]
PREVIOUS_NODES=[]
ENGINE_TRANSFORMS={}
COUNTS={}
PYLON_SHIFT=np.array([.60,.68,0.])


def chart(points):
    """An orthonormal chart of the actual polygon plane, not largest XYZ spans."""
    p=np.asarray(points,float);edges=np.roll(p,-1,axis=0)-p
    normal=mesh.unit(np.sum(np.cross(p,np.roll(p,-1,axis=0)),axis=0))
    u=mesh.unit(edges[np.argmax(np.linalg.norm(edges,axis=1))]);v=np.cross(normal,u)
    q=np.column_stack((p@u,p@v));span=np.maximum(np.ptp(q,axis=0),1e-8)
    return (q-q.min(0))/span,span


class Builder(prior.Builder):
    def face(self,points,material=volume.PANEL,uvbox=volume.UV,normal=None,uv=None):
        p=np.asarray(points,float)
        if uv is None and self.panel_context is None and uvbox in (volume.UV,volume.RED):
            uv,span=chart(p)
            if max(span)/min(span)>2.7 and material!=old.METAL and uvbox!=volume.RED:
                return self.explicit(p,DARK if material==volume.STRUCT else PANEL,prior.STRIP,normal)
        return super().face(p,material,uvbox,normal,uv)

    def explicit(self,p,material,box,normal=None,uv=None):
        if uv is None and box!=prior.STRIP:uv,_=chart(p)
        return super().explicit(p,material,box,normal,uv)

    def pocket(self,contour,axis,level,depth,sign=1,floor_material=volume.DARK):
        p=np.asarray(contour,float);axes=[i for i in range(3) if i!=axis]
        a=np.zeros((len(p),3));a[:,axis]=level;a[:,axes]=p
        c=a.copy();c[:,axis]-=sign*depth;n=np.eye(3)[axis]*sign
        uv,span=chart(c);long=max(span);short=min(span)
        service=(self.part in ('wing','tail_frame') or (axis==0 and self.part=='body' and p.mean(0)[0]<.2)
                 or (self.part=='tail' and (np.ptp(p,axis=0).max()>2 or axis==1)))
        if service:
            # Two native service columns; longitudinal repeats follow their
            # source UV direction instead of stretching one hatch down a wing.
            if span[0]>span[1]:uv=uv[:,::-1]
            self.explicit(c,PANEL2,(.003,.005,.333,.005+.330*long/short),n,uv)
        else:self.explicit(c,DARK,prior.PLAIN,n,uv)
        for i in range(len(p)):
            j=(i+1)%len(p);inward=np.zeros(3);inward[axes]=p.mean(0)-(p[i]+p[j])/2
            self.explicit([a[i],a[j],c[j],c[i]],DARK,prior.STRIP,inward)


def shifted(groups,delta):
    out=copy.deepcopy(groups)
    for g in out:g['corners'][...,:3]+=delta
    return out


def straight_neck(b):
    # Same cabin perimeter, constant width along Z: no pinched hourglass floor.
    xy=np.array([[-1.420413,-1.741818],[-1.250375,-.793803],[-1.047923,.436188],
                 [-.818666,.580133],[.823100,.584477],[1.047965,.436188],
                 [1.250418,-.793803],[1.420474,-1.741818]])
    xy[:,1]+=prior.SHIFT[1]
    back=xy.copy();back[:,1]=FLOOR+(back[:,1]-FLOOR)*(2.04-FLOOR)/(xy[:,1].max()-FLOOR)
    a=np.column_stack((xy,np.full(8,-2.10157)))
    c=np.column_stack((back,np.full(8,.10)))
    center=np.concatenate((a,c)).mean(0)
    for i in range(8):
        j=(i+1)%8;q=np.array([a[i],a[j],c[j],c[i]])
        uv,span=chart(q)
        if i in (3,7):
            # Roof/floor: width across U, length down the red service panels.
            uv=np.column_stack(((q[:,0]-q[:,0].min())/np.ptp(q[:,0]),(q[:,2]-q[:,2].min())/np.ptp(q[:,2])))
            vspan=.335*np.ptp(q[:,2])/np.ptp(q[:,0])
            b.explicit(q,PANEL2,(.001,.001,.336,.001+vspan),q.mean(0)-center,uv)
        elif min(span)<.4:b.explicit(q,PANEL,prior.STRIP,q.mean(0)-center)
        else:b.explicit(q,PANEL,prior.PLAIN,q.mean(0)-center,uv)
    b.explicit(c,PANEL,prior.PLAIN,[0,0,1])
    COUNTS['straight_neck_triangles']=26


def extract_pylons():
    root=[g for g in SOURCE_SCENE if g['part'].lower().startswith('rh_elite_')]
    ids={PANEL:list(range(288,294)),PANEL2:[78,79,*range(182,190)],WEAPON:[2,3]}
    right=[]
    for g in root:
        if g['material'] in ids:right.append(dict(g,corners=g['corners'][ids[g['material']]].copy()))
    assert sum(len(g['corners']) for g in right)==18
    result=[]
    for side in (-1,1):
        for g in right:
            out=copy.deepcopy(g)
            if side<0:
                source=next(q for q in root if q['material']==g['material'])['corners']
                chosen=[]
                for t in g['corners']:
                    target=t[:,:3]*[-1,1,1]
                    # Match each mirrored face in the original, preserving its
                    # own UV orientation instead of mirroring the right atlas.
                    distances=np.linalg.norm(source[:,:,:3,None]-target.T[None,None,:,:],axis=2)
                    error=distances.min(axis=2).max(axis=1)
                    index=int(np.argmin(error));assert error[index]<.002
                    chosen.append(source[index].copy())
                out['corners']=np.array(chosen)
            out['corners'][...,:3]+=PYLON_SHIFT*[side,1,1]
            result.append(out)
    return result


def body(original,neck_factory=None,sill_factory=None,mount_factory=None,front_factory=None):
    b=Builder()
    groups=volume.body_geometry(b,original,neck_factory=neck_factory or straight_neck,cabin_factory=prior.cabin,
                               include_brace=False,sill_factory=sill_factory,mount_factory=mount_factory,front_factory=front_factory)
    for g in groups:
        p=g['corners'][...,:3]
        main_floor=np.all(np.isclose(p[...,1],FLOOR,atol=1e-6),axis=1)&np.all(p[...,2]>=-.100001,axis=1)
        g['corners']=g['corners'][~main_floor]
    floor=Builder()
    for x0,x1 in ((-1.55,-.80),(.80,1.55)):
        floor.explicit([[x0,FLOOR,-.1],[x1,FLOOR,-.1],[x1,FLOOR,6.5],[x0,FLOOR,6.5]],PANEL,
                       (.001,.859,.999,.998),[0,-1,0],[[0,0],[0,1],[1,1],[1,0]])
    floor.explicit([[-.8,FLOOR,-.1],[.8,FLOOR,-.1],[.8,FLOOR,6.5],[-.8,FLOOR,6.5]],PANEL2,
                   (.001,.001,.336,1.36),[0,-1,0],[[0,0],[1,0],[1,1],[0,1]])
    return [g for g in groups+floor.groups()+extract_pylons() if len(g['corners'])]


def boundary_edges(groups):
    edges=collections.defaultdict(list);positions={}
    for g in groups:
        for t in g['corners']:
            keys=[tuple(v[:3].round(4)) for v in t]
            positions.update(zip(keys,t[:,:3]))
            for a,c in zip(keys,keys[1:]+keys[:1]):edges[tuple(sorted((a,c)))].append((a,c))
    return [v[0] for v in edges.values() if len(v)==1],positions


def closed_engine(side):
    name='_port_engine_' if side<0 else '_starboard_engine_'
    groups=copy.deepcopy([g for g in SOURCE_SCENE if name in g['part'].lower()])
    edges,positions=boundary_edges(groups);assert len(edges)==12
    loop=[edges[0][0]];remaining=list(edges)
    while remaining:
        edge=next(e for e in remaining if e[0]==loop[-1]);remaining.remove(edge);loop.append(edge[1])
    assert loop[-1]==loop[0]
    b=Builder();p=np.array([positions[k] for k in loop[:-1]])[::-1]
    b.explicit(p,PANEL,prior.PLAIN,np.sum(np.cross(p,np.roll(p,-1,axis=0)),axis=0))
    caps=b.groups()
    # The opening turns around the end collar. A single averaged polygon
    # normal can reverse its final axial triangle; orient every fill triangle
    # against the actual source boundary, including that return face.
    open_edges={tuple(sorted(e)):e for e in edges}
    pending=[t for g in caps for t in g['corners']]
    while pending:
        for t in pending:
            keys=[tuple(v[:3].round(4)) for v in t]
            tri_edges=list(zip(keys,keys[1:]+keys[:1]))
            shared=[e for e in tri_edges if tuple(sorted(e)) in open_edges]
            if not shared:continue
            if open_edges[tuple(sorted(shared[0]))]==shared[0]:
                t[:]=t[::-1].copy();t[:,3:6]*=-1
                keys=[tuple(v[:3].round(4)) for v in t];tri_edges=list(zip(keys,keys[1:]+keys[:1]))
            for e in tri_edges:
                key=tuple(sorted(e))
                if key in open_edges:
                    assert open_edges[key]==e[::-1];del open_edges[key]
                else:open_edges[key]=e
            pending.pop(next(i for i,q in enumerate(pending) if q is t))
            break
        else:raise AssertionError('Unattached engine cap triangle')
    assert not open_edges
    groups+=caps
    assert not boundary_edges(groups)[0],'Engine shell remains open'
    pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
    lo,hi=pts.min(0),pts.max(0);center=(lo+hi)/2
    scale=np.array([1.5/(hi[0]-lo[0]),1.5/(hi[1]-lo[1]),(old.ENGINE_Z1-old.ENGINE_Z0)/(hi[2]-lo[2])])
    target=np.array([side*ENGINE_X,old.ENGINE_Y,(old.ENGINE_Z0+old.ENGINE_Z1)/2])
    ENGINE_TRANSFORMS[side]=(center,scale,target)
    for g in groups:
        g['corners'][...,:3]=(g['corners'][...,:3]-center)*scale+target
        n=g['corners'][...,3:6]/scale;n/=np.linalg.norm(n,axis=-1,keepdims=True);g['corners'][...,3:6]=n
    # Compact solid saddle beneath the rear hull/tail. No long outboard strut.
    mount=Builder();mount.beam([side*1.22,-.78,7.55],[side*ENGINE_X,-.96,8.10],.60,.34)
    return groups+mount.groups()


def inset(poly,distance):
    p=np.asarray(poly,float);orientation=np.sign(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))
    lines=[]
    for a,c in zip(p,np.roll(p,-1,axis=0)):
        u=(c-a)/np.linalg.norm(c-a);n=np.array([-u[1],u[0]])*orientation
        lines.append((a+n*distance,u))
    result=[]
    for (a,u),(c,v) in zip(lines[-1:]+lines[:-1],lines):
        t=np.linalg.solve(np.column_stack((u,-v)),c-a)[0];result.append(a+u*t)
    return np.array(result)


def frame_skin(b,p):
    # Five structural runs, five coherent UV islands. The previous nearest-
    # triangle assignment could tear the texture at the frame's miter corners.
    saved=b.part;b.part='tail_frame'
    for i in range(5):
        poly=np.array([p[i],p[i+1],p[10-i],p[11-i]])
        hole=inset(poly,.14)
        for side in (-1,1):
            b.planar(poly,[hole],0,side*1.32,side)
            b.pocket(hole,0,side*1.32,.12,side)
    b.part=saved


def arm(b,side):
    for c,r in ((ROOT,.4),(ELBOW,.34)):
        b.radial(c*[side,1,1],[(-.22,r),(.22,r)],12,axis=1,cap=volume.STRUCT)
    b.beam(ROOT*[side,1,1],ELBOW*[side,1,1],.48,.42)


def distortion(t):
    p=t[:,:3];a=p[1]-p[0];length=np.linalg.norm(a)
    if length<1e-9:return 1.
    u=a/length;c=p[2]-p[0]
    q=np.array([[length,np.dot(c,u)],[0,np.linalg.norm(c-u*np.dot(c,u))]])
    if abs(np.linalg.det(q))<1e-10:return 1.
    sv=np.linalg.svd((t[1:,6:8]-t[0,6:8]).T@np.linalg.inv(q),compute_uv=False)
    return float(sv[0]/max(sv[1],1e-12))


def repair_uv(groups):
    """Repair affected coplanar islands, preserving good source texture seams."""
    for g in groups:
        ts=g['corners'];bad={i for i,t in enumerate(ts) if distortion(t)>8}
        if not bad:continue
        edges=collections.defaultdict(list);keys=[];normals=[]
        for i,t in enumerate(ts):
            ks=[tuple(v[:3].round(5)) for v in t];keys.append(ks)
            normals.append(mesh.unit(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])))
            for a,c in zip(ks,ks[1:]+ks[:1]):edges[tuple(sorted((a,c)))].append(i)
        neighbors=collections.defaultdict(set)
        for edge,indices in edges.items():
            if len(indices)!=2:continue
            i,j=indices
            if np.dot(normals[i],normals[j])<.9999:continue
            continuous=all(np.allclose(ts[i,keys[i].index(k),6:8],ts[j,keys[j].index(k),6:8],atol=1e-5) for k in edge)
            if continuous or (i in bad and j in bad):neighbors[i].add(j);neighbors[j].add(i)
        done=set()
        for start in sorted(bad):
            if start in done:continue
            island={start};queue=[start]
            while queue:
                for j in neighbors[queue.pop()]-island:island.add(j);queue.append(j)
            done.update(island);ids=sorted(island)
            points=ts[ids,:,:3].reshape(-1,3)
            n=mesh.unit(np.sum(np.array(normals)[ids],axis=0))
            candidates=np.concatenate([ts[i,[1,2,0],:3]-ts[i,:,:3] for i in ids])
            u=mesh.unit(candidates[np.argmax(np.linalg.norm(candidates,axis=1))]);v=np.cross(n,u)
            q=np.column_stack((points@u,points@v));span=np.maximum(np.ptp(q,axis=0),1e-8)
            box=prior.GRID if g['material']==PANEL2 else prior.STRIP if span.max()/span.min()>2.7 else prior.PLAIN
            x,y,xx,yy=box;w,h=xx-x,yy-y;ratio=span[0]/span[1]
            width,height=min(w,h*ratio),min(h,w/ratio)
            uv=(q-q.min(0))/span*[width,height]+[x+(w-width)/2,y+(h-height)/2]
            ts[ids,:,6:8]=uv.reshape(len(ids),3,2)
        COUNTS['uv_repaired_triangles']=COUNTS.get('uv_repaired_triangles',0)+len(done)
    return groups


def design(part,original):
    name=part.lower();side=-1 if '_port_' in name or 'baydoor01' in name else 1;b=Builder()
    if name.startswith('rh_elite_'):return repair_uv(body(original))
    if '_engine_' in name:return repair_uv(closed_engine(side))
    if '_tail_' in name:
        b.part='tail';volume.frame_geometry(b,False,skin_factory=frame_skin)
        return repair_uv(shifted(b.groups(),[0,TAIL_DROP,0]))
    if '_upperarm_' in name:arm(b,side)
    elif '_wing_' in name:
        b.part='wing';saved=(old.ROOT_PIVOT,old.ELBOW)
        old.ROOT_PIVOT,old.ELBOW=OLD_ROOT,OLD_ELBOW
        try:old.wing_geometry(b,side);prior.weapon_seat(b,side)
        finally:old.ROOT_PIVOT,old.ELBOW=saved
        return repair_uv(shifted(b.groups(),[-side*WING_SHIFT,0,0]))
    elif name.startswith('baydoor'):old.door_geometry(b,side)
    else:return original
    return repair_uv(b.groups())


def rig(nodes):
    prior.rig(nodes)
    for path,n in mesh.walk(nodes):
        if path.lower().endswith('/cons/fix'):
            blob=bytearray(n.blob)
            for at in range(0,len(blob),176):
                name=mesh.string(blob[at+64:at+128]).lower()
                if '_tail_' in name:np.frombuffer(blob,'<f4',3,at+128)[1]+=TAIL_DROP
            n.blob=bytes(blob)
    transforms,_=audit.transforms(nodes);old_tr,_=audit.transforms(PREVIOUS_NODES)
    old_flat={p:n.blob for p,n in mesh.walk(PREVIOUS_NODES)}
    _,source_nodes=mesh.read_tree(base.SOURCE.read_bytes());source_tr,_=audit.transforms(source_nodes)
    source_flat={p:n.blob for p,n in mesh.walk(source_nodes)}
    for path,n in mesh.walk(nodes):
        if '/hardpoints/' not in path.lower() or not path.lower().endswith('/position'):continue
        part=path.split('/')[2];name=path.split('/')[-2].lower();side=-1 if '_port_' in part.lower() else 1
        rot,t=transforms[part.lower()];target=None
        if '_wing_' in part.lower() and path in old_flat:
            oldr,oldt=old_tr[part.lower()];target=oldr@np.frombuffer(old_flat[path],'<f4')+oldt+[-side*WING_SHIFT,0,0]
        elif part.lower().startswith('rh_elite_') and name in ('hpweapon03','hpweapon04'):
            sr,st=source_tr[part.lower()];target=sr@np.frombuffer(source_flat[path],'<f4')+st
            target+=PYLON_SHIFT*([-1,1,1] if name=='hpweapon03' else [1,1,1])
        if target is not None:n.blob=np.array(rot.T@(target-t),'<f4').tobytes()


def uv_stats(scene):
    collapsed=bad=0;worst=[]
    for g in scene:
        if '_glass_' in g['part'].lower():continue
        for i,t in enumerate(g['corners']):
            p=t[:,:3];uv=t[:,6:8];a=p[1]-p[0];length=np.linalg.norm(a)
            if length<1e-9:continue
            u=a/length;c=p[2]-p[0];q=np.array([[length,np.dot(c,u)],[0,np.linalg.norm(c-u*np.dot(c,u))]])
            if abs(np.linalg.det(q))<1e-10:continue
            sv=np.linalg.svd((uv[1:]-uv[0]).T@np.linalg.inv(q),compute_uv=False)
            ratio=sv[0]/max(sv[1],1e-12)
            if sv[1]<1e-7:collapsed+=1
            if ratio>8:bad+=1;worst.append(dict(part=g['part'],material=int(g['material']),triangle=i,ratio=float(ratio)))
    return dict(collapsed=collapsed,anisotropy_above_8=bad,worst=sorted(worst,key=lambda x:-x['ratio'])[:20])


def build():
    global SOURCE_SCENE,PREVIOUS_NODES,TAIL_DROP
    assert shutil.disk_usage(OUT.parents[3]).free>512*1024**2,'Insufficient disk space'
    SOURCE_SCENE,_,_=audit.load(base.ROW)
    _,PREVIOUS_NODES=mesh.read_tree(prior.DEST.read_bytes())
    previous_scene=native.evaluate_pose(PREVIOUS_NODES,0)
    tail=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in previous_scene if '_tail_' in g['part'].lower()])
    TAIL_DROP=FLOOR-float(tail[:,1].min())
    prior.PIRATE_SCENE=SOURCE_SCENE
    prior.Builder=Builder;volume.Builder=Builder
    old.ROOT_PIVOT,old.ELBOW=ROOT,ELBOW;old.ENGINE_X=ENGINE_X
    old.configure();native.OUT,native.DEST=OUT,DEST;native.design,native.rig=design,rig
    native.MESH_PREFIX='rh_b7_';native.COCKPIT_TRANSLATION=prior.SHIFT
    nodes=native.build();native.export(nodes)
    scene=native.evaluate_pose(nodes,0)
    tracks=lambda ns:{p:n.blob for p,n in mesh.walk(ns) if '/animation/' in p.lower()}
    assert tracks(nodes)==tracks(PREVIOUS_NODES),'Animation tracks changed'
    t=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene if '_tail_' in g['part'].lower()])
    assert abs(t[:,1].min()-FLOOR)<1e-5
    uv_after=uv_stats(scene)
    assert uv_after['collapsed']==0 and uv_after['anisotropy_above_8']==0,uv_after
    checks=json.loads((OUT/'checks.json').read_text())
    checks.update(revision=7,tail_translation=[0,TAIL_DROP,0],tail_floor=float(t[:,1].min()),
                  deferred_roof_tail_beam=True,engine_spacing=2*ENGINE_X,wing_translation_each=WING_SHIFT,
                  wing_root=ROOT.tolist(),wing_elbow=ELBOW.tolist(),native_body_pylon_triangles=36,
                  engine_closed_boundary_edges_before=12,engine_closed_boundary_edges_after=0,
                  neck='constant cabin section width, flat floor, straight side transitions',
                  animation='same channels and keys as 06; only wing/engine/tail attachment positions adjusted',
                  uv_before=uv_stats(previous_scene),uv_after=uv_after,
                  repair_counts=COUNTS,
                  wing_rig='65/25 degree joints retained, shorter .80-unit upperarm',
                  cockpit='same cabin/glass/pilot/camera placement as 06',
                  limitations=['offline prototype; no installation','SUR, damage caps, distant LOD and full movement clearance deferred'])
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('READY 07',checks['triangles'],'tail drop',TAIL_DROP,'UV',checks['uv_after'],flush=True)


if __name__=='__main__':build()
