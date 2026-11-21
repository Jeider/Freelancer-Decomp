"""Validate the exported F01 UV prototype, preserved parts and paired wing UVs."""
import json
import struct
import sys
from pathlib import Path
import numpy as np
import rh_fighter_f01_uv as build

OUT,f=build.OUT,build.f
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant in ('f01_uv_01','f01_uv_02','f01_uv_03')
    OUT=OUT.parent/variant


def wing_check(entry):
    upper=[];lower=[]
    for g in entry['groups']:
        for tri in np.asarray(g['corners'],float):
            n=build.olduv.normal(tri)
            if n[1]>.05 and build.poly_area(tri[:,[0,2]])>1e-8:upper.append((tri,g['material']))
            elif n[1]<-.8 and build.poly_area(tri[:,[0,2]])>1e-6:lower.append((tri,g['material']))
    high=np.array([t[:,[0,2]].max(0) for t,_ in upper]);low=np.array([t[:,[0,2]].min(0) for t,_ in upper])
    maximum=0.;samples=0
    for tri,mat in lower:
        point=tri[:,[0,2]].mean(0);want=tri[:,6:8].mean(0);errors=[]
        ids=np.where(np.all((point>=low-2e-6)&(point<=high+2e-6),axis=1))[0]
        for ix in ids:
            t,material=upper[ix]
            if material!=mat:continue
            bary=build.bary(point[None,:],t[:,[0,2]])[0]
            if min(bary)<-2e-4:continue
            errors.append(float(abs(bary@t[:,6:8]-want).max()))
        assert errors,(entry['name'],point,mat)
        error=min(errors);assert error<.002,(entry['name'],point,error)
        maximum=max(maximum,error);samples+=1
    return dict(name=entry['name'],samples=samples,maximum_uv_error=maximum)


def saved_motion_check(data,review):
    if OUT.name not in ('f01_uv_02','f01_uv_03'):return None
    if OUT.name=='f01_uv_03':import rh_fighter_f01_uv3 as motion_build
    else:import rh_fighter_f01_uv2 as motion_build
    movie=json.loads((OUT/'motion_preview.json').read_text(encoding='utf8'))
    assert movie['blend_sha256']==f.digest(Path(review['blend']))
    assert movie['movie_sha256']==f.digest(OUT/'roof_and_wing_motion.mp4')
    maximum=0.;count=0
    for sample in movie['keyed_pose_samples']:
        frame=sample['frame']
        for name,matrix in sample['game_matrices'].items():
            m=data['motion'][name]
            phase=min((frame-1)/36,(73-frame)/36) if m['kind']=='door' else min((frame-90)/60,(240-frame)/60)
            phase=min(max(phase,0),1)
            r,t=motion_build.motion_transform(m,phase)
            expected=np.eye(4);expected[:3,:3]=r;expected[:3,3]=t
            error=float(abs(expected-np.array(matrix)).max())
            assert error<3e-6,(name,frame,error)
            maximum=max(maximum,error);count+=1
    return dict(keyed_samples=count,max_transform_error=maximum,
        meaning='Reopened Blender keyframes agree with the numerical transforms used for static CMP export')


def receiving_wing_check(data):
    if OUT.name!='f01_uv_03':return None
    import rh_fighter_f01_uv3 as current
    objects={e['name']:e for e in data['objects']}
    cargo=np.concatenate([np.array(g['corners'])[:,:,:3].reshape(-1,3)
        for g in objects['Root']['groups'] if g['material']==current.HOLD])
    # The obsolete long bay must actually be gone, not hidden below a new floor.
    assert cargo[:,2].min()>=-3.900001 and cargo[:,2].max()<=-1.659999
    assert abs(cargo[:,0]).max()<=.740001 and cargo[:,1].min()>=.494999
    hull=max(abs(np.array(g['corners'])[:,:,0]).max() for name,e in objects.items()
        if name in ('Root','Port_carved_flank','Starboard_carved_flank') for g in e['groups'])
    result=[]
    outline=np.array([[1.77,-.80],[5.08,-3.40],[5.36,-3.28],[5.36,-2.19],[2.46,.86],[1.77,1.02]])
    ends=np.roll(outline,-1,axis=0);edge_vectors=ends-outline
    for name,e in objects.items():
        if not name.endswith('_swept_wing'):continue
        r,t=current.motion_transform(data['motion'][name],1)
        lower=[];edge_checks=0;max_edge_error=0
        for g in e['groups']:
            for tri in np.array(g['corners']):
                n=build.olduv.normal(tri)
                area=np.linalg.norm(np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]))/2
                if n[1]<-.8 and area>1e-6:lower.extend((tri[:,:3]@r.T+t)[:,1])
                if g['material']!=current.D or abs(n[1])>.8:continue
                mid=np.array([abs(tri[:,0].mean()),tri[:,2].mean()])
                fractions=np.clip(np.sum((mid-outline)*edge_vectors,axis=1)/np.sum(edge_vectors**2,axis=1),0,1)
                if np.linalg.norm(mid-outline-fractions[:,None]*edge_vectors,axis=1).min()>.045:continue
                transformed=tri[:,:3]@r.T+t
                for a,b in ((0,1),(1,2),(2,0)):
                    # Equal-height points on a level blade's edge must have
                    # equal texture V, regardless of its sweep in plan view.
                    if abs(transformed[a,1]-transformed[b,1])>2e-5:continue
                    if np.linalg.norm(transformed[a]-transformed[b])<.01:continue
                    error=float(abs(tri[a,7]-tri[b,7]));max_edge_error=max(max_edge_error,error)
                    assert error<2e-5,(name,'diagonal edge UV',error)
                    edge_checks+=1
        # Plane heights remain reliable for the subpixel UV triangles whose
        # normals are sensitive to the source float32 position rounding.
        flat_error=float(np.ptp(lower))
        assert flat_error<2e-5,(name,'not horizontal',flat_error)
        warning=np.concatenate([np.array(g['corners'])[:,:,:3].reshape(-1,3)
            for g in e['groups'] if g['material']==current.old.WARNING])@r.T+t
        margin=float(abs(warning[:,0]).min()-hull)
        assert margin>.5,(name,'outer section buried',margin)
        assert edge_checks>0
        result.append(dict(name=name,horizontal_height_range=flat_error,
            edge_parallel_samples=edge_checks,max_edge_v_error=max_edge_error,
            outer_warning_section_hull_clearance=margin))
    return dict(cargo_bounds=[cargo.min(0).tolist(),cargo.max(0).tolist()],wings=result,
        limit='Outer blade geometry checked; clearance of a specific mounted gun awaits the equipment/HP pass')


def main():
    raw=OUT/'geometry.json';data=json.loads(raw.read_text(encoding='utf8'))
    previous=json.loads(Path(data['shape_source']).read_text(encoding='utf8'))
    old={e['name']:e for e in previous['objects']}
    review=json.loads((OUT/'blender_check.json').read_text(encoding='utf8'))
    assert review['geometry_sha256']==f.digest(raw)
    assert review['saved_and_reopened'] and not review['lid_collisions'] and not review['wing_collisions']
    for e in data['objects']:
        if e['name'] in data['preserved_objects']:assert e==old[e['name']],e['name']
    closed={e['name'] for e in data['objects'] if e['authored_closed']}
    for ob in review['objects']:
        if ob['name'] in closed:
            assert ob['nonmanifold_edges']==ob['inconsistent_winding_edges']==0,ob
            assert ob['signed_volume']>0,ob
    mats=f.audit.material_table([build.model.MAT,build.model.ENV])
    zero_uv=[];metal=[]
    for e in data['objects']:
        for g in e['groups']:
            mat=mats[g['material']]
            for t in np.array(g['corners']):
                p=t[:,:3];area=np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))/2
                texarea=build.poly_area(t[:,6:8])
                if mat['texture'] and area>1e-6 and texarea<1e-12:zero_uv.append((e['name'],area))
                if 'metal' in mat['texture'].lower():
                    name=e['name'];assert name in ('Root','Sculpted_roof_shoulders','Port_BayDoor','Starboard_BayDoor'),name
                    if name=='Sculpted_roof_shoulders':assert build.olduv.normal(t)[1]<.8
                    metal.append(name)
    assert not zero_uv,zero_uv[:10]
    limits=[];salts=set()
    for ex in data['exports']:
        path=Path(ex['file']);assert f.digest(path)==ex['sha256']
        assert ex['salt'] not in salts;salts.add(ex['salt'])
        _,nodes=f.mesh.read_tree(path.read_bytes())
        assert not any(n.name.lower() in ('material library','texture library') for n in nodes[0].children)
        actual=f.hp_world(nodes)
        for hp in data['hardpoints']:assert np.allclose(actual[hp['name'].lower()]['position'],hp['position'])
        for name in ex['private_submodels'].values():assert ex['salt'] in name
        libs=set()
        for p,n in f.mesh.walk(nodes):
            if p.endswith('/VMeshData'):
                _,_,groups,indices,fvf,vertices=struct.unpack_from('<II4H',n.blob)
                assert max(vertices,indices)<65536 and fvf==0x112
                libs.add(f.mesh.crc(p.split('/')[-2]));limits.append(dict(file=path.name,vertices=vertices,indices=indices))
        for p,n in f.mesh.walk(nodes):
            if p.lower().endswith('/vmeshref'):assert struct.unpack_from('<I',n.blob,4)[0] in libs
    wings=[wing_check(e) for e in data['objects'] if e['name'].endswith('_swept_wing')]
    motion=saved_motion_check(data,review)
    receiving=receiving_wing_check(data)
    for path,digest in data['sources'].items():assert f.digest(Path(path))==digest,path
    report=dict(status='passed',geometry_sha256=f.digest(raw),blend_sha256=f.digest(Path(review['blend'])),
        preserved_objects=data['preserved_objects'],closed_objects=len(closed),door_phases=31,wing_phases=61,
        intersections=[],seated_carrier_contacts=len(review['intentional_carrier_contacts']),
        wing_uv_checks=wings,material_validation='External native MAT; cargo-only metal family; no significant collapsed UV faces',
        saved_motion_check=motion,
        receiving_wing_check=receiving,
        mesh_limits=limits,exports=data['exports'],installed=False,game_launched=False,
        limits='Offline LOD0 prototype; CMP poses are static. Animation study is in Blender. Full rig/SUR/LODs/damage are not final.')
    build.model.dump(OUT/'validation.json',report)
    print(json.dumps(dict(status='passed',triangles=data['total_triangles'],wings=wings,closed=len(closed),
        max_vertices=max(x['vertices'] for x in limits),max_indices=max(x['indices'] for x in limits)),indent=2))


if __name__=='__main__':main()
