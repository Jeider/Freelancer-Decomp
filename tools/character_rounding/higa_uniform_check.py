import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
path = ROOT / 'out/character_rounding/higa/uniform_scale/higa_uniform.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
configure('character_rounding')
for ob in bpy.data.objects:
    n = len(ob.data.vertices) if ob.type == 'MESH' else '-'
    print(ob.name, ob.type, n, tuple(round(x, 3) for x in ob.location))
