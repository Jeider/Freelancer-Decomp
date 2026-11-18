"""Render staged native DFM readbacks, before left / after right."""
import bpy,json,sys,argparse,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
exec(compile((ROOT/'tools/character_rounding/render.py').read_text().split('for rec in records:')[0],'body_preview_helpers','exec'))
OUT=ROOT/'out/character_rounding/all_bodies'
cache_dir=OUT/'optix_cache';cache_dir.mkdir(exist_ok=True);os.environ['OPTIX_CACHE_PATH']=str(cache_dir)
ap=argparse.ArgumentParser();ap.add_argument('--name');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.cycles.samples=12
scene.render.use_persistent_data=True
# Prefer hardware Cycles rendering for large offline comparison galleries.
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 gpu=[d for d in prefs.devices if d.type=='OPTIX']
 if gpu:
  for d in prefs.devices:d.use=d.type=='OPTIX'
  scene.cycles.device='GPU'
except Exception as error:print('Cycles CPU fallback:',error,flush=True)
for folder in sorted(OUT.iterdir()):
 if not (folder/'report.json').exists() or (args.name and folder.name!=args.name):continue
 report=json.loads((folder/'report.json').read_text());before=json.loads((folder/'before.json').read_text());after=json.loads((folder/'after.json').read_text())
 cache=folder/'render_source.json';same=cache.exists() and json.loads(cache.read_text()).get('sha256')==report['output_sha256']
 points=before['points'];low=min(p[1] for p in points);high=max(p[1] for p in points);width=max(p[0] for p in points)-min(p[0] for p in points)
 variants=[('front',False),('back',False)]
 for label,clay in variants:
  path=folder/(label+'.png')
  if path.exists() and same:continue
  cam=setup();offset=max(.44,width*.68);target=(0,0,.38);scale=max(1.85,width*2.6)
  if label in ('front','back'):target=(0,0,(low+high)/2);scale=max((high-low)*1.45,width*2.8)
  if label=='belt':target=(0,0,.09);scale=1.2;offset=.28
  if label=='cuff_clay':target=(.30,.08,.075);scale=.65;offset=.16
  def cut(d):
   if label!='cuff_clay':return d
   out=dict(d);out['groups']=[]
   for group in d['groups']:
    g=dict(group);g['faces']=[tri for tri in group['faces'] if all(d['points'][d['point_indices'][i]][0]>.19 and -.08<d['points'][d['point_indices'][i]][1]<.25 for i in tri)]
    if g['faces']:out['groups'].append(g)
   return out
  sign=-1 if label=='back' else 1
  model(cut(before),offset*sign,clay);model(cut(after),-offset*sign,clay)
  for ob in scene.objects:
   if ob.type=='MESH':ob.location.x-=target[0]
  focus=Vector((0,target[1],target[2]));cam.location=focus+Vector((0,4*sign,.10));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);print('PREVIEW',folder.name,label,flush=True)
 (folder/'render_source.json').write_text(json.dumps(dict(sha256=report['output_sha256'],front='front.png',back='back.png')))
