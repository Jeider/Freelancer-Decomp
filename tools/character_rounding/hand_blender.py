"""Hand source study, editable rig and matched anatomical comparisons."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from blender_workspace import configure
configure('character_rounding')
OUT=ROOT/'out/character_rounding/hands'
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
ap=argparse.ArgumentParser();ap.add_argument('--name',default='benchmarkmalehandright');ap.add_argument('--source',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);folder=OUT/args.name
data=json.loads(gzip.decompress((folder/('source.json.gz' if args.source else 'edited.json.gz')).read_bytes()))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world.color=(.08,.08,.08)
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.58,.48,.38)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=True
points=[C@Vector(p) for p in data['points']]
faces=[[data['point_indices'][i] for i in t] for g in data['groups'] for t in g['faces']]
mesh=bpy.data.meshes.new('Native hand');mesh.from_pydata(points,[],faces);mesh.update()
ob=bpy.data.objects.new('Native hand',mesh);scene.collection.objects.link(ob)
for poly in mesh.polygons:poly.use_smooth=True
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.clip_start=.001
center=sum(points,Vector())/len(points)
for label,direction in [('front',Vector((0,-1,0))),('side',Vector((1,0,0))),('top',Vector((0,0,1))),('angle',Vector((1,-1,1)))]:
    cam.location=center+direction.normalized();cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.34;scene.render.filepath=str(folder/(('source_' if args.source else 'edited_')+label+'.png'));bpy.ops.render.render(write_still=True)
