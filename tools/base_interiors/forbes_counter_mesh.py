"""Constrained relief on the explicitly selected curved counter strips."""
import sys,json,collections
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blender_workspace import configure
configure('base_interiors')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from forbes_counter_audit import OUT
from depot_relief_mesh import triangulate,offset_polygon,cross2
from relief_mesh import area,intersect
from native_common import dump


def normalize(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-20)


def inset(p,d):
    # Image-traced gaps can taper to a sharp tip. Limit the inset's miter there
    # instead of extending a tiny bevel far outside the painted opening.
    out=[]
    for i,b in enumerate(p):
        u=normalize(b-p[i-1]);v=normalize(p[(i+1)%len(p)]-b)
        nu=np.array([-u[1],u[0]]);nv=np.array([-v[1],v[0]])
        q=(nu+nv)*d/max(1+nu@nv,1e-8)
        length=np.linalg.norm(q)
        if length>4*d:q*=4*d/length
        out.append(b+q)
    return np.array(out)


def smooth_directions(t,ids):
    pool=collections.defaultdict(list)
    for i in ids:
        tri=t[i];n=normalize(np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]))
        if n@tri[:,3:6].mean(0)<0:n=-n
        for v in tri:pool[tuple(np.round(v[[0,2]],5))].append(n)
    values={k:normalize(np.mean(v,axis=0)) for k,v in pool.items()}
    return {i:np.array([values[tuple(np.round(v[[0,2]],5))] for v in t[i]]) for i in ids}


def rebuild_attributes(tri,source,source_directions):
    matrix=np.vstack((source[:,6:8].T,np.ones(3)))
    weights=np.c_[tri[:,6:8],np.ones(3)]@np.linalg.inv(matrix).T
    original=weights@source
    base_normal=normalize(np.cross(source[1,:3]-source[0,:3],source[2,:3]-source[0,:3]))
    if base_normal@source[:,3:6].mean(0)<0:base_normal=-base_normal
    heights=(tri[:,:3]-original[:,:3])@base_normal
    smooth=normalize(weights@source_directions)
    tri[:,:3]=original[:,:3]+heights[:,None]*smooth
    face=normalize(np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]))
    if face@smooth.mean(0)<0:face=-face
    tri[:,3:6]=normalize(face+smooth-base_normal)
    # Installed model encodes tangent.xyz/sign in the final four floats (two
    # TEXCOORD slots). Keep all real UV channels; recompute this tangent frame.
    duv=tri[1:,6:8]-tri[0,6:8];dp=tri[1:,:3]-tri[0,:3]
    tangent,bitangent=np.linalg.solve(duv,dp)
    tangent=normalize(tangent-(tri[:,3:6]@tangent)[:,None]*tri[:,3:6])
    sign=np.sign(np.einsum('ij,j->i',np.cross(tri[:,3:6],tangent),bitangent))
    assert np.all(abs(sign)==1)
    tri[:,-4:-1]=tangent;tri[:,-1]=sign
    return tri


def main():
    build=OUT/'modeled';definition=json.loads((build/'features.json').read_text())
    source=np.load(OUT/'original_geometry.npz');surfaces=json.loads((OUT/'surfaces.json').read_text());meta={g['key']:g for g in surfaces['groups']}
    result={k:source[k] for k in source.files};features=definition['features'];summaries=[];coverage=[];directions={};parents={};repairs=[]
    for f in features:
        f['outer']=np.array(f['points_px'],float)/768;f['bevel']=f['bevel_px']/768
        f['inner']=inset(f['outer'],f['bevel'])
    for key,selected in definition['source_groups'].items():
        t=source[key].astype(float);name=surfaces['materials'][meta[key]['material']]['name']
        if key=='Back Bar Illum_00':
            # The installed source has uninitialised UV1 in exactly one corner.
            # Three other copies of that same position + UV0 agree exactly.
            refs=[(0,2),(1,2),(2,0)];v=t[5,0]
            assert np.all(abs(v[8:10])>1e30)
            matches=np.array([t[i,j] for i,j in refs])
            assert np.all(matches[:,:3]==v[:3]) and np.all(matches[:,6:8]==v[6:8])
            assert np.all(matches[:,8:10]==matches[0,8:10])
            repairs.append(dict(group=key,triangle=5,corner=0,slots=[8,9],
                before=v[8:10].tolist(),after=matches[0,8:10].tolist(),matching_source_corners=refs))
            t[5,0,8:10]=matches[0,8:10]
        fs=[f for f in features if f['material']==name];dirs=smooth_directions(t,selected);out=[];parent=[]
        directions[key]={str(i):d.tolist() for i,d in dirs.items()}
        for f in fs:
            overlap=0.
            for i in selected:
                uv=t[i,:,6:8];uv=uv if cross2(uv[1]-uv[0],uv[2]-uv[0])>0 else uv[::-1]
                overlap+=area(intersect(f['outer'],uv))
            assert overlap>1e-8,(key,f['label'])
            coverage.append(dict(group=key,feature=f['id'],label=f['label'],coverage=overlap/area(f['outer'])))
        for i,tri in enumerate(t):
            if i not in dirs:out.append(tri);parent.append(i);continue
            uv=tri[:,6:8];uv=uv if cross2(uv[1]-uv[0],uv[2]-uv[0])>0 else uv[::-1]
            hits=[f for f in fs if area(intersect(f['outer'],uv))>1e-10]
            if not hits:out.append(tri);parent.append(i);continue
            n=normalize(np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]))
            if n@tri[:,3:6].mean(0)<0:n=-n
            tris,_,_=triangulate(tri,hits,n,[])
            out.extend(rebuild_attributes(q,tri,dirs[i]) for q in tris);parent.extend([i]*len(tris))
        result[key]=np.array(out,dtype='<f4');parents[key]=parent
        summaries.append(dict(group=key,material=name,source_triangles=len(t),result_triangles=len(out),selected_source_triangles=selected))
        print('MODELED',key,len(t),'->',len(out),flush=True)
    np.savez_compressed(build/'geometry.npz',**result)
    dump(build/'geometry_validation.json',dict(original_triangles=sum(len(source[k]) for k in source.files),
        result_triangles=sum(len(v) for v in result.values()),groups=summaries,coverage=coverage,
        source_triangle_indices=parents,displacement_directions=directions,source_uv_repairs=repairs,
        method='Constrained contour triangulation with a shared smooth normal field across the curved strip; source UV interpolation and regenerated per-corner tangent frames.'))
    print('GEOMETRY_COMPLETE',sum(len(v) for v in result.values()),flush=True)


if __name__=='__main__':main()
