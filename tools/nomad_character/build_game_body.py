import sys,json,struct,copy,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,DataFolder,read_tree,write_tree,child,blob,put,arr,triangles
from generate_station_lods import Node
from repair_panel_normals import leaves
OUT=ROOT/'out/nomad_character/game_body_v3';REL='CHARACTERS/BODIES/alien_nomad_body.dfm'
source=(GAME/'DATA/CHARACTERS/BODIES/robot_body_a.dfm').read_bytes();header,roots=read_tree(source);root=roots[0]
mesh=np.load(OUT/'mesh.npz');p=mesh['points'];n=mesh['normals'];uv=mesh['uv'];f=mesh['faces'];w=mesh['weights'];names=mesh['bone_names'].tolist()
bone_ids={blob(part,'Object name').rstrip(b'\0').decode():struct.unpack('<I',blob(part,'Index'))[0] for part in child(root,'Cmpnd').children if part.children and any(x.name=='Index' for x in part.children)}
assert all(name in bone_ids for name in names)
assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()
assert len(p)<65536 and f.min()>=0 and f.max()<len(p)
assert np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-4
assert (w>=0).all() and np.max(abs(w.sum(axis=1)-1))<1e-5 and (np.count_nonzero(w,axis=1)<=4).all()
first=[];counts=[];ids=[];weights=[]
for row in w:
 idx=np.flatnonzero(row);first.append(len(ids));counts.append(len(idx));ids.extend(bone_ids[names[i]] for i in idx);weights.extend(row[idx])
def branch(name,children):
 out=Node(name);out.children=children;return out
def array(name,value,kind):return Node(name,np.asarray(value,dtype=kind).tobytes())
geometry=branch('Geometry',[array('Points',p,'<f4'),array('Vertex_normals',n,'<f4'),array('Point_indices',np.arange(len(p)),'<u4'),array('UV0',uv,'<f4'),array('UV0_indices',np.arange(len(p)),'<u4'),array('Point_bone_first',first,'<u4'),array('Point_bone_count',counts,'<u4'),array('Bone_id_chain',ids,'<u4'),array('Bone_weight_chain',weights,'<f4')])
groups=branch('Face_groups',[array('Count',[1],'<u4'),branch('Group0',[Node('Material_name',b'alien_nomad_body\0'),array('Face_indices',f,'<u2')])])
multi=child(root,'MultiLevel');multi.children=[array('Fractions',[1.0],'<f4'),branch('Mesh0',[groups,geometry])]
# Reuse the user's proven static-model texture, including its DDS mip chain.
_,static_roots=read_tree((ROOT/'out/nomad_character/alien/char_alien.3db').read_bytes())
static=static_roots[0];texture=copy.deepcopy(child(child(static,'Texture library'),'char_alien.tga'));texture.name='alien_nomad_body.tga'
material=branch('alien_nomad_body',[Node('Type',b'DcDt\0'),Node('Dt_name',b'alien_nomad_body.tga\0'),array('Dt_flags',[64],'<u4')])
child(root,'Material library').children=[array('Material count',[1],'<u4'),material]
child(root,'Texture library').children=[texture]
result=write_tree(header,roots)
# All native skeleton, hardpoint and compound leaves must remain exact.
old={k:b for k,_,b in leaves(source)[1]};new={k:b for k,_,b in leaves(result)[1]}
for k,b in old.items():
 if not any(x in k for x in ['/MultiLevel/','/Material library/','/Texture library/']):assert new[k]==b,k
stage=DataFolder(root=OUT/'stage');stage.sync_data_file(REL,result)
configs={
 'CHARACTERS/bodyparts.ini':b'[Body]\r\nnickname = alien_nomad_body\r\nmesh = characters\\bodies\\alien_nomad_body.dfm\r\n',
 'CHARACTERS/costumes.ini':b'[Costume]\r\nnickname = alien_nomad\r\nbody = alien_nomad_body\r\n'}
manifest={'files':{},'body':'alien_nomad_body','costume':'alien_nomad','hands':'integrated, LHand/RHand; no external hand parts','head':'integrated','lods':1,'triangles':len(f),'points':len(p),'normal_maps':'not enabled; original static DcDt material','native_skeleton_preserved':True}
sha=lambda b:hashlib.sha256(b).hexdigest()
live=DataFolder(root=GAME)
manifest['files'][REL]={'before':sha(live.data_path(REL).read_bytes()) if live.data_path(REL).exists() else None,'after':sha(result)}
previous=json.loads((ROOT/'out/nomad_character/game_body/manifest.json').read_text())['files'][REL]['after']
assert manifest['files'][REL]['before'] in (None,previous,sha(result)), 'Existing body differs'
for rel,addition in configs.items():
 original=live.data_path(rel).read_bytes();token=b'nickname = '+(b'alien_nomad_body' if rel.endswith('bodyparts.ini') else b'alien_nomad')
 if rel.endswith('bodyparts.ini'):
  context=(b'[DetailSwitchTable]\r\nswitch = 100, 50000\r\n\r\n'
   b'[PetalAnimations]\r\nanim = characters\\animations\\BodyGenericMale.anm\r\n'
   b'anim = characters\\animations\\BodyStoryMale.anm\r\nanim = characters\\animations\\Special.anm\r\n\r\n'
   b'[Skeleton]\r\nsex = male\r\n\r\n')
  if context+addition in original:updated=original
  elif addition in original:
   assert original.count(addition)==1;updated=original.replace(addition,context+addition)
  else:
   assert token not in original;updated=original.rstrip(b'\r\n')+b'\r\n\r\n'+context+addition
 else:
  if addition in original:updated=original
  else:
   assert token not in original;updated=original.rstrip(b'\r\n')+b'\r\n\r\n'+addition
 stage.sync_data_file(rel,updated);manifest['files'][rel]={'before':sha(original),'after':sha(updated)}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
