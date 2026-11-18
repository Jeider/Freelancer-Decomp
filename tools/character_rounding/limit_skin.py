"""Enforce native four-influence skinning on the offline batch only."""
from all_bodies import *
records=[]
for folder in sorted(OUT.iterdir()):
 if not (folder/'report.json').exists():continue
 report=json.loads((folder/'report.json').read_text());path=OUT/'stage/DATA/CHARACTERS/BODIES'/(folder.name+'.dfm');raw=path.read_bytes()
 header,roots=read_tree(raw);g=child(child(child(roots[0],'MultiLevel'),'Mesh0'),'Geometry')
 counts=arr(g,'Point_bone_count','<u4').ravel();first=arr(g,'Point_bone_first','<u4').ravel();ids=arr(g,'Bone_id_chain','<u4').ravel();weights=arr(g,'Bone_weight_chain','<f4').ravel()
 if counts.max()<=4:continue
 assert report['changed'],'Do not alter preserved source bodies'
 starts=[];cc=[];bb=[];ww=[];discarded=[]
 for f,c in zip(first,counts):
  pairs=list(zip(map(int,ids[f:f+c]),map(float,weights[f:f+c])))
  if c>4:
   pairs=sorted(pairs,key=lambda item:(-item[1],item[0]));discarded.append(sum(w for _,w in pairs[4:]));pairs=pairs[:4]
  total=sum(w for _,w in pairs);starts.append(len(bb));cc.append(len(pairs));bb.extend(k for k,_ in pairs);ww.extend(w/total for _,w in pairs)
 for nm,val,typ in [('Point_bone_first',starts,'<u4'),('Point_bone_count',cc,'<u4'),('Bone_id_chain',bb,'<u4'),('Bone_weight_chain',ww,'<f4')]:put(g,nm,np.asarray(val,dtype=typ).tobytes())
 data=write_tree(header,roots);old={k:v for k,_,v in leaves(raw)[1]};new={k:v for k,_,v in leaves(data)[1]}
 allowed={'Point_bone_first','Point_bone_count','Bone_id_chain','Bone_weight_chain'}
 assert all('/MultiLevel/Mesh0/Geometry/' in k and k.rsplit('/',1)[-1] in allowed for k in old if old[k]!=new[k])
 DataFolder(root=OUT/'stage').sync_data_file('CHARACTERS/BODIES/'+path.name,data)
 previous=report['output_sha256'];report['output_sha256']=hashlib.sha256(data).hexdigest();report['skin_limit']=4
 report['skin_vertices_reduced']=len(discarded);report['max_discarded_weight']=max(discarded)
 # Geometry, textures and normals are byte-identical: completed static
 # previews remain exact, despite the new animation weights.
 cache=folder/'render_source.json'
 if cache.exists():
  meta=json.loads(cache.read_text());assert meta['sha256']==previous
  meta['sha256']=report['output_sha256'];meta['skin_only_update']=True;cache.write_text(json.dumps(meta))
 (folder/'report.json').write_text(json.dumps(report,indent=2))
 records.append(dict(name=folder.name,vertices=len(discarded),max_discarded_weight=max(discarded)))
(OUT/'skin_limit.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
