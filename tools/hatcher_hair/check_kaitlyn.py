"""Validate the separate Kaitlyn prototype without starting the game."""
import hashlib
import json
import numpy as np
from kaitlyn import OUT, REL, SOURCE, GAME
from build import read_tree, child, arr, triangles

def leaves(node, prefix=''):
    path=prefix+'/'+node.name
    if node.children:
        return {k:v for n in node.children for k,v in leaves(n,path).items()}
    return {path:node.blob}

baseline=(OUT/'original/DATA'/REL).read_bytes()
live=(GAME/'DATA'/SOURCE).read_bytes()
assert live==baseline, 'Original live head changed since this prototype started'
_,old=read_tree(baseline)
_,new=read_tree((OUT/'stage/DATA'/REL).read_bytes())
old,new=old[0],new[0]
for node in old.children:
    if node.name in ('MultiLevel','Material library','Texture library'):continue
    assert leaves(node)==leaves(child(new,node.name)), node.name
for node in child(old,'Texture library').children:
    assert leaves(node)==leaves(child(child(new,'Texture library'),node.name)), node.name
report=[]
for mesh in child(new,'MultiLevel').children:
    if not mesh.name.startswith('Mesh'):continue
    geo=child(mesh,'Geometry')
    p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3)
    pi=arr(geo,'Point_indices','<u4').ravel()
    uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
    assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()
    assert len(pi)==len(ui) and max(pi)<len(p) and max(ui)<len(uv)
    first=arr(geo,'Point_bone_first','<u4').ravel()
    counts=arr(geo,'Point_bone_count','<u4').ravel()
    weights=arr(geo,'Bone_weight_chain','<f4').ravel()
    assert len(first)==len(p)==len(counts)
    for f,c in zip(first,counts):
        assert c>0 and f+c<=len(weights) and abs(sum(weights[f:f+c])-1)<1e-4
    total=0
    for group in child(mesh,'Face_groups').children:
        if not group.children:continue
        ts=np.asarray(triangles(group))
        if ts.size:assert ts.min()>=0 and ts.max()<len(pi)
        total+=len(ts)
    report.append(dict(mesh=mesh.name,points=len(p),triangles=total))
result=dict(original_unchanged=True,original_sha256=hashlib.sha256(live).hexdigest(),
            skeleton_and_original_textures_unchanged=True,lods=report,
            limitation='Offline structural checks only; facial animation and game rendering not tested.')
(OUT/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
