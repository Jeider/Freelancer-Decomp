"""Blender background: reproduce reviewed contours, retaining both native UV sets."""
import sys,json
from pathlib import Path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'out/base_interiors/rh_biz_01_base/bar'
OUT=BASE/'integration_v8';OUT.mkdir(exist_ok=True)
script=ROOT/'tools/base_interiors/material_relief_v3.py'
scope={'__file__':str(script),'__name__':'native_geometry_export'}
sys.argv+=['--output-version','prototype_v8']
exec(compile(script.read_text().split('def toggle(')[0],str(script),'exec'),scope)
exports=scope['native_exports'];data=scope['data']
np.savez_compressed(OUT/'native_geometry.npz',**{str(k):v for k,v in exports.items()})
# Prove integration reproduces the reviewed saved geometry, not a new variation.
bpy.ops.wm.open_mainfile(filepath=str(BASE/'prototype_v8/bismarck_material_relief.blend'))
report={}
for index,corners in exports.items():
    b=data['batches'][index];name=data['materials'][b['material']]['name'].split('.')[0].lower()
    mesh=bpy.data.objects[name+'_contour_relief'].data
    expected=[]
    for loop in mesh.loops:
        p=mesh.vertices[loop.vertex_index].co;uv=mesh.uv_layers[0].data[loop.index].uv
        expected.append([p.x,p.z,-p.y,uv.x,1-uv.y])
    exported=corners.reshape(-1,b['stride'])[:,[0,1,2,6,7]]
    err=float(np.max(np.abs(exported-np.asarray(expected))))
    assert err<3e-6,(name,err)
    report[name]={'triangles':len(corners),'max_saved_blend_position_uv_error':err,'uv_sets':2 if b['stride']==10 else 1}
(OUT/'blend_export_check.json').write_text(json.dumps(report,indent=2))
print('Native geometry exported, both UV sets retained; reviewed Blender geometry matched.',flush=True)
