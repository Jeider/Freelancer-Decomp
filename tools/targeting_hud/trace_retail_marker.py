"""Trace a retail marker's bright core into simplified polygons and triangles.

Only the offline exporter reads the image. Runtime geometry has no texture.
"""
import hashlib
import io
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from generate_station_lods import read_tree, child


def simplify(points, tolerance):
    def rdp(p):
        if len(p)<3:return p
        d=p[-1]-p[0]
        if np.linalg.norm(d)<1e-8:return p
        t=np.clip((p-p[0])@d/(d@d),0,1)
        distances=np.linalg.norm(p-p[0]-t[:,None]*d,axis=1)
        index=int(np.argmax(distances))
        if distances[index]<=tolerance:return p[[0,-1]]
        return np.concatenate((rdp(p[:index+1])[:-1],rdp(p[index:])))
    # Split a closed contour at opposite points so the RDP baseline isn't zero.
    p=np.array(points,dtype=float)
    k=int(np.argmax(np.linalg.norm(p-p[0],axis=1)))
    return np.concatenate((rdp(p[:k+1])[:-1],rdp(np.concatenate((p[k:],p[:1])))[:-1]))


def trace(atlas,index,name,threshold=240):
    raw=atlas.read_bytes()
    root=read_tree(raw)[1][0]
    blob=child(child(child(root,'Texture library'),'HUD_targetingelement'),'MIP0').blob
    image=Image.open(io.BytesIO(blob)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    size=image.width//4
    rgba=np.array(image)[index//4*size:(index//4+1)*size,
                         index%4*size:(index%4+1)*size].astype(float)
    coverage=rgba[:,:,3]*rgba[:,:,:3].max(axis=2)/252.0
    # Trace the bright core only. The atlas's existing soft halo and translucent
    # separator in the quotes must not be baked into an opaque silhouette.
    mask=gaussian_filter(coverage,.75)>=threshold
    edges={}
    for y,x in np.argwhere(mask):
        # Directed pixel boundary; shared edges cancel, leaving outer and hole loops.
        for a,b in (((x,y),(x+1,y)),((x+1,y),(x+1,y+1)),
                    ((x+1,y+1),(x,y+1)),((x,y+1),(x,y))):
            if (b,a) in edges:del edges[(b,a)]
            else:edges[(a,b)]=True
    following={}
    for a,b in edges:following.setdefault(a,[]).append(b)
    loops=[]
    while following:
        start=next(iter(following));p=start;loop=[]
        while True:
            loop.append(p);q=following[p].pop()
            if not following[p]:del following[p]
            p=q
            if p==start:break
        if len(loop)>12:loops.append(simplify(loop,1.25)*256/size)
    vertices,faces=triangulate(loops)
    return {'source':name,'source_file':'ButtonTextures.txm/'+name,
            'sha256':hashlib.sha256(raw).hexdigest(),
            'points':np.array(vertices),'triangles':np.array(faces)}


def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])


def area(loop):return sum(cross(a,b) for a,b in zip(loop,np.roll(loop,-1,axis=0)))/2


def contains(loop,p):
    result=False
    for a,b in zip(loop,np.roll(loop,-1,axis=0)):
        if (a[1]>p[1])!=(b[1]>p[1]):
            if p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result


def triangulate(loops):
    # Bridge each hole to a visible outer vertex, then ear-clip the weakly simple
    # polygon. This keeps original contour vertices instead of hundreds of
    # scanline subdivisions, and never fills the internal details.
    outers=[p for p in loops if area(p)>0]
    holes=[p for p in loops if area(p)<0]
    assigned={i:[] for i in range(len(outers))}
    for hole in holes:
        candidates=[i for i,p in enumerate(outers) if contains(p,hole[0])]
        assert candidates,'Uncontained contour hole'
        assigned[min(candidates,key=lambda i:area(outers[i]))].append(hole)
    vertices=[];faces=[];ids={}
    def vertex(p):
        key=tuple(float(v) for v in p)
        if key not in ids:ids[key]=len(vertices);vertices.append(key)
        return ids[key]
    for index,outer in enumerate(outers):
        polygon=list(outer)
        for hole in assigned[index]:
            hi=int(np.argmax(hole[:,0]));h=hole[hi]
            def visible(v):
                for loop in [polygon]+assigned[index]:
                    for a,b in zip(loop,list(loop[1:])+[loop[0]]):
                        if cross(v-h,a-h)*cross(v-h,b-h)<-1e-8 and cross(b-a,h-a)*cross(b-a,v-a)<-1e-8:return False
                for t in (.25,.5,.75):
                    p=h+(v-h)*t
                    if not contains(outer,p) or any(contains(other,p) for other in assigned[index]):return False
                return True
            candidates=[i for i,v in enumerate(polygon) if visible(v)]
            assert candidates,'Cannot bridge contour hole'
            oi=min(candidates,key=lambda i:np.linalg.norm(polygon[i]-h))
            polygon=polygon[:oi+1]+list(hole[hi:])+list(hole[:hi+1])+[polygon[oi]]+polygon[oi+1:]
        order=[vertex(p) for p in polygon]
        p=np.array(vertices)
        while len(order)>2:
            for i,b in enumerate(order):
                a,c=order[i-1],order[(i+1)%len(order)]
                if cross(p[b]-p[a],p[c]-p[b])<=1e-8:continue
                if any(cross(p[b]-p[a],p[k]-p[a])>=-1e-8 and
                       cross(p[c]-p[b],p[k]-p[b])>=-1e-8 and
                       cross(p[a]-p[c],p[k]-p[c])>=-1e-8
                       for k in order if k not in (a,b,c)):continue
                faces.append((a,b,c));order.pop(i);break
            else:raise ValueError('Cannot triangulate retail contour')
    expected=sum(area(loop) for loop in loops)
    p=np.array(vertices)
    actual=sum(cross(p[b]-p[a],p[c]-p[a])/2 for a,b,c in faces)
    assert abs(expected-actual)<.01,(expected,actual)
    return vertices,faces
