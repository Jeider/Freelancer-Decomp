"""Run with Python to prepare native-CMP samples, then Blender background to verify them."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rh_redesign_paths import CONCEPT_B_DETAIL as OUT


def prepare():
    import numpy as np
    import rh_concept_b_detail as b
    _,nodes=b.mesh.read_tree(b.DEST.read_bytes())
    names={e['file']:e['name'] for e in json.loads((OUT/'blender_scene.json').read_text())['objects']}
    samples=[]
    for frame in (1,25,37,49,61,73,84,97,109,121,133,145):
        phase=1 if frame<=25 or frame>=145 else 1-(frame-25)/48 if frame<73 else 0 if frame<=97 else (frame-97)/48
        scene=b.evaluate_pose(nodes,phase)
        sample=dict(frame=frame,objects=[])
        for part in dict.fromkeys(g['part'] for g in scene):
            points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene if g['part']==part])
            ids=np.arange(0,len(points),17)
            sample['objects'].append(dict(name=names[part],indices=ids.tolist(),positions=points[ids].tolist()))
        samples.append(sample)
    folder=OUT/'checks';folder.mkdir(exist_ok=True)
    (folder/'native_pose_samples.json').write_text(json.dumps(samples,separators=(',',':')))
    print('Prepared native CMP samples at',len(samples),'animation frames')


def verify():
    import bpy
    from mathutils import Matrix,Vector
    from mathutils.bvhtree import BVHTree
    C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
    samples=json.loads((OUT/'checks/native_pose_samples.json').read_text())
    max_error=0
    overlap=[]
    for sample in samples:
        bpy.context.scene.frame_set(sample['frame'])
        bpy.context.view_layer.update()
        for entry in sample['objects']:
            obj=bpy.data.objects[entry['name']]
            for index,point in zip(entry['indices'],entry['positions']):
                actual=obj.matrix_world@obj.data.vertices[index].co
                expected=C@Vector(point)
                max_error=max(max_error,(actual-expected).length)
                assert (actual-expected).length<2e-5,(sample['frame'],entry['name'],index,actual,expected)
        # Check the moving panel skin against the fixed body, frame, glass and engines.
        # Bearings intentionally meet their parent arm, so those mating parts are excluded.
        trees={}
        for entry in sample['objects']:
            obj=bpy.data.objects[entry['name']]
            vertices=[obj.matrix_world@v.co for v in obj.data.vertices]
            faces=[tuple(p.vertices) for p in obj.data.polygons]
            trees[obj.name]=BVHTree.FromPolygons(vertices,faces,all_triangles=True,epsilon=0)
        for wing in ('Rh_port_wing_lod1','Rh_starboard_wing_lod1'):
            for other in ('Root','Rh_tail_lod1','Rh_glass_lod1','Rh_port_engine_lod1','Rh_starboard_engine_lod1'):
                collisions=trees[wing].overlap(trees[other])
                if collisions:overlap.append(dict(frame=sample['frame'],panel=wing,other=other,triangle_pairs=len(collisions)))
    result=dict(frames=len(samples),max_vertex_error=max_error,panel_fixed_geometry_intersections=overlap,
                scope='panel vs body/frame/glass/engines; excludes intentional bearing contacts and separate equipment')
    (OUT/'rig_checks.json').write_text(json.dumps(result,indent=2))
    assert not overlap,overlap
    print('PASS Blender rig matches native CMP samples; no panel/fixed-body triangle intersections:',result,flush=True)


if __name__=='__main__':
    if '--blender-check' in sys.argv:verify()
    else:prepare()
