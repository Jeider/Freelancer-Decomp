"""Inspect the actual Scrote vest volume and its native waist profile."""
import sys,json,gzip
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
from hassler_inspect import studio
configure('character_rounding')
TOP=ROOT/'out/character_rounding/hassler/native_upper'

def main():
    data=json.loads(gzip.decompress((TOP/'source/scrote/source/scrote.json.gz').read_bytes()))
    dest=TOP/'source/scrote/study';dest.mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True);configure('character_rounding')
    ob=native.native_mesh(data,'Actual li_scrote_body',native.collection('Native reference'));ob.location.z=.975662
    cam=studio(bpy.context.scene);cam.data.ortho_scale=1.0
    scene=bpy.context.scene;scene.render.resolution_x=800;scene.render.resolution_y=800
    for label,direction in [('front',(.3,1,.08)),('side',(1,0,.02)),('back',(.3,-1,.08))]:
        d=Vector(direction).normalized();cam.location=Vector((0,0,1.36))+d*4
        cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(dest/(label+'.png'));bpy.ops.render.render(write_still=True)
    points=np.array(data['points']);stats={}
    for height in (.10,.15,.20,.25,.30,.35,.40,.45,.50):
        rows=points[(abs(points[:,1]-height)<.025)&(abs(points[:,0])<.18)]
        if len(rows):stats[str(height)]={'front_native_z':float(rows[:,2].min()),'back_native_z':float(rows[:,2].max()),'x_extent':float(abs(rows[:,0]).max())}
    (dest/'profiles.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats),flush=True)

if __name__=='__main__':main()
