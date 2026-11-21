"""Matched native BR elite proportion reference, with Hassler's unchanged head."""
import sys,json,gzip
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step15 as views
import hassler_runtime_pose as runtime
configure('character_rounding');TOP=native.OUT/'native_upper';OUT=TOP/'step_19'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
edit=bpy.data.collections['EDIT — native costume upper study'];edit.hide_render=True
d=json.loads(gzip.decompress((TOP/'source/bretonia/source/bretonia.json.gz').read_bytes()));col=native.collection('REFERENCE — native BR elite');ob=native.native_mesh(d,'Native BR elite reference',col);ob.matrix_world=bpy.data.objects['RIG — native Rheinland'].matrix_world.copy()
runtime.cull_materials(col.objects);views.OUT=OUT;scene.cycles.samples=24
views.render(scene,'br_reference',(-.45,1,.20),(0,.02,1.58),.73)
