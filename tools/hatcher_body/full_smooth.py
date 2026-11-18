"""Restart from native DFM; round angular surfaces on Mesh0 only."""
import importlib.util,sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('hatcher_detail_helpers',ROOT/'tools/hatcher_body/build.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
from build import GAME,read_tree,child,arr,triangles
from repair_panel_normals import leaves
engine=helpers.engine;OUT=ROOT/'out/hatcher_body_full_smooth';REL=helpers.REL
def key(p):return tuple(np.round(p,6))
def previous_region(p):
    x,y,z=p;s=helpers.smooth
    bracer=s(.19,.235,abs(x))*s(-.10,-.055,y)*(1-s(.135,.21,y))
    vest=s(.14,.21,y)*(1-s(.53,.57,y))*(1-s(.17,.235,abs(x)))
    return max(bracer,vest)

def region(p):
    # Keep the sole/contact plane and neck attachment fixed. Round the costume,
    # not its overall proportions; preserve the established upper-body treatment.
    y=p[1]
    added=.85*helpers.smooth(-.964,-.945,y)*(1-helpers.smooth(.52,.547,y))
    return max(previous_region(p),added)

def main():
    source=(ROOT/'out/hatcher_body_smooth/original/DATA'/REL).read_bytes();_,roots=read_tree(source);root=roots[0]
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
        # Tangential relaxation in newly treated areas avoids shrinking limbs.
        added=max(0.,mask-previous_region(pos))/max(mask,1e-9)
        delta-=normal*np.dot(delta,normal)*added
        delta*=mask
        length=np.linalg.norm(delta)
        if length>.006:delta*=.006/length
        rounded[k]=pos+delta
    profiles={}
    for side in [-1,1]:
        pts=np.asarray(list(points.values()))
        # Native outer cuff rim vertices (the upper rim also has inset duplicates).
        low=pts[(pts[:,0]*side>.23)&(pts[:,1]>-.04)&(pts[:,1]<.02)]
        top=pts[(pts[:,0]*side>.20)&(pts[:,1]>.085)&(pts[:,1]<.142)]
        lo=low.mean(axis=0);hi=top.mean(axis=0)
        axis=hi-lo;axis/=np.linalg.norm(axis)
        def diameter(ring):
            flat=ring-np.outer((ring-lo)@axis,axis)
            return max(np.linalg.norm(a-b) for a in flat for b in flat)
        profiles[side]=(lo,axis,0.,np.dot(hi-lo,axis),diameter(low)/2,diameter(top)/2)
    # Native horizontal envelopes retain width/depth of the legs and boots.
    # Samples use actual triangle-plane intersections, not a guessed cylinder.
    tri_positions=[]
    for group in child(mesh,'Face_groups').children:
        if group.children:
            tri_positions.extend(p[pi[tri]] for tri in triangles(group))
    tris=np.asarray(tri_positions)
    section_y=np.linspace(float(p[:,1].min())+.00001,.13,700)
    envelopes={}
    for side in [-1,1]:
        values=[]
        for height in section_y:
            hits=[]
            for i,j in [(0,1),(1,2),(2,0)]:
                a=tris[:,i];b=tris[:,j];den=b[:,1]-a[:,1]
                valid=(abs(den)>1e-9)&((a[:,1]-height)*(b[:,1]-height)<=0)
                a=a[valid];b=b[valid];den=den[valid]
                h=a+(b-a)*((height-a[:,1])/den)[:,None]
                hits.extend(h[h[:,0]*side>0])
            h=np.asarray(hits)
            values.append([h[:,0].min(),h[:,0].max(),h[:,2].min(),h[:,2].max()] if len(h) else [np.nan]*4)
        values=np.asarray(values)
        for col in range(4):
            valid=np.isfinite(values[:,col]);values[:,col]=np.interp(section_y,section_y[valid],values[valid,col])
        envelopes[side]=values
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
        # Circular cross sections around the native forearm axis. Diameters
        # come from the native cuff rims, not the inflated Phong surface.
        side=1 if old[0]>0 else -1
        lo,axis,t0,t1,r0,r1=profiles[side]
        t=np.dot(old-lo,axis)
        radial=old-lo-axis*t
        radius=np.linalg.norm(radial)
        blend=helpers.smooth(.18,.205,abs(old[0]))*(1-helpers.smooth(t1+.002,t1+.035,t))
        if blend>0 and t>=t0-.012 and radius>.008:
            desired=np.interp(t,[t0,t1],[r0,r1])
            # Retain the inset sleeve/lip surface inside the cuff.
            original_r=bary@np.linalg.norm((vertices-lo)-np.outer((vertices-lo)@axis,axis),axis=1)
            ratio=min(1.,original_r/max(desired,1e-9))
            target=lo+axis*t+radial/radius*(desired*ratio)
            q=q*(1-blend)+target*blend
        if old[1]<.13 and abs(old[0])<.18:
            bounds=[np.interp(q[1],section_y,envelopes[side][:,i]) for i in range(4)]
            # Retain the native section envelope, allowing only sub-mm tolerance.
            q[0]=np.clip(q[0],min(bounds[0]-.0005,old[0]),max(bounds[1]+.0005,old[0]))
            q[2]=np.clip(q[2],min(bounds[2]-.0005,old[2]),max(bounds[3]+.0005,old[2]))
        q[1]=max(q[1],float(p[:,1].min()))
        max_delta[0]=max(max_delta[0],float(np.linalg.norm(q-old)))
        return q
    helpers.OUT=OUT;engine.OUT=OUT;engine.REL=REL;engine.ACTIVE_LODS=(0,)
    engine.SUBDIVISIONS=2;engine.FOCUS_REFINEMENT=False;engine.POSITION_SAMPLE=sample
    engine.relief=lambda *args:np.zeros(3)
    engine.surface_maps=helpers.surface_maps;engine.export=helpers.preview_export
    engine.GAME=ROOT/'out/hatcher_body_smooth/original'
    engine.main()
    staged=(OUT/'stage/DATA'/REL).read_bytes()
    a={p:b for p,_,b in leaves(source)[1]};b={p:v for p,_,v in leaves(staged)[1]}
    changed=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
    assert all('/MultiLevel/Mesh0/' in k for k in changed)
    report=json.loads((OUT/'report.json').read_text());report.update(only_mesh0_changed=True,base='native game DFM',texture_displacement=False,max_smoothing_delta_m=max_delta[0])
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    print('Native source, Mesh0 only; max rounding movement:',max_delta[0])
if __name__=='__main__':main()

