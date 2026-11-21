"""Close-up each decoded DFM collar with back-face culling."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step15 as views
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_20'
bpy.ops.wm.open_mainfile(filepath=str(TOP/'game/rh_hassler_body.blend'));configure('character_rounding')
scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=16;scene.render.film_transparent=True;views.OUT=OUT
cols=[next(c for c in bpy.data.collections if c.name.startswith(f'GAME LOD{i} ')) for i in range(5)]
for i in (1,2,4):
    for j,col in enumerate(cols):col.hide_viewport=col.hide_render=i!=j
    runtime.cull_materials(cols[i].objects)
    views.render(scene,f'before_lod{i}',(-.45,1,.12),(0,.02,1.58),.73)
