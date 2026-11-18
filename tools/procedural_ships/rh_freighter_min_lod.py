"""Authored ~500-triangle far silhouette; reuse the approved projection atlas."""
import itertools,json,math
import numpy as np
from scipy.spatial import ConvexHull
import rh_freighter_final as d
from rh_freighter_uv_b3 import UP_BACK,UP_FACE
f=d.f;B=d.q.B;OUT=d.OUT/'lod_refinement'
PROJ=d.read('projectors.json')


def roof_dividers():
    """Static extended HUD lines, not the triangle edges of a render LOD."""
    result=[]
    for theta in np.deg2rad([-75,-25,25,75]):
        cross=[[-2.32,4.51],[-2.15,4.65],[-1.96,4.65],[-1.82,4.51],
               [1.82,4.51],[1.96,4.65],[2.15,4.65],[2.32,4.51]]
        pts=np.array([[x,2.434951+r*np.cos(theta),.939292+r*np.sin(theta)] for x,r in cross])
        result.extend(np.stack((pts[:-1],pts[1:]),axis=1))
    cfg=json.loads((d.PREVIOUS/'cornice_symmetry.json').read_text())
    z=cfg['front']['top_z'][1];w=cfg['front']['rear_width']/2
    for zz in (z,2*cfg['plane_z']-z):result.append([[-w,2.8,zz],[w,2.8,zz]])
    return np.array(result)


def project(groups,owner,canopy=False):
    ts=[]
    for g in groups:
        for t in np.array(g['corners'],float):
            n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=np.linalg.norm(n)
            views=[p for p in PROJ[owner] if not canopy or abs(p['normal'][1])<.1]
            p=max(views,key=lambda p:n@p['normal']);co=t[:,:3]-p['center'];tx,ty=p['tile']
            t[:,6]=(tx+co@p['u']/p['scale']+.5)/8;t[:,7]=(ty+.5-co@p['v']/p['scale'])/8
            ts.append(t)
    return [dict(material=0,corners=np.array(ts),unused=204)]


def loft(rings,caps=True):
    b=B()
    for a,c in zip(rings,rings[1:]):b.bridge(a,c,0)
    if caps:
        center=np.concatenate(rings).mean(0)
        for r in (rings[0],rings[-1]):b.face(r,0,normal=r.mean(0)-center)
    return b.groups()


def prism(poly,x0,x1):
    b=B();a=b.yz(poly,x0);c=b.yz(poly,x1);b.bridge(a,c,0)
    b.face(a,0,normal=[-1,0,0]);b.face(c,0,normal=[1,0,0]);return b.groups()


def body():
    # Large flat belly, tapered neck/stern. The top between the shoulders
    # remains open, with one floor and four walls for the cargo mechanism.
    sections=[(-8.416,1.98,-2.079,.766),(-4.1,3.2,-4.0,3.81),
              (5.72,3.2,-4.0,3.81),(8.30,2.04,-2.62,1.78)]
    rings=[np.array([[-w,bot,z],[w,bot,z],[w,top,z],[-w,top,z]]) for z,w,bot,top in sections]
    b=B()
    for i,(a,c) in enumerate(zip(rings,rings[1:])):
        for j in range(4):
            if i==1 and j==2:continue
            ps=np.array([a[j],a[(j+1)%4],c[(j+1)%4],c[j]])
            normal=[0,-1,0] if j==0 else [1,0,0] if j==1 else [0,1,0] if j==2 else [-1,0,0]
            b.face(ps,0,normal=normal)
    b.face(rings[0],0,normal=[0,0,-1]);b.face(rings[-1],0,normal=[0,0,1])
    a,c=rings[1],rings[2];floor=np.array([[-3.2,.36,-4.1],[3.2,.36,-4.1],[3.2,.36,5.72],[-3.2,.36,5.72]])
    b.face(floor,0,normal=[0,1,0])
    rim=np.array([a[3],a[2],c[2],c[3]])
    for j in range(4):
        ps=np.array([rim[j],rim[(j+1)%4],floor[(j+1)%4],floor[j]])
        n=floor.mean(0)-ps.mean(0);n[1]=0;b.face(ps,0,normal=n)
    return b.groups()


def cornices():
    cfg=json.loads((d.PREVIOUS/'cornice_symmetry.json').read_text());p=cfg['front'];result=[]
    z0,z1=p['top_z'];w0=p['tip_width']/2;w1=p['rear_width']/2
    # One slab each. Painted fascia supplies all small trim and recesses.
    for flip in (False,True):
        rings=[np.array([[-w,2.35,z],[w,2.35,z],[w,2.8,z],[-w,2.8,z]]) for w,z in ((w0,z0),(w1,z1))]
        gs=loft(rings)
        if flip:
            for g in gs:
                g['corners']=g['corners'][:,::-1].copy();g['corners'][:,:,2]=2*cfg['plane_z']-g['corners'][:,:,2];g['corners'][:,:,5]*=-1
        result+=gs
    return result


def cockpit():
    # Only the DISTANT cabin is replaced. Select support vertices from its
    # actual silhouette, then assign canopy-facing hull planes to glass.
    data=d.read('blender_input.json');p=d.points(data['preserved_cockpit'])
    dirs=np.array([v for v in itertools.product((-1,0,1),repeat=3) if any(v)])
    ps=np.unique(p[np.argmax(p@dirs.T,axis=0)].round(6),axis=0);h=ConvexHull(ps)
    shell=B();glass=B();mid=next(o for o in data['objects'] if o['name']=='glass_lod1')['groups'][0]['material']
    for ids,eq in zip(h.simplices,h.equations):
        pts=ps[ids];normal=eq[:3];center=pts.mean(0)
        glazing=center[1]>-1.4 and center[2]<-8.7 and (normal[2]<-.25 or abs(normal[0])>.45)
        (glass if glazing else shell).face(pts,mid if glazing else 0,normal=normal)
    assert glass.groups()
    return shell.groups(),glass.groups()


def engine(side):
    n=6;theta=np.arange(n)*2*np.pi/n+np.pi/6
    rings=[np.column_stack((side*1.80+w*np.cos(theta),-.28+h*np.sin(theta),np.full(n,z)))
           for z,w,h in ((9.48,1.2,1.15),(11.18,1.29,1.24),(12.158,.98,.94))]
    pod=loft(rings)
    mount=[np.array([[side*1.8-.38,y-.38,z],[side*1.8+.38,y-.38,z],
                    [side*1.8+.38,y+.38,z],[side*1.8-.38,y+.38,z]]) for y,z in ((-.9,8.30),(-.28,9.50))]
    return loft(mount)+pod


def buttons(side,ids):
    result=[];theta=np.arange(4)*np.pi/2+np.pi/4
    for i in ids:
        z={1:-2.76,2:.66,3:3.94}[i];r=1.12 if i==2 else .73;end=4.70 if i==2 else 4.19
        rings=[np.column_stack((np.full(4,side*x),2.08+r*np.cos(theta),z+r*np.sin(theta))) for x in (2.91,end)]
        result+=loft(rings)
    return result


def main():
    medium=json.loads((OUT/'far_world.json').read_text());root=body()+cornices()
    for side in (-1,1):
        theta=np.linspace(-np.pi/2,np.pi/2,9)
        poly=np.column_stack((.939292+4.909*np.sin(theta),2.434951+4.909*np.cos(theta)))
        root+=prism(poly,*sorted((side*2.35,side*2.93)))
    shell,glass=cockpit();root+=shell
    # On this distant proxy the photographed framing/windows convey the
    # canopy, avoiding a solid-colour glass triangle across the entire nose.
    out={'Root':project(root,'Root'),'glass_lod1':project(glass,'Root',canopy=True),'Baydoor_lod1':medium['Baydoor_lod1']}
    for side,label in ((-1,'port'),(1,'star')):
        name='rh_'+label+'_side_lod1'
        # Keep the accepted simple concave panel outline from the 1776-tri LOD.
        out[name]=medium[name]
        for size,ids in (('big',[2]),('sml',[1,3])):
            name='rh_'+label+'_'+size+'_btn_lod1';out[name]=project(buttons(side,ids),name)
        name=('port' if side<0 else 'starboard')+'_engine_lod1';out[name]=project(engine(side),name)
    count={name:sum(len(g['corners']) for g in gs) for name,gs in out.items()}
    assert sum(count.values())<=500,count
    assert set(out)==set(medium)
    d.dump(OUT/'minimum_world.json',out)
    d.dump(OUT/'minimum_geometry.json',dict(parts=count,total=sum(count.values()),flat_belly=True,atlas_unchanged=True))
    print('MINIMUM',count,'TOTAL',sum(count.values()))


if __name__=='__main__':main()
