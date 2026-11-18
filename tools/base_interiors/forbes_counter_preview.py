"""Whole-counter and reverse-counter review, using native exported geometry."""
import sys,json,math,warnings
from pathlib import Path
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blender_workspace import configure
configure('base_interiors')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from forbes_counter_audit import OUT,SOURCE,RETAIL
from native_common import sha,dump
from depot_family_preview import make_mesh,cv

SHOTS=[
 ('counter_overview',(5,3,5),(0,1.1,-1.7),4,62),
 ('counter_front',(0,1.2,3.5),(0,.6,-.3),2.8,65),
 ('counter_left',(-4,1.3,1.6),(-1,.65,-1.1),2.6,66),
 ('counter_right',(4,1.3,1.6),(1,.65,-1.1),2.6,66),
 ('back_bar',(0,1.7,-.6),(0,1.6,-3.5),2.4,76),
]


def main():
 baseline='--baseline' in sys.argv;build=OUT/('baseline' if baseline else 'modeled');build.mkdir(exist_ok=True)
 pins=json.loads((OUT/'sources.json').read_text());report=json.loads((OUT/'surfaces.json').read_text())
 old=np.load(OUT/'original_geometry.npz')
 if baseline:
  data=old;changed=set();digest=pins['installed_sha256'];expected=pins['source_triangles']
 else:
  native=json.loads((build/'native_validation.json').read_text());digest=native['exported_sha256']
  assert sha(Path(native['cmp']).read_bytes())==digest
  expected=native['result_triangles'];data=np.load(build/'exported_geometry.npz')
  changed={g['group'] for g in json.loads((build/'geometry_validation.json').read_text())['groups']}
 bpy.ops.wm.read_factory_settings(use_empty=True);configure('base_interiors');scene=bpy.context.scene
 scene['native_cmp_sha256']=digest;scene['scope']='Original' if baseline else 'Reviewed counter relief decoded from native CMP'
 scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.use_persistent_data=True
 scene.render.resolution_x=1280;scene.render.resolution_y=900;scene.render.resolution_percentage=100
 scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.5
 scene.world=bpy.data.worlds.new('Inspection ambient');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 if any(d.use for d in prefs.devices):scene.cycles.device='GPU'
 materials={}
 for key,source in report['materials'].items():
  mat=bpy.data.materials.new(source['name']);mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
  bs.inputs['Roughness'].default_value=.65;dt=source['textures'].get('Dt_name')
  if dt:
   tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/dt['path']),check_existing=True)
   uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UV0';links.new(uv.outputs[0],tex.inputs[0]);links.new(tex.outputs['Color'],bs.inputs['Base Color'])
   links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.2
   if 'Ot' in source['type']:links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
  if 'Two' not in source['type']:
   geo=nodes.new('ShaderNodeNewGeometry');transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
   links.new(geo.outputs['Backfacing'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
  materials[key]=mat
 archive=bpy.data.collections.new('ARCHIVE - original counter surfaces - disabled');active=bpy.data.collections.new('Counter relief - exported CMP');rest=bpy.data.collections.new('Retained room geometry')
 for c in (archive,active,rest):scene.collection.children.link(c)
 for g in report['groups']:
  g['uv_sets']=(data[g['key']].shape[-1]-10)//2
  make_mesh(g,data[g['key']],materials[g['material']],active if g['key'] in changed else rest)
  if g['key'] in changed:make_mesh(g,old[g['key']],materials[g['material']],archive,'_original')
 clay=bpy.data.materials.new('Diagnostic clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.4,.43,.46,1)
 # Keep the room's outside/back faces transparent in the geometry-only views,
 # just as they are in the textured preview; otherwise a wall hides the overview.
 nodes=clay.node_tree.nodes;links=clay.node_tree.links;bs=nodes.get('Principled BSDF')
 geo=nodes.new('ShaderNodeNewGeometry');transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
 links.new(geo.outputs['Backfacing'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
 ld=bpy.data.lights.new('Inspection softbox','AREA');ld.shape='DISK';lamp=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(lamp)
 cam=bpy.data.objects.new('Counter review camera',bpy.data.cameras.new('Counter review camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.clip_start=.02
 def toggle(after):
  archive.hide_render=after;archive.hide_viewport=after;active.hide_render=not after;active.hide_viewport=not after
 def point(position,target,scale,fov):
  cam.location=cv(position);q=cv(target);cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(fov)
  lamp.location=cam.location+Vector((scale*.5,0,scale*.6));lamp.rotation_euler=(q-lamp.location).to_track_quat('-Z','Y').to_euler();ld.energy=55*scale**2;ld.size=scale*.6
 for name,pos,target,scale,fov in SHOTS:
  point(pos,target,scale,fov)
  for style in (('clay',) if '--clay-only' in sys.argv else ('textured','clay')):
   scene.view_layers[0].material_override=clay if style=='clay' else None
   for mode in (('before',) if baseline else ('before','after')):
    toggle(mode=='after');scene.render.filepath=str(build/f'{name}_{style}_{mode}.png');bpy.ops.render.render(write_still=True)
  print('REVIEWED_VIEW',name,flush=True)
 toggle(True);scene.view_layers[0].material_override=None;point(*SHOTS[0][1:]);bpy.ops.file.pack_all()
 blend=build/'forbes_bar_counter.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.wm.open_mainfile(filepath=str(blend));configure('base_interiors')
 archive=bpy.data.collections['ARCHIVE - original counter surfaces - disabled'];active=bpy.data.collections['Counter relief - exported CMP']
 assert archive.hide_render and archive.hide_viewport and not active.hide_render and not active.hide_viewport
 visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not any(c.hide_render for c in o.users_collection)]
 assert sum(len(o.data.polygons) for o in visible)==expected
 assert all(im.packed_file for im in bpy.data.images if im.type=='IMAGE' and im.source=='FILE')
 assert sha(SOURCE.read_bytes())==pins['installed_sha256'] and sha(RETAIL.read_bytes())==pins['original_sha256']
 dump(build/'preview_validation.json',dict(cmp_sha256=digest,blend_sha256=sha(blend.read_bytes()),reopened=True,
  originals_hidden_in_viewport_and_render=True,visible_triangles=expected,textures_packed=True,views=[s[0] for s in SHOTS],
  sources_unchanged=True,baseline=baseline,scope='Offline current-artwork preview with matched diagnostic lighting; game shader and THN props are not simulated.'))
 print('PREVIEW_COMPLETE',flush=True)


if __name__=='__main__':main()
