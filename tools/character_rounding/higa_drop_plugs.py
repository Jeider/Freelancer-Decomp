import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
path = ROOT / 'out/character_rounding/higa/peasant_scaled/higa_peasant_scaled.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
configure('character_rounding')
for name in ('shoulder bridge', 'shoulder socket'):
    ob = bpy.data.objects.get(name)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
        print('removed', name)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
