"""Check the user's actual coplanar flicker locations on decoded revision 08."""
import itertools
import json
import numpy as np
import rh_concept_b_sockets as r


def cross(a,b):return a[0]*b[1]-a[1]*b[0]


def area(p):
    return abs(sum(cross(a,b) for a,b in zip(p,np.roll(p,-1,axis=0))))/2 if len(p)>=3 else 0.


def intersection(a,b):
    poly=list(a.copy());sign=np.sign(cross(b[1]-b[0],b[2]-b[0]))
    for p,q in zip(b,np.roll(b,-1,axis=0)):
        out=[]
        if not poly:break
        for x,y in zip(poly,poly[1:]+poly[:1]):
            dx=sign*cross(q-p,x-p);dy=sign*cross(q-p,y-p)
            if dx>=-1e-9:out.append(x)
            if (dx>=0)!=(dy>=0):out.append(x+(y-x)*dx/(dx-dy))
        poly=out
    return area(np.array(poly))


def horizontal_overlaps(scene,y):
    triangles=[]
    for g in scene:
        for i,t in enumerate(g['corners']):
            if np.all(np.isclose(t[:,1],y,atol=1e-5)):
                q=t[:,[0,2]]
                if area(q)>1e-9:triangles.append((g['part'],i,q))
    hits=[]
    for a,b in itertools.combinations(triangles,2):
        if np.any(a[2].max(0)<b[2].min(0)-1e-6) or np.any(b[2].max(0)<a[2].min(0)-1e-6):continue
        overlap=intersection(a[2],b[2])
        if overlap>1e-6:hits.append(dict(parts=[a[0],b[0]],triangles=[a[1],b[1]],area=overlap))
    return hits


def main():
    _,nodes=r.mesh.read_tree(r.DEST.read_bytes());scene=r.native.evaluate_pose(nodes,0)
    checks=json.loads((r.OUT/'checks.json').read_text())
    floors=horizontal_overlaps(scene,-1.15);lips=horizontal_overlaps(scene,-.16)
    report=dict(cmp_sha256=checks['output_sha256'],floor_overlaps=floors,wing_mount_top_overlaps=lips)
    (r.OUT/'seam_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    assert not floors,'Coplanar bottom overlap'
    assert not lips,'Coplanar wing mount overlap'


if __name__=='__main__':main()
