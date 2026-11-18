"""Large matched detail views for the focused elite study."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
# Reuse only the tested scene/mesh loader, not the batch rendering loop.
script=(ROOT/'tools/character_rounding/render.py').read_text().split('for rec in records:')[0]
exec(compile(script,'render_helpers','exec'))
OUT=ROOT/'out/character_rounding/elite_focus'
before=json.loads((OUT/'before.json').read_text());after=json.loads((OUT/'after.json').read_text())
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.cycles.samples=24
views=[('upper',(0,0,.42),1.85,.44,False),('upper_clay',(0,0,.42),1.85,.44,True),
 ('cuff',(.31,.09,.075),.62,.15,False),('cuff_clay',(.31,.09,.075),.62,.15,True),
 ('cuff_end',(.31,.09,.025),.58,.145,True),('shoulder',(0,0,.50),1.24,.30,True)]
for label,target,scale,offset,clay in views:
 cam=setup()
 def cropped(data):
  if not label.startswith('cuff'):return data
  result=dict(data);result['groups']=[]
  for group in data['groups']:
   g=dict(group);g['faces']=[tri for tri in group['faces'] if all(data['points'][data['point_indices'][i]][0]>.20 and -.065<data['points'][data['point_indices'][i]][1]<.24 for i in tri)]
   if g['faces']:result['groups'].append(g)
  return result
 model(cropped(before),offset,clay);model(cropped(after),-offset,clay)
 # Shift both meshes to centre the selected right cuff in each half.
 for ob in bpy.context.scene.objects:
  if ob.type=='MESH':ob.location.x-=target[0]
 focus=Vector((0,target[1],target[2]));cam.location=focus+Vector((0,3,-1.5 if label=='cuff_end' else .5))
 cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
 if label=='upper':bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'elite_comparison.blend'))
print('All elite detail previews complete')
