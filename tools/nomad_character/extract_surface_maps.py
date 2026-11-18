"""Extract original packed material data without altering the source blend."""
import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=root/'out/nomad_character/surface';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'out/nomad_character/alien/alien.blend'))
for name,filename in [('base_color','base.jpg'),('normal','normal.png'),('texture_0_roughness.png','roughness.png')]:
    im=bpy.data.images.get(name)
    if im is None:
        candidates=[i for i in bpy.data.images if name in i.name]
        assert len(candidates)==1,(name,[i.name for i in bpy.data.images])
        im=candidates[0]
    assert im.packed_file
    (out/filename).write_bytes(bytes(im.packed_file.data))
print('Extracted original normal, roughness and base maps')
