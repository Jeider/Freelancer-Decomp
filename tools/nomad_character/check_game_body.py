import sys,json,struct,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,read_tree,child,blob,arr,triangles
from repair_panel_normals import leaves
OUT=ROOT/'out/nomad_character/game_body_v3';manifest=json.loads((OUT/'manifest.json').read_text());mesh=np.load(OUT/'mesh.npz')
rel='CHARACTERS/BODIES/alien_nomad_body.dfm';data=(OUT/'stage/DATA'/rel).read_bytes()
assert hashlib.sha256(data).hexdigest()==manifest['files'][rel]['after']
_,roots=read_tree(data);r=roots[0];multi=child(r,'MultiLevel');assert [n.name for n in multi.children]==['Fractions','Mesh0']
assert struct.unpack('<f',blob(multi,'Fractions'))==(1.,)
m=child(multi,'Mesh0');g=child(m,'Geometry');p=arr(g,'Points','<f4',3);normal=arr(g,'Vertex_normals','<f4',3);uv=arr(g,'UV0','<f4',2)
assert np.allclose(p,mesh['points'],atol=1e-7) and np.allclose(normal,mesh['normals'],atol=1e-7) and np.allclose(uv,mesh['uv'],atol=1e-7)
assert np.array_equal(arr(g,'Point_indices','<u4').ravel(),np.arange(len(p)))
face=triangles(child(child(m,'Face_groups'),'Group0'));assert np.array_equal(face,mesh['faces'])
ids={struct.unpack('<I',blob(part,'Index'))[0]:blob(part,'Object name').rstrip(b'\0').decode() for part in child(r,'Cmpnd').children if part.children and any(x.name=='Index' for x in part.children)}
names=mesh['bone_names'].tolist();starts=arr(g,'Point_bone_first','<u4').ravel();counts=arr(g,'Point_bone_count','<u4').ravel();bones=arr(g,'Bone_id_chain','<u4').ravel();ws=arr(g,'Bone_weight_chain','<f4').ravel()
restored=np.zeros_like(mesh['weights'])
for i,(start,count) in enumerate(zip(starts,counts)):
 assert 1<=count<=4
 for j in range(start,start+count):restored[i,names.index(ids[bones[j]])]=ws[j]
assert np.allclose(restored,mesh['weights'],atol=1e-7)
assert np.any(restored[:,names.index('LHand')]>0) and np.any(restored[:,names.index('RHand')]>0) and np.any(restored[:,names.index('Body_Head')]>0)
native={k:b for k,_,b in leaves((GAME/'DATA/CHARACTERS/BODIES/robot_body_a.dfm').read_bytes())[1]}
for k,_,b in leaves(data)[1]:
 if not any(s in k for s in ['/MultiLevel/','/Material library/','/Texture library/']):assert b==native[k]
mat=child(child(r,'Material library'),'alien_nomad_body');texname=blob(mat,'Dt_name').rstrip(b'\0').decode();dds=blob(child(child(r,'Texture library'),texname),'MIPS');assert dds.startswith(b'DDS ')
costume=(OUT/'stage/DATA/CHARACTERS/costumes.ini').read_bytes().split(b'nickname = alien_nomad\r\n')[-1]
assert b'body = alien_nomad_body' in costume and b'hand =' not in costume and b'head =' not in costume
bodyparts=(OUT/'stage/DATA/CHARACTERS/bodyparts.ini').read_bytes()
prefix=bodyparts.split(b'nickname = alien_nomad_body')[0]
assert b'sex = male' in prefix.rsplit(b'[Skeleton]',1)[-1]
animations=prefix.rsplit(b'[PetalAnimations]',1)[-1]
assert b'BodyGenericMale.anm' in animations and b'BodyStoryMale.anm' in animations and b'HandFemale.anm' not in animations
report=dict(native_readback_matches_blender=True,native_bone_id_mapping_verified=True,head_and_hands_weighted=True,external_hands_disabled=True,skeleton_exact=True,male_body_animations=True,dds_texture_present=True,vertices=len(p),triangles=len(face),game_launched=False)
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
