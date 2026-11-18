"""Prepare photo-atlas LODs from the approved near mesh. No game writes."""
import copy
import json
import numpy as np
import rh_concept_b_v2 as v
f=v.f;OUT=v.OUT/'lod_refinement';SOURCE=v.DEST


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,default=v.hp.serial,separators=(',',':')),encoding='utf8')


def body_shell(shift):
    b=f.b.Builder();b.part='body'
    # The authored stepped hull, with technological recesses filled. Never
    # convexify the neck, shoulder overhang and lower sill into a single wedge.
    stations=[(-.1,2.05),(2.135,2.94),(2.135,3.136),(4.627,3.60),(6.50,.85)]
    rings=[]
    for z,top in stations:
        lip=min(2.06,top-.30)
        half=[[1.12,top],[1.78,lip],[2.02,lip],[2.02,lip-.18],
              [1.65,lip-.18],[1.65,.16],[2.05,.16],[2.05,-.80],[1.55,-1.15]]
        p=np.array(half+[[-x,y] for x,y in half[::-1]])
        rings.append(np.column_stack((p,np.full(len(p),z))))
    for a,c in zip(rings,rings[1:]):
        for i in range(len(a)):
            if i==len(a)-1 and a[0,2]<2.725 and c[0,2]>4.525:
                # Keep the animated cargo doors functional: the roof is not a
                # painted lid across the entire opening.
                xs=(-1.12,-.74,.74,1.12);zs=(a[0,2],2.725,4.525,c[0,2])
                def point(x,z):
                    y=a[0,1]+(c[0,1]-a[0,1])*(z-a[0,2])/(c[0,2]-a[0,2])
                    return [x,y,z]
                for xi in range(3):
                    for zi in range(3):
                        if xi==1 and zi==1:continue
                        q=[point(xs[xi],zs[zi]),point(xs[xi+1],zs[zi]),point(xs[xi+1],zs[zi+1]),point(xs[xi],zs[zi+1])]
                        b.face(q,v.PANEL,(0,0,1,1),[0,1,0])
                continue
            j=(i+1)%len(a);q=np.array([a[i],a[j],c[j],c[i]])
            n=np.cross(q[1]-q[0],q[2]-q[0])
            if np.linalg.norm(n)<1e-9:continue
            # This contour runs clockwise viewed from aft.
            edge=a[j,:2]-a[i,:2];normal=np.r_[-edge[1],edge[0],0.]
            if abs(c[0,2]-a[0,2])<1e-8:normal=np.array([0,0,-1])
            b.face(q,v.PANEL,(0,0,1,1),normal)
    b.face(rings[0],v.PANEL,(0,0,1,1),[0,0,-1])
    b.face(rings[-1],v.PANEL,(0,0,1,1),[0,0,1])
    return f.base.world(b.groups(),np.eye(3),shift)


def main():
    OUT.mkdir(exist_ok=True)
    snapshot=OUT/'before.cmp'
    if not snapshot.exists():snapshot.write_bytes(SOURCE.read_bytes())
    assert f.digest(snapshot)==f.digest(SOURCE),'Main prototype changed; do not overwrite user work'
    nodes=f.mesh.read_tree(snapshot.read_bytes())[1];names=f.component_map(nodes);local=f.local_geometry(nodes)
    shift=np.array(json.loads((v.OUT/'build.json').read_text())['center_shift_native'])
    drop=json.loads((f.OUT.parent/'revision_07/checks.json').read_text())['tail_translation'][1]
    center=f.b.old.point(0,[175,86])+np.array([0,drop,0])+shift
    records=[]
    for file,gs in local.items():
        name=names[file]
        if name=='Root':
            split={'body':[],'frame':[],'drum':[]}
            for g in gs:
                by={key:[] for key in split}
                for t in g['corners']:
                    p=t[:,:3];q=p-shift;radius=np.linalg.norm(p[:,1:]-center[1:],axis=1)
                    if abs(p[:,0]).max()<=1.041 and radius.max()<2.017:region='drum'
                    elif q[:,2].min()>6.77-1e-4 or (q[:,1].max()>3.9 and q[:,2].min()>6.2) or (q[:,2].min()>6.50+1e-4 and q[:,1].max()<.3):region='frame'
                    else:region='body'
                    by[region].append(t)
                for key,ts in by.items():
                    if ts:split[key].append(dict(g,corners=np.array(ts)))
            for region,groups in split.items():records.append(dict(id=region,file=file,name=name,groups=groups))
        else:records.append(dict(id=name,file=file,name=name,groups=gs))
    body=next(e for e in records if e['id']=='body')
    front=f.clip_groups(body['groups'],2,-.10001+shift[2],False)
    coarse_body=body_shell(shift)
    # Keep the original side weapon platforms rather than swelling the hull to
    # their width. Photographs retain their mount pattern without extra rivets.
    for g in body['groups']:
        keep=np.any(abs(g['corners'][...,0])>2.051,axis=1)
        if keep.any():coarse_body.append(dict(g,corners=g['corners'][keep]))
    # Rebuild frame and drum at the actual near-model offset (the old coarse
    # proxy had omitted the -0.8610515 tail translation).
    pixels=[[214,16],[148,16],[95,48],[95,124],[123,153],[207,153],
            [207,133],[140,133],[116,112],[116,59],[154,36],[214,36]]
    poly=f.b.old.yz(pixels);poly[:,0]+=drop;frame=[]
    for bound,greater in ((f.TAIL_CUT,False),(f.TAIL_TOP,True)):
        frame+=v.solid_frame_polygon(v.clip_polygon(poly,0,bound,greater),shift)
    # Keep the continuous lower junction and structural wing supports.
    oldframe=next(e for e in records if e['id']=='frame')
    for g in oldframe['groups']:
        q=g['corners'][...,:3]-shift
        keep=(q[...,1].max(1)<.3)&(q[...,2].max(1)<9.11)&np.any(abs(q[...,0])>1.321,axis=1)
        if keep.any():frame.append(dict(g,corners=g['corners'][keep]))
    for p0,p1 in (([175,49],[175,35]),([175,122],[175,135]),([139,86],[110,86])):
        b=f.b.Builder();b.part='tail';b.beam(f.b.old.point(0,p0),f.b.old.point(0,p1),.4,.48)
        frame+=f.base.world(b.groups(),np.eye(3),shift+[0,drop,0])
    angle=(np.arange(16)+.5)*2*np.pi/16
    yz=center[1:]+2.01*np.column_stack((np.cos(angle),np.sin(angle)))
    points=np.concatenate([np.column_stack((np.full(16,x),yz)) for x in (-.98,.98)])
    drum=[v.hull_group(points)]
    b=f.b.volume.Builder();b.part='drum_face'
    b.ring(center,2.01,1.66,-.98,.98,20)
    angle=(np.arange(20)+.5)*2*np.pi/20
    yz=center[1:]+1.66*np.column_stack((np.cos(angle),np.sin(angle)))
    for sign in (-1,1):
        b.face(np.column_stack((np.full(20,sign*.80),yz)),v.PANEL,(0,0,1,1),[sign,0,0])
    mid_drum=b.groups()
    old_proxy=json.loads((v.OUT/'wire_pieces.json').read_text())['Root'][:1]
    # The former convex neck swallowed the shoulders and became a wide wedge.
    # Its actual source transition is only 60 triangles and preserves the notch.
    old_proxy+=f.clip_groups(front,2,-2.1015+shift[2],True)
    interior=[g for g in body['groups'] if g['material'] in {
        key for key,m in f.audit.material_table([f.SHARED_MAT]).items() if 'metal' in m['name'].lower()}]
    solid_parts={}
    for e in records:
        if not any(k in e['id'] for k in ('_engine_','_wing_','upperarm')):continue
        points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in e['groups']])
        if '_engine_' in e['id']:
            solid_parts[e['id']]=[v.hull_group(points[points[:,1]<.751])]
            # Retain the separate original engine support, already a simple box.
            for g in e['groups']:
                mask=g['corners'][...,1].max(1)>.8
                if mask.any():solid_parts[e['id']].append(dict(g,corners=g['corners'][mask]))
        else:solid_parts[e['id']]=[v.hull_group(points)]
    _,original=f.mesh.read_tree(v.ORIGINAL.read_bytes());onames=f.component_map(original)
    originals={onames[file]:file for file in onames}
    glasses=[]
    for level in (1,2):
        og=f.local_geometry(original,level)
        glasses.append(og[originals['Rh_glass_lod1']])
    materials=f.audit.material_table([f.SHARED_MAT]);meta={}
    for key,m in materials.items():
        if key not in {g['material'] for e in records for g in e['groups']}:continue
        path=None
        if m['image'] is not None:
            path=m['name']+'.png';m['image'].save(OUT/path)
        meta[str(key)]=dict(name=m['name'],image=path,colour=m['colour'].tolist())
    transforms,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    auxiliaries=[]
    for e in records:
        if e['name'].startswith('BayDoor') or '_glass_' in e['name']:
            auxiliaries+=f.base.world(e['groups'],*transforms[e['file'].lower()])
    dump('input.json',dict(source_sha256=f.digest(snapshot),records=records,materials=meta,auxiliaries=auxiliaries,
        coarse=dict(body=coarse_body,front=front,front_solid=old_proxy,frame=frame,drum=drum,mid_drum=mid_drum),glass=glasses,
        tail_drop=drop,shift=shift,drum_center=center,bay_interior=interior,solid_parts=solid_parts))
    dump('sources.json',dict(near_cmp=str(snapshot),near_sha256=f.digest(snapshot),
        original_cmp=str(v.ORIGINAL),original_sha256=f.digest(v.ORIGINAL),
        shared_mat=str(f.SHARED_MAT),shared_mat_sha256=f.digest(f.SHARED_MAT),
        original_lod_atlas='pir_Rh_elite_lod, 256x256; original LOD counts 1514 / 710 / 296',
        method='Blender orthographic photography of current LOD0, isolated parts, six directions'))
    print('PROJECTION INPUT',[(e['id'],sum(len(g['corners']) for g in e['groups'])) for e in records],flush=True)


if __name__=='__main__':main()
