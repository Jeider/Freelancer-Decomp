"""Reopen delivered blend and compare actual native CMP poses and asset contents."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rh_concept_b_final_blender import OUT,C

bpy.ops.wm.open_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
scene=bpy.context.scene
native=json.loads((OUT/'native_samples.json').read_text())
checks=json.loads((OUT/'checks.json').read_text())
review=json.loads((OUT/'review_data.json').read_text())
digest=hashlib.sha256((OUT/'rh_concept_b.cmp').read_bytes()).hexdigest()
assert digest==scene['CMP_sha256']==native['cmp_sha256']==checks['cmp_sha256']==review['cmp_sha256']
max_error=0
for sample in native['samples']:
    scene.frame_set(sample['frame']);bpy.context.view_layer.update()
    for entry in sample['objects']:
        obj=bpy.data.objects[entry['name']]
        for index,expected in zip(entry['indices'],entry['positions']):
            error=(obj.matrix_world@obj.data.vertices[index].co-C@Vector(expected)).length
            max_error=max(max_error,error)
            assert error<3e-5,(sample['frame'],entry['name'],error)
counts=[]
for lv in range(3):
    col=bpy.data.collections['LOD0 - near model' if lv==0 else f'LOD{lv} - distance model']
    counts.append(sum(len(o.data.polygons) for o in col.objects if o.type=='MESH'))
    assert col.hide_render==(lv>0) and col.hide_viewport==(lv>0)
assert counts==checks['lods']
assert len(bpy.data.collections['Hardpoints - native local transforms'].objects)==len(review['hardpoints'])
assert len(bpy.data.collections['Damage caps - enable with detached part hidden'].objects)==5
assert len(bpy.data.collections['Debris caps - attached to detached components'].objects)==5
textures=[i for i in bpy.data.images if i.source=='FILE' and i.users and i.name not in ('Render Result','Viewer Node')]
assert textures and all(i.packed_file for i in textures),[i.name for i in textures if not i.packed_file]
motion=json.loads((OUT/'motion_intersections.json').read_text())
assert motion['cmp_sha256']==digest and not motion['wing_intersections'] and not motion['door_intersections']
report=dict(cmp_sha256=digest,blend_sha256=hashlib.sha256((OUT/'rh_concept_b_rigged.blend').read_bytes()).hexdigest(),
            native_sample_frames=len(native['samples']),max_native_position_error=max_error,lod_triangles=counts,
            packed_textures=len(textures),hardpoints=len(review['hardpoints']),damage_caps=10)
(OUT/'blend_checks.json').write_text(json.dumps(report,indent=2))
print('PASS REOPENED BLEND',report,flush=True)
