"""Revision 03: native pose/Blender agreement, horizontal fold, cavities and culling."""
import json
import hashlib
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from rh_redesign_paths import CONCEPT_B_FORM as OUT
REVISION=4 if '--revision' in sys.argv and sys.argv[sys.argv.index('--revision')+1]=='4' else 3
if REVISION==4:
    from rh_redesign_paths import CONCEPT_B_PROFILE as OUT


def phase_at(frame):
    if frame<=25 or frame>=145:return 0
    if frame<73:return (frame-25)/48
    if frame<=97:return 1
    return 1-(frame-97)/48


def door_at(frame):
    return max(0,min(1,(frame-169)/32)) if frame<225 else max(0,1-(frame-225)/32)


def prepare():
    import numpy as np
    import rh_concept_b_form as b
    if REVISION==4:
        import rh_concept_b_profile as profile
        profile.configure()
    _,nodes=b.mesh.read_tree(b.DEST.read_bytes())
    data=json.loads((OUT/'blender_scene.json').read_text())
    names={e['file']:e['name'] for e in data['objects']}
    samples=[];frames=sorted(set([1,*range(25,74),*range(97,146,4),169,185,201,225,241,257]))
    for frame in frames:
        scene=b.evaluate_pose(nodes,phase_at(frame),door_at(frame))
        sample=dict(frame=frame,objects=[])
        for part in dict.fromkeys(g['part'] for g in scene):
            points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene if g['part']==part])
            ids=np.arange(0,len(points),11)
            sample['objects'].append(dict(name=names[part],indices=ids.tolist(),positions=points[ids].tolist()))
        samples.append(sample)
    folder=OUT/'checks';folder.mkdir(exist_ok=True)
    (folder/'native_pose_samples.json').write_text(json.dumps(samples,separators=(',',':')))
    # Validate every track against its actual parent, and the launch->wing seam.
    channels={}
    for script in b.mesh.child(b.mesh.child(nodes[0],'Animation'),'Script').children:
        assert len({j.name for j in script.children})==len(script.children)
        channels[script.name]={}
        for j in script.children:
            name=b.mesh.string(b.mesh.child(j,'Child name').blob)
            parent=b.mesh.string(b.mesh.child(j,'Parent name').blob)
            obj=next(e for e in data['objects'] if e['name']==name)
            assert parent==obj['joint']['parent'],(script.name,name,parent)
            ch=b.mesh.child(j,'Channel');count,interval,kind=b.S.unpack('<IfI',b.mesh.child(ch,'Header').blob)
            raw=b.mesh.child(ch,'Frames').blob
            assert interval==-1 and kind==1 and count>0 and len(raw)==count*8
            keys=np.frombuffer(raw,'<f4').reshape(count,2)
            assert np.isfinite(keys).all() and np.all(np.diff(keys[:,0])>=0)
            channels[script.name][name]=keys
    seam={name:abs(float(keys[-1,1])-float(channels['Sc_extend wing'][name][0,1])) for name,keys in channels['Sc_launch extend'].items()}
    assert max(seam.values())<1e-6
    (OUT/'channel_checks.json').write_text(json.dumps(dict(cmp_sha256=hashlib.sha256(b.DEST.read_bytes()).hexdigest(),launch_to_wing_max_error=max(seam.values()),scripts=len(channels),all_parents_and_frame_sizes_valid=True,sampled_frames=len(samples)),indent=2))
    print('Prepared',len(samples),'native CMP poses; parent bindings and launch continuity pass',flush=True)


def verify():
    import bpy
    from mathutils import Matrix,Vector
    from mathutils.bvhtree import BVHTree
    C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
    digest=hashlib.sha256((OUT/'rh_concept_b_lod0.cmp').read_bytes()).hexdigest()
    assert bpy.context.scene['CMP_sha256']==digest
    assert json.loads((OUT/'channel_checks.json').read_text())['cmp_sha256']==digest
    if REVISION==4:
        expected=json.loads((OUT/'checks.json').read_text())['triangles']
        actual=sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
        assert actual==expected,(actual,expected)
        texture_nodes=[n for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
        assert texture_nodes and all(n.image.packed_file for n in texture_nodes),'Textures must travel inside the blend'
    samples=json.loads((OUT/'checks/native_pose_samples.json').read_text())
    max_error=0;overlap=[];open_positions={};folded_positions={};height_error=0
    def tree(obj):
        return BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],
            [tuple(p.vertices) for p in obj.data.polygons],all_triangles=True,epsilon=0)
    for sample in samples:
        bpy.context.scene.frame_set(sample['frame']);bpy.context.view_layer.update()
        trees={}
        for entry in sample['objects']:
            obj=bpy.data.objects[entry['name']]
            for index,point in zip(entry['indices'],entry['positions']):
                actual=obj.matrix_world@obj.data.vertices[index].co;expected=C@Vector(point)
                max_error=max(max_error,(actual-expected).length)
                assert (actual-expected).length<2e-5,(sample['frame'],entry['name'],index,actual,expected)
            trees[obj.name]=tree(obj)
            if '_wing_' in obj.name:
                points=[obj.matrix_world@v.co for v in obj.data.vertices]
                if sample['frame']==1:open_positions[obj.name]=points
                if sample['frame']==73:folded_positions[obj.name]=points
                for p,q in zip(points,open_positions[obj.name]):height_error=max(height_error,abs(p.z-q.z))
        # Panels must clear the fixed ship, doors, opposite panel and upper arm.
        for side,other_side in (('port','starboard'),('starboard','port')):
            wing=f'Rh_{side}_wing_lod1'
            for other in ('Root','Rh_tail_lod1','Rh_glass_lod1','Rh_port_engine_lod1','Rh_starboard_engine_lod1',
                          'BayDoor01_lod1','BayDoor02_lod1',f'Rh_{other_side}_upperarm',f'Rh_{other_side}_wing_lod1'):
                hits=trees[wing].overlap(trees[other])
                if hits:overlap.append(dict(frame=sample['frame'],panel=wing,other=other,triangle_pairs=len(hits)))
    assert height_error<2e-5,height_error
    travel=[]
    for name,points in open_positions.items():
        # Identify actual outer tips, not a fixed coordinate from the old short
        # paddles (revision 04's long panels extend far beyond that coordinate).
        tip_threshold=max(abs(p.x) for p in points)-.25 if REVISION==4 else 5.9
        far=[i for i,p in enumerate(points) if abs(p.x)>tip_threshold]
        folded=folded_positions[name]
        forward=min(folded[i].y-points[i].y for i in far)
        inward=min(abs(points[i].x)-abs(folded[i].x) for i in far)
        assert forward>2.5 and inward>2,(name,forward,inward)
        travel.append(dict(part=name,min_tip_forward=forward,min_tip_inward=inward))
    # Front-facing ray hits prove there is a visible back wall/floor, not a hidden backface.
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();root=tree(bpy.data.objects['Root'])
    rays=[]
    def cast(label,origin,direction,maximum,axis,expected,tolerance=.025):
        o=C@Vector(origin);d=C@Vector(direction)
        pos,normal,index,distance=root.ray_cast(o,d,maximum)
        assert pos is not None,(label,'missing surface')
        assert normal.dot(d)<-.1,(label,'back-facing surface',normal,d)
        native=C.transposed()@pos
        assert abs(native[axis]-expected)<tolerance,(label,native,expected)
        rays.append(dict(label=label,hit=list(native),front_facing=True))
    for x in (-.65,0,.65):
        for y in (-1.3,-.5,.25):cast('cabin_rear', [x,y,-4.05],[0,0,-1],1.2,2,-4.35)
    for side in (-1,1):
        for y,z,x in ((.15,-5.75,.87),(0,-6.03,.89),(-.30,-6.36,.93)):
            cast('cabin_window_pillar',[side*1.8,y,z],[-side,0,0],1.1,0,side*(x+.025),.055)
    compartment=json.loads((OUT/'checks.json').read_text()).get('compartment',
        dict(x=.735,z0=-.397,z1=1.447,floor=-1.20,top0=1.45,top1=2.30))
    z0,z1=compartment['z0'],compartment['z1']
    cargo_z=[z0+(z1-z0)*t for t in (.15,.5,.85)]
    for x in (-.30,0,.30):
        for z in cargo_z:cast('cargo_floor',[x,compartment['top1']+1,z],[0,-1,0],8,1,compartment['floor'])
    for side in (-1,1):
        for z in cargo_z:cast('cargo_wall',[0,-.5,z],[side,0,0],1,0,side*compartment['x'])
    for z,d in ((z0,-1),(z1,1)):cast('cargo_end',[0,-.5,(z0+z1)/2],[0,0,d],3,2,z)
    result=dict(cmp_sha256=hashlib.sha256((OUT/'rh_concept_b_lod0.cmp').read_bytes()).hexdigest(),frames=len(samples),max_vertex_error=max_error,wing_height_error=height_error,tip_motion=travel,
                panel_intersections=overlap,front_facing_cavity_rays=rays,
                scope='panel vs fixed ship, doors and opposite wing mechanism; mating bearings excluded; no equipment or SUR contacts simulated')
    (OUT/'rig_checks.json').write_text(json.dumps(result,indent=2))
    assert not overlap,overlap[:20]
    print('PASS: CMP and Blender agree; fold is forward/inward; visible cabin and cargo walls; no tested panel intersections',flush=True)


if __name__=='__main__':
    if '--blender-check' in sys.argv:verify()
    else:prepare()
