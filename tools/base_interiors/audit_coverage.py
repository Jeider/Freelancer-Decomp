"""Automatic material/adjacency audit. Does not pretend to recognize painted shapes."""
import json,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/base_interiors/rh_biz_01_base/bar'/(sys.argv[1] if len(sys.argv)>1 else 'prototype_v4')
data=json.loads((OUT/'scene_mesh.json').read_text());stats=json.loads((OUT/'prototype_stats.json').read_text())
edges=defaultdict(set);groups={};changed=set(stats['changed_batches'])
for i,b in enumerate(data['batches']):
 v=np.array(b['vertices']);name=data['materials'][b['material']]['name'].split('.')[0].lower()
 groups[i]={'material':name,'part':b['part'],'triangles':b['triangles'],'processed':i in changed,'neighbors':[],'uv_min':v[:,6:8].min(0).tolist(),'uv_max':v[:,6:8].max(0).tolist()}
 tris=v.reshape(-1,3,b['stride']);cross=np.cross(tris[:,1,:3]-tris[:,0,:3],tris[:,2,:3]-tris[:,0,:3]);areas=np.linalg.norm(cross,axis=1)*.5;normals=cross/np.maximum(areas[:,None]*2,1e-10);centers=tris[:,:,:3].mean(1)
 best_area=0.
 for k in np.argsort(areas)[-20:]:
  if abs(normals[k,1])>.35:continue # floor/ceiling is not a wall candidate
  coplanar=(abs(normals@normals[k])>.995)&(abs((centers-centers[k])@normals[k])<.03)
  best_area=max(best_area,float(areas[coplanar].sum()))
 groups[i]['largest_sampled_wall_plane_area']=best_area
 groups[i]['flat_wall_image_review_candidate']=best_area>=2
 groups[i]['selection_note']='Inspect the material image for painted structural relief; flatness alone never authorizes subdivision.'
 for t in v.reshape(-1,3,b['stride']):
  pts=[tuple(np.round(p[:3],4)) for p in t]
  for a,c in ((0,1),(1,2),(2,0)):edges[tuple(sorted((pts[a],pts[c])))].add(i)
neighbors=defaultdict(set)
for owners in edges.values():
 for i in owners:neighbors[i].update(owners-{i})
review=[]
for i,near in neighbors.items():
 groups[i]['neighbors']=sorted(near)
 if i in changed:
  for j in near:
   if j not in changed and groups[j]['part']=='Root':review.append({'processed':groups[i]['material'],'review_neighbor':groups[j]['material'],'reason':'Shared native edge; inspect imagery before deciding whether relief is appropriate.'})
assert 7 in changed and 8 in changed,'Both alternating fascia materials must be handled.'
assert all(groups[i]['processed'] for i,b in enumerate(data['batches']) if groups[i]['material'] in ('detailmap_r_bar_03','detailmap_r_bar_04'))
if OUT.name=='prototype_v5':
 assert all(any(g['material']==name and g['processed'] for g in groups.values()) for name in ('r_bar_22','r_bar_28','r_bar_05'))
report={'scope':'Automatic discovery and adjacency checks; contour recognition remains manual. Neighbors are review candidates, not automatic edit targets.','groups':groups,'neighbor_review_candidates':review,'fascia_material_coverage':'all r_bar_03 and r_bar_04 batches processed'}
(OUT/'coverage_audit.json').write_text(json.dumps(report,indent=2));print('Material coverage checked; adjacent unprocessed groups recorded for review, not blindly modified.')
