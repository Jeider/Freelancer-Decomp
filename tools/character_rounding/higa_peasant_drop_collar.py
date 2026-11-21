import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
path = ROOT / 'out/character_rounding/higa/peasant_arms/higa_peasant_arms.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
configure('character_rounding')
ob = bpy.data.objects.get('shoulder collar')
if ob:
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('collar removed')
