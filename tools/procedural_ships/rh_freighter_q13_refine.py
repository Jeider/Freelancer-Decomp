"""Q13/03: relief inside existing recesses, shaped belly, flat exhaust faces."""
import json
import sys
from pathlib import Path
import numpy as np
import rh_freighter_q13_form as base

q=base.q
f=base.f
B=base.B
OUT=base.OUT.parent/'q13_03'
RAISED_NECK='--raised-neck' in sys.argv
if RAISED_NECK:OUT=OUT.parent/'q13_04'
OLD_CORE=base.core
SKIN,EDGE,DEEP,MECHANISM=base.SKIN,base.EDGE,base.DEEP,base.MECHANISM
CHECKS={}


def native_reference():
    OUT.mkdir(parents=True,exist_ok=True)
    source=q.SOURCE.parent.parent/'rh_freighter/rh_freighter.cmp'
    _,nodes=f.mesh.read_tree(source.read_bytes());tr,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    local=f.local_geometry(nodes);names=f.component_map(nodes)
    scene=[dict(g,part=names[file]) for file,gs in local.items() for g in f.base.world(gs,*tr[file.lower()])]
    mats=f.audit.material_table([source.parent.parent/'rh_playerships.mat',source.parents[3]/'fx/envmapbasic.mat'])
    pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene]);center=(pts.min(0)+pts.max(0))/2
    radius=np.linalg.norm(pts-center,axis=1).max()*1.03
    for label,cam in [('native_under',(1,-1,-.5)),('native_bottom',(0,-1,.00001))]:
        for mode in ('texture','clay'):
            q.cull_render(scene,mats,center,radius,cam,size=1400,mode=mode).save(OUT/(label+'_'+mode+'.png'))
    # Bottom-facing root surfaces tell modeled steps apart from painted panel lines.
    gs=[g for g in scene if g['part']=='Root'];report=[]
    for g in gs:
        a=g['corners'];n=np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
        a=a[(n[:,1]<-.45)&(a[:,:,1].mean(1)<-1)]
        if len(a):report.append(dict(material=mats[g['material']]['name'],triangles=len(a),min=a[...,:3].min((0,1)).tolist(),max=a[...,:3].max((0,1)).tolist()))
    data=dict(source=str(source),sha256=f.digest(source),bottom_surfaces=report)
    (OUT/'native_bottom_audit.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    print(json.dumps(data,indent=2))


def lower_side(side):
    # Same accepted outline and rim; deepen only the bottom of the existing recess.
    back=np.array([[-6.82,-1.75],[-4.55,-.27],[-3.06,-1.67],[5.84,.42],
                   [7.39,.39],[7.50,-1.55],[6.20,-4.118],[-5.25,-4.118]])
    face=np.array([[-6.45,-1.85],[-4.57,-.65],[-3.09,-2.06],[5.84,.05],
                   [7.06,.03],[7.12,-1.53],[5.99,-3.72],[-5.12,-3.72]])
    inner=np.array([[-5.88,-2.12],[-4.60,-1.15],[-3.16,-2.49],[5.71,-.40],
                   [6.61,-.42],[6.62,-1.58],[5.67,-3.26],[-4.96,-3.26]])
    b=B();a=base.yz(back,side*2.52);c=base.yz(face,side*3.34);d=base.yz(inner,side*3.34)
    e=base.yz(inner,side*2.85)
    base.loops(b,[a,c,d,e],[SKIN,EDGE,DEEP]);b.face(a,SKIN,normal=[-side,0,0]);b.face(e,DEEP,normal=[side,0,0])
    base.add(f'Lower diagonal hull {side:+}',b)
    # The silhouette is defined by the rim. These three different-shaped relief
    # sections sit INSIDE it, with roots buried into the backing instead of floating.
    fields=[
        ('Forward return',[[-5.37,-2.19],[-4.63,-1.53],[-3.46,-2.72],[-3.21,-3.02],[-4.83,-3.02]],3.22),
        ('Central stepped web',[[-2.84,-3.02],[.68,-3.02],[.68,-1.85],[-.58,-2.15],[-1.01,-2.55],[-2.84,-2.77]],3.13),
        ('Aft diagonal web',[[1.04,-3.02],[5.46,-3.02],[6.28,-1.55],[6.24,-.74],[5.63,-.66],
                            [1.04,-1.76],[1.04,-2.12],[1.47,-2.30],[1.47,-2.57],[1.04,-2.72]],3.25)]
    checks=[]
    for label,poly,height in fields:
        poly=np.array(poly,float)
        for a,c in zip(poly,np.roll(poly,-1,axis=0)):
            assert all(q.inside(inner,p) for p in np.linspace(a,c,11)),(label,a,c)
        assert 2.85<height<3.34
        top=base.scaled(poly,.95,.88)
        b=B();rings=[base.yz(poly,side*2.80),base.yz(poly,side*(height-.12)),base.yz(top,side*height)]
        base.loops(b,rings,[SKIN,EDGE]);b.face(rings[0],DEEP,normal=[-side,0,0]);b.face(rings[-1],SKIN,normal=[side,0,0])
        base.add(f'Recess relief {label} {side:+}',b)
        checks.append(dict(name=label,outer_x=height,rim_x=3.34,clearance=round(3.34-height,3),inside_perimeter=True))
    CHECKS[f'side_{side}']=checks


def core():
    # Retain approved foredeck shoulders and engine connections from revision 02.
    start=len(base.OBJECTS);OLD_CORE()
    assert base.OBJECTS[start]['name']=='Continuous inner hull and cockpit neck'
    base.OBJECTS.pop(start)
    # Native rh_freighter uses transverse stepped valleys, not a featureless slab.
    # The new belly has three ramped channels cut into its own skin.
    stations=[(-8.416,1.98,-2.0786,.766,.12),(-7.62,2.40,-2.22,1.38,.26),
        (-4.10,2.72,-3.88,3.81,.37)]
    for z,y in [(-3.60,-3.88),(-3.28,-3.40),(-2.85,-3.40),(-2.50,-3.88),
                (.15,-3.88),(.48,-3.40),(.91,-3.40),(1.26,-3.88),
                (3.88,-3.88),(4.21,-3.40),(4.64,-3.40),(4.99,-3.88),(5.72,-3.88)]:
        stations.append((z,2.72,y,3.81,.37))
    stations.extend([(7.72,2.47,-3.24,2.48,.42),(8.30,2.04,-2.62,1.78,.35)])
    rings=[base.section(*s) for s in stations];b=B()
    for i,(a,c) in enumerate(zip(rings,rings[1:])):
        for j in range(8):
            if i==1 and j==4:continue  # This face receives the two real foredeck ducts.
            k=(j+1)%8;quad=np.array([a[j],a[k],c[k],c[j]])
            n=quad.mean(0)-np.concatenate((a,c)).mean(0)
            mat=DEEP if j==0 and a[0,1]>-3.50 and c[0,1]>-3.50 and i>2 else SKIN
            b.face(quad,mat,normal=n)
    b.face(rings[0],DEEP,normal=[0,0,-1]);b.face(rings[-1],DEEP,normal=[0,0,1])
    # Replace the actual ramp surface, without covering the previous pockets.
    outer=np.array([[-2.14,-7.62],[2.14,-7.62],[2.35,-4.10],[-2.35,-4.10]]) # x,z
    if RAISED_NECK:
        # One short, wide, low rise near the root of the neck. No twin nostrils.
        hole=np.array([[-1.43,-5.90],[1.43,-5.90],[1.60,-5.74],[1.60,-5.00],
                       [1.43,-4.84],[-1.43,-4.84],[-1.60,-5.00],[-1.60,-5.74]])
        holes=[hole]
    else:
        hole=np.array([[.65,-6.95],[1.55,-6.95],[1.81,-6.66],[1.81,-4.71],[.90,-4.71],[.65,-5.01]])
        holes=[hole,hole*np.array([-1,1])]
    points,tris,contours=q.planar_mesh(outer,holes)
    assert len(contours[0])==4
    slope=(3.81-1.38)/(-4.10+7.62)
    def plane(p,depth=0):
        p=np.array(p,float)
        return np.column_stack((p[:,0],1.38+(p[:,1]+7.62)*slope-depth,p[:,1]))
    normal=np.array([0,1,-slope])
    for ids in tris:b.face(plane(points[ids]),SKIN,normal=normal)
    for contour in contours[1:]:
        if RAISED_NECK:
            top=base.scaled(contour,.91,.73)
            a=plane(contour);c=plane(top,-.18)
            b.bridge(a,c,SKIN);b.face(c,SKIN,normal=normal)
        else:
            lower=base.scaled(contour,.78,.90)
            a=plane(contour);c=plane(lower,.32)
            b.bridge(a,c,EDGE,inner=True);b.face(c,DEEP,normal=normal)
    base.add('Continuous hull - stepped belly and '+('low foredeck rise' if RAISED_NECK else 'recessed foredeck'),b)
    # A low central chine reinforces each broad bottom field, with inclined ends.
    # It stops at each channel instead of bridging or concealing the cuts.
    for i,(z0,z1) in enumerate([(-2.35,.04),(1.41,3.77)]):
        poly=np.array([[-.62,z0],[-.92,z0+.30],[-.92,z1-.30],[-.62,z1],
                       [.62,z1],[.92,z1-.30],[.92,z0+.30],[.62,z0]])
        def bottom(p,y):return np.column_stack((p[:,0],np.full(len(p),y),p[:,1]))
        bb=B();a=bottom(poly,-3.80);c=bottom(base.scaled(poly,.70,.83),-4.04)
        bb.bridge(a,c,SKIN);bb.face(a,DEEP,normal=[0,1,0]);bb.face(c,EDGE,normal=[0,-1,0])
        base.add(f'Ventral integrated chine {i+1}',bb)
    CHECKS['belly']=dict(transverse_channels=3,channel_depth=.48,chine_low_y=-4.04,old_lowest_y=-4.118)
    CHECKS['foredeck']=(dict(real_blind_recesses=0,integrated_rises=1,width=3.20,length=1.06,height_vertical=.18,
        z_front=-5.90,z_back=-4.84) if RAISED_NECK else dict(real_blind_recesses=2,depth_vertical=.32))


def engines(side):
    # All accepted external engine sections are unchanged. The exhaust is a flat
    # closed disk inside its existing outer lip; no inner chamber or stator sticks.
    x=side*2.08;y=-.28;angles=(np.arange(16)+.5)*2*np.pi/16
    def ring(z,r):return np.column_stack((x+r*np.cos(angles),y+r*np.sin(angles),np.full(16,z)))
    profile=[(6.82,.98),(7.15,1.36),(7.85,1.78),(8.17,1.86),(10.35,1.86),
        (10.87,1.61),(10.87,1.41),(11.63,1.41),(11.84,1.30),(12.158,1.30),
        (12.158,1.08)]
    rings=[ring(z,r) for z,r in profile];b=B();base.loops(b,rings,
        [MECHANISM,SKIN,EDGE,SKIN,SKIN,EDGE,MECHANISM,EDGE,SKIN,EDGE])
    b.face(rings[0],DEEP,normal=[0,0,-1]);b.face(rings[-1],DEEP,normal=[0,0,1])
    base.add(f'Engine casing - flat exhaust {side:+}',b)
    CHECKS[f'exhaust_{side}']=dict(flat_z=12.158,stator_vanes=0)


def main():
    base.OUT=OUT;base.OBJECTS.clear()
    base.core=core;base.lower_side=lower_side;base.engines=engines
    base.main()
    current=json.loads((OUT/'geometry.json').read_text(encoding='utf8'))
    previous_revision='q13_03' if RAISED_NECK else 'q13_02'
    previous=json.loads((OUT.parent/previous_revision/'geometry.json').read_text(encoding='utf8'))
    assert current['cabin_hash']==previous['cabin_hash']
    old={o['name']:o for o in previous['objects']};preserved=[]
    for o in current['objects']:
        if o['name'] in old and not o['name'].startswith('Lower diagonal'):
            assert o['groups']==old[o['name']]['groups'],o['name']
            preserved.append(o['name'])
    assert not any('stator' in o['name'].lower() for o in current['objects'])
    CHECKS.update(unchanged_objects=preserved,original_cockpit_preserved=True,
                  previous_revision=previous_revision,current_revision=OUT.name,installed=False)
    (OUT/'revision_check.json').write_text(json.dumps(CHECKS,indent=2),encoding='utf8')


if __name__=='__main__':
    if '--audit' in sys.argv:native_reference()
    else:main()
