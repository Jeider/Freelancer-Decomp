"""Native rear bands and projecting shoulder boards, offline references only."""
import sys, json, gzip, shutil
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
OUT=TOP/'source/open_uniform_study'
OUT.mkdir(parents=True,exist_ok=True)
photo=Path('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-s8R0S4.png')
if photo.exists() and not (OUT/'user_uniform_reference.png').exists():
    shutil.copyfile(photo,OUT/'user_uniform_reference.png')
for label,data,direction in [
    ('elite_back',native.load('body'),(0,-1,.05)),
    ('dietrich_front',json.loads(gzip.decompress((TOP/'source/dietrich/source/dietrich.json.gz').read_bytes())),(.4,1,.25)),
    ('dietrich_back',json.loads(gzip.decompress((TOP/'source/dietrich/source/dietrich.json.gz').read_bytes())),(.2,-1,.18))]:
    bpy.ops.wm.read_factory_settings(use_empty=True);configure('character_rounding')
    ob=native.native_mesh(data,label,native.collection('Native reference'));ob.location.z=.975662
    scene=bpy.context.scene;cam=studio(scene);cam.data.ortho_scale=.87
    d=Vector(direction).normalized();cam.location=Vector((0,0,1.43))+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=700;scene.render.resolution_y=700;scene.cycles.samples=20
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
    print('REFERENCE',label,flush=True)
