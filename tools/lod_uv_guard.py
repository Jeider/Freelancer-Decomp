"""Topology/UV-island validation against the authored near mesh."""
import collections
import math
import struct as S


def uv(v):return S.unpack_from('<2f',v,24)
def point(v):return S.unpack_from('<3f',v)
def area2(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def density(face):
    a,b,c=[point(v) for v in face]
    x=[b[k]-a[k] for k in range(3)];y=[c[k]-a[k] for k in range(3)]
    cross=(x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0])
    world=math.sqrt(sum(x*x for x in cross))
    return abs(area2(*(uv(v) for v in face)))/world if world>1.e-12 else None


class UvGuard:
    @staticmethod
    def face_key(material,face):
        return (material,min(tuple(face),tuple(face[1:]+face[:1]),tuple(face[2:]+face[:2])))

    def __init__(self,descriptors,groups):
        parent=[];edges={};faces=[]
        def find(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for (material,_,_),cs in zip(descriptors,groups):
            for t in range(0,len(cs),3):
                face=cs[t:t+3];i=len(parent);parent.append(i);faces.append((material,face))
                keys=[point(v)+uv(v) for v in face]
                for k in range(3):
                    edge=(material,tuple(sorted((keys[k],keys[(k+1)%3]))))
                    if edge in edges:parent[find(i)]=find(edges[edge])
                    else:edges[edge]=i
        self.membership=collections.defaultdict(set)
        self.original_faces=set()
        self.uv_faces=collections.defaultdict(list)
        self.densities=collections.defaultdict(list)
        self.signs=collections.defaultdict(set)
        for i,(material,face) in enumerate(faces):
            self.original_faces.add(self.face_key(material,face))
            chart=find(i)
            for v in face:self.membership[(material,v)].add(chart)
            coords=[uv(v) for v in face];area=area2(*coords)
            if abs(area)>1.e-12:
                self.uv_faces[chart].append(coords);self.signs[chart].add(1 if area>0 else -1)
            d=density(face)
            if d is not None and d>1.e-12:self.densities[chart].append(d)
        self.ranges={k:(min(v),max(v)) for k,v in self.densities.items()}

    @staticmethod
    def inside(p,tri):
        a,b,c=tri;det=area2(a,b,c)
        if abs(det)<1.e-12:return False
        w0=area2(p,b,c)/det;w1=area2(a,p,c)/det;w2=1-w0-w1
        return min(w0,w1,w2)>=-1.e-5

    def issue(self,material,face):
        if self.face_key(material,face) in self.original_faces:return None
        sets=[self.membership.get((material,v),set()) for v in face]
        common=set.intersection(*sets)
        if not common:return 'crossed_uv_islands'
        coords=[uv(v) for v in face];area=area2(*coords);d=density(face)
        for chart in common:
            if len(self.signs[chart])==1 and area!=0 and (1 if area>0 else -1) not in self.signs[chart]:continue
            if chart in self.ranges:
                lo,hi=self.ranges[chart]
                if d is None or not lo*.8<=d<=hi*1.25:continue
            triangles=self.uv_faces[chart]
            if not triangles:return None
            samples=[tuple(sum(p[k] for p in coords)/3 for k in range(2))]
            samples += [tuple((coords[i][k]+coords[(i+1)%3][k])*.5 for k in range(2)) for i in range(3)]
            if all(any(self.inside(p,t) for t in triangles) for p in samples):return None
        return 'uv_orientation_density_or_coverage'

    def issues(self,material,corners):
        return collections.Counter(x for i in range(0,len(corners),3) if (x:=self.issue(material,corners[i:i+3])))
