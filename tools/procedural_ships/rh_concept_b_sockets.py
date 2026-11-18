"""RH B 08: source-width neck, inset panels, swept wings in plain slot sockets.

No roof-tail beam, no new animation keys, no installation or game launch.
"""
import collections
import copy
import json
import shutil
import numpy as np
import rh_concept_b_compact as prev
from rh_redesign_paths import CONCEPT_B_SOCKETS as OUT

prior,volume,old,native,mesh,audit,base=prev.prior,prev.volume,prev.old,prev.native,prev.mesh,prev.audit,prev.base
PANEL,PANEL2,DARK,WEAPON=prev.PANEL,prev.PANEL2,prev.DARK,prev.WEAPON
DEST=OUT/'rh_concept_b_lod0.cmp'
SWEEP=np.deg2rad(25.)
PYLON_AFT=3.15
SOURCE=[]
WING_SEATS={}
COUNTS={}
TAIL_FOOT_Z=6.754108
TAIL_FOOT_TOP=-.094


def append(b,groups):
    for g in groups:b.tris[g['material']].extend(g['corners'])


class Builder(prev.Builder):
    def face(self,points,material=volume.PANEL,uvbox=volume.UV,normal=None,uv=None):
        p=np.asarray(points,float)
        # Lower outer sill bevels use the atlas's long framed strip. Section
        # boundaries keep each placement short enough to retain visible grain.
        if (self.part=='body' and uvbox==volume.UV and p[:,1].max()<=-.79999
                and p[:,1].min()>=-1.15001 and p[:,2].min()>=-.10001
                and np.ptp(p[:,2])>.4 and np.ptp(p[:,0])>.1):
            q,span=prev.chart(p)
            return self.explicit(p,PANEL,(.003,.86,.997,.997),normal,q)
        return super().face(p,material,uvbox,normal,uv)


def native_neck(b):
    # Select the actual narrow core and original cabin-to-neck transition;
    # exclude the old hull cheeks, cargo rim and weapon hardpoint chin.
    ids={PANEL:[*range(7),32,33,*range(128,132),*range(178,185),*range(321,329)],
         PANEL2:[76,77,198,199,280]}
    groups=[dict(g,corners=g['corners'][ids[g['material']]].copy()) for g in SOURCE
            if g['part'].lower().startswith('rh_elite_') and g['material'] in ids]
    z0,z1=-4.80157,-3.4254
    groups=prior.clipped(groups,z0,z1)
    for g in groups:
        p=g['corners'][...,:3];f=np.clip((p[...,2]-z0)/(z1-z0),0,1)
        p[...,2]=-2.10157+f*2.20157
        p[...,1]+=prior.SHIFT[1]
        # Seat its aft roof into our hull without widening the native 1.5 core.
        p[...,1]-=f*(1.6695+prior.SHIFT[1]-2.05)*np.clip((p[...,1]+1.15)/3.411318,0,1)
        p[...,1]=np.where(p[...,1]<-1.04,-1.15,p[...,1])
        n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);ln=np.linalg.norm(n,axis=1)
        keep=ln>1e-8;g['corners']=g['corners'][keep]
        g['corners'][...,3:6]=(n[keep]/ln[keep,None])[:,None,:]
    # The floor must meet the main floor at Z=-.1, not extend underneath it.
    # Only side/roof surfaces enter the hull by .20 for their closed junction.
    for g in groups:
        floor=np.all(np.isclose(g['corners'][...,1],-1.15,atol=1e-5),axis=1)
        clipped=prior.clipped([dict(g,corners=g['corners'][floor])],maximum=-.1)
        retained=[g['corners'][~floor]]+[q['corners'] for q in clipped]
        g['corners']=np.concatenate(retained)
    append(b,groups)
    pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
    core=pts[pts[:,2]>-1.70]
    assert abs(np.ptp(core[:,0])-1.5)<1e-5
    # Closed aft face inside the hull. The front shares the retained cabin rim.
    b.explicit([[-.75,-1.15,.1],[.75,-1.15,.1],[.75,2.05,.1],[-.75,2.05,.1]],PANEL,prior.PLAIN,[0,0,1])
    COUNTS['native_neck_width']=1.5


def sill(b,side,outer,fields):
    x=side*2.05;n=[side,0,0]
    def face(y0,y1,z0,z1,vertical=False):
        p=np.array([[x,y0,z0],[x,y1,z0],[x,y1,z1],[x,y0,z1]])
        uv=np.array([[0,0],[0,1],[1,1],[1,0]])
        if vertical:
            uv=uv[:,::-1];box=(.003,.258,.091,.854)
        else:box=(.003,.86,.997,.997)
        b.explicit(p,PANEL,box,n,uv)
    # Separate longitudinal rails and short uprights. Never map one square
    # over the complete 6.6-unit frame around all three openings.
    breaks=[-.1,.30,2.,2.18,3.9,4.1,5.5,6.5]
    for a,c in zip(breaks,breaks[1:]):
        face(-.80,-.60,a,c);face(-.06,.16,a,c)
    for a,c in ((-.1,.30),(2.,2.18),(3.9,4.1),(5.5,6.5)):face(-.60,-.06,a,c,True)
    for p in fields:
        y0,z0=p.min(0);y1,z1=p.max(0);inner=x-side*.08
        q=np.array([[inner,y0,z0],[inner,y1,z0],[inner,y1,z1],[inner,y0,z1]])
        # One long strapped panel per opening, as in revision 06.
        b.explicit(q,PANEL2,(.003,.005,.166,.499),n,[[0,0],[1,0],[1,1],[0,1]])
        front=q.copy();front[:,0]=x
        for i in range(4):
            j=(i+1)%4;normal=np.r_[0,p.mean(0)-(p[i]+p[j])/2]
            b.explicit([front[i],front[j],q[j],q[i]],DARK,prior.STRIP,normal)


def close_old_wing_notch(scene):
    result=[]
    for side in (-1,1):
        name='_port_engine_' if side<0 else '_starboard_engine_'
        groups=copy.deepcopy([g for g in scene if name in g['part'].lower()])
        dark=next(g for g in groups if g['material']==DARK)
        p=dark['corners'][...,:3];z0,z1=p[...,2].min(),p[...,2].max()
        inner={tuple(v.round(4)) for v in p.reshape(-1,3)}
        removed=0
        for g in groups:
            ts=[]
            for t in g['corners']:
                within=t[:,2].min()>=z0-1e-4 and t[:,2].max()<=z1+1e-4
                belongs=any(tuple(v[:3].round(4)) in inner for v in t)
                if within and belongs:removed+=1
                else:ts.append(t)
            g['corners']=np.array(ts).reshape(-1,3,8)
        assert removed==28,(side,removed)
        edges,positions=prev.boundary_edges(groups)
        front=[e for e in edges if all(abs(k[2]-z0)<1e-4 for k in e)]
        assert len(front)==4,(side,len(front))
        patch=Builder()
        candidates=np.concatenate([g['corners'] for g in groups if g['material']==PANEL])
        for ka,kc in front:
            a,c=positions[ka],positions[kc];aa=a.copy();cc=c.copy();aa[2]=cc[2]=z1
            # Reverse the exposed directed edge to preserve shell winding.
            q=np.array([c,a,aa,cc]);normal=mesh.unit(np.cross(q[1]-q[0],q[2]-q[0]))
            # Continue the original UV plane from a surviving adjacent facet.
            normals=np.cross(candidates[:,1,:3]-candidates[:,0,:3],candidates[:,2,:3]-candidates[:,0,:3])
            length=np.linalg.norm(normals,axis=1);normals/=length[:,None]
            dist=np.max(abs((candidates[:,:,:3]-q[0])@normal),axis=1)
            valid=(dist<2e-4)&((normals@normal)>.999)
            assert valid.any(),('No adjacent engine UV',side,ka,kc)
            ids=np.where(valid)[0];t=candidates[ids[np.argmax(length[ids])]]
            u=mesh.unit(q[1]-q[0]);v=np.cross(normal,u)
            xy=np.column_stack((t[:,:3]@u,t[:,:3]@v,np.ones(3)))
            mapping=np.linalg.solve(xy,t[:,6:8])
            uv=np.column_stack((q@u,q@v,np.ones(4)))@mapping
            patch.explicit(q,PANEL,(0,0,1,1),normal,uv)
        groups=[g for g in groups if len(g['corners'])]
        for g in patch.groups():g['part']=groups[0]['part'];groups.append(g)
        assert len(prev.boundary_edges(groups)[0])==12,'Changed inner engine opening'
        result+=groups
    COUNTS['old_notch_triangles_removed_each']=28
    COUNTS['continuous_shell_triangles_added_each']=8
    return [g for g in scene if '_engine_' not in g['part'].lower()]+result


def sweep_points(p,side):
    pivot=prev.ELBOW*[side,1,1]
    return (np.asarray(p)-pivot)@old.rotation(side*SWEEP).T+pivot


def swept_groups(groups,side):
    for g in groups:
        g['corners'][...,:3]=sweep_points(g['corners'][...,:3],side)
        g['corners'][...,3:6]=g['corners'][...,3:6]@old.rotation(side*SWEEP).T
    return groups


def wing(side):
    saved=old.ROOT_PIVOT,old.ELBOW
    old.ROOT_PIVOT,old.ELBOW=prev.OLD_ROOT,prev.OLD_ELBOW
    try:
        b=Builder();b.part='wing';old.wing_geometry(b,side)
    finally:old.ROOT_PIVOT,old.ELBOW=saved
    groups=prev.shifted(b.groups(),[-side*prev.WING_SHIFT,0,0])
    # Area centroid of the actual upper inset, not the bounding box tip.
    ts=np.concatenate([g['corners'] for g in groups])
    flat=np.all(np.isclose(ts[...,1],old.WING_Y+.065,atol=1e-5),axis=1)
    fs=ts[flat,:,:3];assert len(fs)
    areas=np.linalg.norm(np.cross(fs[:,1]-fs[:,0],fs[:,2]-fs[:,0]),axis=1)
    center=np.average(fs.mean(1),weights=areas,axis=0);center[1]=old.WING_Y+.075
    p=Builder();normal=[0,1,0]
    q=center+np.array([[-.42,0,-.34],[.42,0,-.34],[.42,0,.34],[-.42,0,.34]])
    p.explicit(q,WEAPON,(0,0,1,1),normal,[[0,0],[1,0],[1,1],[0,1]])
    lower=q-[0,.06,0]
    for i in range(4):
        j=(i+1)%4;p.explicit([q[i],q[j],lower[j],lower[i]],DARK,prior.STRIP,(q[i]+q[j])/2-center)
    WING_SEATS[side]=sweep_points(center,side)
    return swept_groups(groups+p.groups(),side)


def socket(side):
    # A single extruded U section: upper/lower lips and a solid inboard back.
    # The wing root enters the .40-high slot. No round hubs, pins or caps.
    yz=np.array([[-1.12,-.34],[.40,-.34],[.40,-.20],[-.84,-.20],
                 [-.84,.20],[.40,.20],[.40,.34],[-1.12,.34]])
    b=Builder();b.part='socket'
    a=np.column_stack((side*(prev.ELBOW[0]+yz[:,0]),old.WING_Y+yz[:,1],np.full(8,7.50)))
    c=a.copy();c[:,2]=8.98
    b.explicit(a,PANEL,prior.PLAIN,[0,0,-1]);b.explicit(c,PANEL,prior.PLAIN,[0,0,1])
    for i in range(8):
        j=(i+1)%8;q=np.array([a[i],a[j],c[j],c[i]])
        normal=np.cross(a[j]-a[i],c[i]-a[i])*side
        # Clockwise section viewed from aft: correct outward orientation.
        _,span=prev.chart(q)
        box=prior.PLAIN if max(span)/min(span)<2.7 else prior.STRIP
        b.explicit(q,DARK if i in (2,3,4) else PANEL,box,normal)
    return swept_groups(b.groups(),side)


def mount(b,side):
    # End exactly at the socket's back plane. The old guessed contour crossed
    # its coplanar upper lip and flickered. The inner edge enters the C-frame.
    ends=sweep_points([[side*(prev.ELBOW[0]-1.12),old.WING_Y,7.50],
                       [side*(prev.ELBOW[0]-1.12),old.WING_Y,8.98]],side)
    poly=np.array([[side*1.20,6.30],[side*1.75,6.40],ends[0,[0,2]],ends[1,[0,2]],[side*1.20,9.10]])
    b.sharp_solid(poly,-.84,-.16,axis=1)


def aft_floor_join(b):
    # Close the real .254-unit gap from the hull end to the lowered tail foot.
    # This is the lower hull junction, not the postponed roof-to-tail beam.
    front=np.array([[-1.55,-1.15,6.49],[1.55,-1.15,6.49],[1.55,-.10,6.49],[-1.55,-.10,6.49]])
    back=np.array([[-1.32,-1.15,6.77],[1.32,-1.15,6.77],[1.32,-.10,6.77],[-1.32,-.10,6.77]])
    # Exact ends avoid coplanar overlap with either existing bottom surface.
    front[:,2]=6.50;back[:,2]=TAIL_FOOT_Z;back[2:,1]=TAIL_FOOT_TOP
    center=np.concatenate((front,back)).mean(0)
    for i in range(4):
        j=(i+1)%4;q=np.array([front[i],front[j],back[j],back[i]])
        b.explicit(q,PANEL,prior.STRIP,q.mean(0)-center)
    b.explicit(front,PANEL,prior.PLAIN,[0,0,-1]);b.explicit(back,PANEL,prior.PLAIN,[0,0,1])


def front_vents(b,ring):
    holes=[]
    shape=np.array([[.96,-.55],[1.37,-.64],[1.48,.95],[1.37,1.36],[1.04,1.44]])
    for side in (-1,1):holes.append(shape*[side,1])
    z=float(ring[0,2]);b.planar(ring[:,:2],holes,2,z,-1)
    for p in holes:
        front=np.column_stack((p,np.full(len(p),z)))
        back=front+[0,0,.16];center=p.mean(0)
        b.explicit(back,DARK,prior.PLAIN,[0,0,-1])
        for i in range(len(p)):
            j=(i+1)%len(p);n=np.r_[center-(p[i]+p[j])/2,0]
            b.explicit([front[i],front[j],back[j],back[i]],DARK,prior.STRIP,n)
    COUNTS['front_recessed_vent_banks']=2
    COUNTS['new_pale_lamellae']=0


def drum(b):
    center=old.point(0,[175,86])
    b.part='tail';b.ring(center,2.01,1.66,-.98,.98,20)
    outer=volume.circle(center[1:],1.66,20,phase=.5)
    # Keep the marked rim width. The full inner disc is .18 behind that rim.
    holes=[]
    for y in (-.88,-.44,0,.44,.88):
        half=np.sqrt(1.53**2-y*y)-.10
        holes.append(center[1:]+np.array([[y-.09,-half],[y+.09,-half],[y+.09,half],[y-.09,half]]))
    b.part='drum_face'
    def clip(poly,axis,sign):
        out=[]
        for a,c in zip(poly,np.roll(poly,-1,axis=0)):
            da=sign*(a[axis]-center[axis+1]);dc=sign*(c[axis]-center[axis+1])
            if da>=-1e-9:out.append(a)
            if (da>=0)!=(dc>=0):out.append(a+(c-a)*da/(da-dc))
        return np.array(out)
    for side in (-1,1):
        quadrants=collections.defaultdict(list)
        approximate=np.array([side*.760,1.3102,4.644])
        hub=None;radius=None
        for g in SOURCE:
            if not g['part'].lower().startswith('rh_elite_') or g['material'] not in (PANEL,PANEL2):continue
            for t in g['corners']:
                if np.all(t[:,0]*side>.54) and np.any(np.linalg.norm(t[:,:3]-approximate,axis=1)<.002):
                    hub=t[np.argmax(t[:,0]*side),1:3]
                    key=tuple(np.sign(t[:,1:3].mean(0)-hub).astype(int))
                    quadrants[key].append((g['material'],t.copy()))
        assert len(quadrants)==4 and all(len(v)==6 for v in quadrants.values())
        points=np.concatenate([t[:,1:3] for ls in quadrants.values() for _,t in ls])
        radii=np.linalg.norm(points-hub,axis=1);radius=radii[radii>.1].mean()
        charts={}
        for key,items in quadrants.items():
            p=np.concatenate([t for _,t in items]);q=np.column_stack((p[:,1:3],np.ones(len(p))))
            matrix=np.linalg.lstsq(q,p[:,6:8],rcond=None)[0]
            assert np.max(abs(q@matrix-p[:,6:8]))<2e-5
            charts[key]=(items[0][0],matrix)
        # Split only at the four native UV seams, not into many radial spokes.
        flat=Builder();flat.part='drum_face';flat.planar(outer,holes,0,side*.80,side)
        for g in flat.groups():
            for t in g['corners']:
                for key,(material,matrix) in charts.items():
                    p=clip(t[:,1:3],0,key[0])
                    if len(p)<3:continue
                    p=clip(p,1,key[1])
                    if len(p)<3:continue
                    source=hub+(p-center[1:])*(radius/1.66)
                    uv=np.column_stack((source,np.ones(len(source))))@matrix
                    b.explicit(np.column_stack((np.full(len(p),side*.80),p)),material,(0,0,1,1),[side,0,0],uv)
        for h in holes:
            a=np.column_stack((np.full(len(h),side*.80),h));c=a-[side*.16,0,0]
            b.explicit(c,DARK,prior.PLAIN,[side,0,0])
            for i in range(len(h)):
                j=(i+1)%len(h);normal=np.r_[0,h.mean(0)-(h[i]+h[j])/2]
                b.explicit([a[i],a[j],c[j],c[i]],DARK,prior.STRIP,normal)
    COUNTS['native_drum_uv_source_triangles_each']=24
    COUNTS['native_drum_face_radius']=1.66
    COUNTS['drum_rim_width']=.35
    COUNTS['drum_face_recess']=.18
    COUNTS['drum_parallel_recesses_each']=5
    b.part='tail'


def design(part,original):
    name=part.lower();side=-1 if '_port_' in name or 'baydoor01' in name else 1
    if name.startswith('rh_elite_'):
        groups=prev.body(original,neck_factory=native_neck,sill_factory=sill,mount_factory=mount,front_factory=front_vents)
        join=Builder();aft_floor_join(join)
        return prev.repair_uv(groups+join.groups())
    if '_wing_' in name:return prev.repair_uv(wing(side))
    if '_upperarm_' in name:return prev.repair_uv(socket(side))
    if '_tail_' in name:
        b=Builder();b.part='tail'
        volume.frame_geometry(b,False,skin_factory=prev.frame_skin,drum_factory=drum)
        return prev.repair_uv(prev.shifted(b.groups(),[0,prev.TAIL_DROP,0]))
    return prev.design(part,original)


def rig(nodes):
    prev.rig(nodes)
    tr,_=audit.transforms(nodes)
    # native.build asks for rig before geometry; derive the same seat targets.
    for side in (-1,1):wing(side)
    for path,node in mesh.walk(nodes):
        if '/hardpoints/' not in path.lower() or not path.lower().endswith('/position'):continue
        part=path.split('/')[2];hp=path.split('/')[-2].lower()
        if '_wing_' not in part.lower():continue
        side=-1 if '_port_' in part.lower() else 1
        rot,t=tr[part.lower()]
        world=rot@np.frombuffer(node.blob,'<f4')+t
        target=WING_SEATS[side] if hp.startswith('hpweapon') else sweep_points(world,side)
        node.blob=np.array(rot.T@(target-t),'<f4').tobytes()


def build():
    global SOURCE,TAIL_FOOT_Z,TAIL_FOOT_TOP
    assert shutil.disk_usage(OUT.parents[3]).free>512*1024**2
    SOURCE,_,_=audit.load(base.ROW)
    prev.SOURCE_SCENE=close_old_wing_notch(SOURCE)
    _,prev.PREVIOUS_NODES=mesh.read_tree(prior.DEST.read_bytes())
    _,before=mesh.read_tree(prev.DEST.read_bytes())
    before_scene=native.evaluate_pose(before,0)
    tail=np.concatenate([g['corners'][...,:3] for g in before_scene if '_tail_' in g['part'].lower()])
    bottom=np.all(np.isclose(tail[...,1],-1.15,atol=1e-5),axis=1)
    TAIL_FOOT_Z=float(tail[bottom,...,2].min())
    tp=tail.reshape(-1,3)
    edge=tp[np.isclose(tp[:,2],TAIL_FOOT_Z,atol=1e-5)&(tp[:,1]<.5)]
    TAIL_FOOT_TOP=float(edge[:,1].max())
    prev.TAIL_DROP=json.loads((prev.OUT/'checks.json').read_text())['tail_translation'][1]
    prior.PIRATE_SCENE=SOURCE
    prev.Builder=Builder;prior.Builder=Builder;volume.Builder=Builder
    prev.PYLON_SHIFT=np.array([.60,.68,PYLON_AFT])
    old.ROOT_PIVOT,old.ELBOW=prev.ROOT,prev.ELBOW;old.ENGINE_X=prev.ENGINE_X
    old.configure();native.OUT,native.DEST=OUT,DEST;native.design,native.rig=design,rig
    native.MESH_PREFIX='rh_b8_';native.COCKPIT_TRANSLATION=prior.SHIFT
    nodes=native.build();native.export(nodes)
    tracks=lambda ns:{p:n.blob for p,n in mesh.walk(ns) if '/animation/' in p.lower() or p.lower().endswith('/cons/rev')}
    assert tracks(nodes)==tracks(before),'Animation data changed'
    scene=native.evaluate_pose(nodes,0);uv=prev.uv_stats(scene)
    assert uv['collapsed']==0 and uv['anisotropy_above_8']==0,uv
    shells={}
    for component in ('port_engine','starboard_engine','port_upperarm','starboard_upperarm'):
        groups=[g for g in scene if '_'+component+'_' in g['part'].lower()]
        assert not prev.boundary_edges(groups)[0]
        edges=collections.defaultdict(list)
        for g in groups:
            for t in g['corners']:
                ks=[tuple(v[:3].round(4)) for v in t]
                for a,c in zip(ks,ks[1:]+ks[:1]):edges[tuple(sorted((a,c)))].append((a,c))
        assert all(len(es)==2 and es[0]==es[1][::-1] for es in edges.values())
        shells[component]='closed, consistent winding'
    transforms,_=audit.transforms(nodes)
    for path,node in mesh.walk(nodes):
        if '/hardpoints/' not in path.lower() or not path.lower().endswith('/position'):continue
        part=path.split('/')[2];hp=path.split('/')[-2].lower()
        if '_wing_' in part.lower() and hp.startswith('hpweapon'):
            side=-1 if '_port_' in part.lower() else 1
            rot,t=transforms[part.lower()]
            assert np.linalg.norm(rot@np.frombuffer(node.blob,'<f4')+t-WING_SEATS[side])<1e-5
    checks=json.loads((OUT/'checks.json').read_text())
    checks.update(revision=8,changes=COUNTS,body_pylon_aft_shift=PYLON_AFT,wing_sweep_degrees=25,
                  wing_weapon_centers={str(k):v.tolist() for k,v in WING_SEATS.items()},
                  neck='native pirate geometry and UV; 1.5 wide core',wing_attachment='plain U slot; no visible circular hinges',
                  closed_engine_and_socket_shells=shells,uv_after=uv,deferred_roof_tail_beam=True,
                  animation='same keys and Rev joints as 07; geometry and weapon locations changed',
                  wing_rig='retained 65/25 degree joints; animation authoring paused',
                  cockpit='same glazing and pilot/camera positions as 07',
                  limitations=['offline LOD0 prototype; not installed','SUR, damage caps, distant LODs and full animation clearance deferred'])
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('READY 08',checks['triangles'],uv,flush=True)


if __name__=='__main__':build()
