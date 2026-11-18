"""Restart from native DFM; round angular surfaces on Mesh0 only."""
import importlib.util,sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('hatcher_detail_helpers',ROOT/'tools/hatcher_body/build.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
from build import GAME,read_tree,child,arr,triangles
from repair_panel_normals import leaves
engine=helpers.engine;OUT=ROOT/'out/hatcher_body_smooth';REL=helpers.REL
def key(p):return tuple(np.round(p,6))
def region(p):
    x,y,z=p;s=helpers.smooth
    bracer=s(.19,.235,abs(x))*s(-.10,-.055,y)*(1-s(.135,.21,y))
    vest=s(.14,.21,y)*(1-s(.53,.57,y))*(1-s(.17,.235,abs(x)))
    return max(bracer,vest)

def main():
    source=(GAME/'DATA'/REL).read_bytes();_,roots=read_tree(source);root=roots[0]
    mesh=child(child(root,'MultiLevel'),'Mesh0');geo=child(mesh,'Geometry')
    p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3);pi=arr(geo,'Point_indices','<u4').ravel()
    points={key(v):v.copy() for v in p};neighbors={k:set() for k in points};edges={};normals={}
    for i,pos in enumerate(p):normals.setdefault(key(pos),[]).append(n[i])
    for group in child(mesh,'Face_groups').children:
        if not group.children:continue
        for tri in triangles(group):
            keys=[key(p[pi[v]]) for v in tri]
            for a,b in zip(keys,keys[1:]+keys[:1]):
                if a==b:continue
                neighbors[a].add(b);neighbors[b].add(a)
                e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1
    borders={k:set() for k in points}
    for (a,b),count in edges.items():
        if count==1:borders[a].add(b);borders[b].add(a)
    rounded={};directions={}
    for k,pos in points.items():
        normal=np.mean(normals[k],axis=0);normal/=max(np.linalg.norm(normal),1e-9);directions[k]=normal
        mask=region(pos);near=neighbors[k]
        delta=np.zeros(3)
        if len(borders[k])==2:
            # Gently round polygonal rim paths, retaining the opening.
            delta=(sum((points[v] for v in borders[k]),np.zeros(3))-2*pos)*.125
        elif not borders[k] and near:
            # Conservative one-ring relaxation. No texture-driven displacement.
            delta=(np.mean([points[v] for v in near],axis=0)-pos)*.18
        delta*=mask
        length=np.linalg.norm(delta)
        if length>.006:delta*=.006/length
        rounded[k]=pos+delta
    max_delta=[0.]
    def sample(vertices,bary,lod):
        old=bary@vertices
        if lod:return old
        ks=[key(v) for v in vertices];v=np.asarray([rounded[k] for k in ks]);ns=np.asarray([directions[k] for k in ks])
        linear=bary@v
        # Phong triangle interpolation bends newly inserted edge samples along
        # the original smooth normal field instead of merely splitting flats.
        projected=np.asarray([linear-ns[i]*np.dot(linear-v[i],ns[i]) for i in range(3)])
        q=linear+(bary@projected-linear)*.85*region(old)
        delta=q-old;length=np.linalg.norm(delta)
        if length>.009:q=old+delta*(.009/length)
        max_delta[0]=max(max_delta[0],float(np.linalg.norm(q-old)))
        return q
    helpers.OUT=OUT;engine.OUT=OUT;engine.REL=REL;engine.ACTIVE_LODS=(0,)
    engine.SUBDIVISIONS=2;engine.FOCUS_REFINEMENT=False;engine.POSITION_SAMPLE=sample
    engine.relief=lambda *args:np.zeros(3)
    engine.surface_maps=helpers.surface_maps;engine.export=helpers.preview_export
    engine.main()
    staged=(OUT/'stage/DATA'/REL).read_bytes()
    a={p:b for p,_,b in leaves(source)[1]};b={p:v for p,_,v in leaves(staged)[1]}
    changed=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
    assert all('/MultiLevel/Mesh0/' in k for k in changed)
    report=json.loads((OUT/'report.json').read_text());report.update(only_mesh0_changed=True,base='native game DFM',texture_displacement=False,max_smoothing_delta_m=max_delta[0])
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    print('Native source, Mesh0 only; max rounding movement:',max_delta[0])
if __name__=='__main__':main()
