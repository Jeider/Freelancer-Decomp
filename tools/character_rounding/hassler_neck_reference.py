"""Small offline collar/shoulder studies of the actual native references."""
import gzip,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
from hassler_inspect import studio
configure('character_rounding')
TOP=ROOT/'out/character_rounding/hassler/native_upper'

def main():
    dest=TOP/'source/collar_study';dest.mkdir(parents=True,exist_ok=True)
    for label,path in [('wilham',TOP/'source/wilham.json.gz'),('dietrich',TOP/'source/dietrich/source/dietrich.json.gz')]:
        bpy.ops.wm.read_factory_settings(use_empty=True);configure('character_rounding')
        data=json.loads(gzip.decompress(path.read_bytes()))
        ob=native.native_mesh(data,label,native.collection('Reference'));ob.location.z=.975662
        cam=studio(bpy.context.scene);cam.data.ortho_scale=.68
        d=Vector((.35,1,.18)).normalized();cam.location=Vector((0,0,1.55))+d*4
        cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
        scene=bpy.context.scene;scene.render.resolution_x=800;scene.render.resolution_y=800
        scene.render.filepath=str(dest/(label+'.png'));bpy.ops.render.render(write_still=True)
        print('REFERENCE',label,flush=True)

if __name__=='__main__':main()
