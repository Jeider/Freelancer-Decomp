"""Closed, swept hair locks sharing the head's existing material and skin rig."""
import numpy as np

def add_locks(p,n,pi,uv,ui,uv1,ui1,skin,masks,triangles,level):
    if level>2:return 0
    positions=np.asarray(p);normals=np.asarray(n);candidates=[]
    for t in triangles:
        ids=[pi[v] for v in t];center=positions[ids].mean(axis=0)
        if center[1]<.078 or min(masks[i] for i in ids)<.85:continue
        normal=normals[ids].mean(axis=0);normal/=max(np.linalg.norm(normal),1e-9)
        candidates.append((center,normal,t))
    candidates.sort(key=lambda item:float(np.sin(np.dot(item[0],[1337,1777,2111]))))
    placed=[];limit=(64,32,12)[level];spacing=(.012,.018,.027)[level]
    for center,normal,t in candidates:
        if any(np.linalg.norm(center-other)<spacing for other in placed):continue
        placed.append(center)
        direction=np.array([-.22,.55,-.85]);direction-=normal*np.dot(direction,normal)
        direction/=max(np.linalg.norm(direction),1e-9)
        across=np.cross(direction,normal);across/=max(np.linalg.norm(across),1e-9)
        length=.024; width=.0045
        points=[center-direction*length*.45-across*width-normal*.002,
                center-direction*length*.45+across*width-normal*.002,
                center+across*width*.8-normal*.0015,
                center-across*width*.8-normal*.0015,
                center+normal*.0045,
                center+direction*length*.6+normal*.006]
        texture=np.asarray([uv[ui[v]] for v in t]).mean(axis=0)
        texture1=np.asarray([uv1[ui1[v]] for v in t]).mean(axis=0)
        influences={}
        for v in t:
            for bone,w in skin[pi[v]].items():influences[bone]=influences.get(bone,0)+w/3
        mask=float(np.mean([masks[pi[v]] for v in t]))
        interior=np.mean(points,axis=0)
        for face in ((0,1,4),(1,2,4),(0,4,3),(3,4,5),(4,2,5),(0,3,5),(0,5,1),(1,5,2)):
            a,b,c=[points[i] for i in face];fn=np.cross(b-a,c-a)
            if np.dot(fn,(a+b+c)/3-interior)<0:face=tuple(reversed(face));fn=-fn
            fn/=max(np.linalg.norm(fn),1e-9)
            fn=fn*.65+normal*.35;fn/=max(np.linalg.norm(fn),1e-9)
            corners=[]
            for i in face:
                point=len(p);p.append(points[i].tolist());n.append(fn.tolist());skin.append(dict(influences));masks.append(mask)
                v=len(pi);pi.append(point);corners.append(v)
                offset=np.array([np.dot(points[i]-center,across),np.dot(points[i]-center,direction)])*1.5
                ui.append(len(uv));uv.append((texture+offset).tolist())
                ui1.append(len(uv1));uv1.append(texture1.tolist())
            triangles.append(corners)
        if len(placed)>=limit:break
    return len(placed)
