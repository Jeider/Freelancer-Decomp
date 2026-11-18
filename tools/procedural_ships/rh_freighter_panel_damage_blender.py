"""Authored torn sheet metal for Q13, inspired by native rh_freighter damage."""
import json, math, sys, hashlib
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_freighter_final_blender as g
OUT=g.OUT
PALE=4138378680

def bvh(ob):
    return BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])

def ribbon(name,side,rows,width_axis,thickness=.055):
    """Folded tapered sheet; connected root, dark reverse, closed torn edge."""
    centers=np.array([r[:3] for r in rows],float);widths=np.array([r[3] for r in rows]);axis=np.array(width_axis,float)
    verts=[];uvs=[]
    length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(centers,axis=0),axis=1))];length/=length[-1]
    for j,(center,width) in enumerate(zip(centers,widths)):
        tangent=centers[min(j+1,len(rows)-1)]-centers[max(j-1,0)]
        w=axis-axis.dot(tangent)*tangent/tangent.dot(tangent);w/=np.linalg.norm(w)
        n=np.cross(w,tangent);n/=np.linalg.norm(n)
        # Change twist along the fractured strip rather than extruding a box.
        angle=math.radians(rows[j][4] if len(rows[j])>4 else 0)
        w,n=w*math.cos(angle)+n*math.sin(angle),n*math.cos(angle)-w*math.sin(angle)
        for depth in (-1,1):
            for edge in (-1,1):
                p=center+w*width*.5*edge+n*thickness*.5*depth;p[0]*=side
                verts.append(p);uvs.append((.57+(edge+1)*.17,.30+length[j]*.14))
    faces=[];kinds=[]
    for j in range(len(rows)-1):
        a=j*4;b=a+4
        faces.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)])
        kinds.extend([g.DM,PALE,g.DM,g.DM])
    faces.extend([(0,2,3,1),(len(verts)-4,len(verts)-3,len(verts)-1,len(verts)-2)]);kinds.extend([g.DM,g.DM])
    ob=g.object_from_points(name,verts,faces,PALE)
    ob.data.materials.append(bpy.data.materials[str(g.DM)])
    uv=ob.data.uv_layers.active
    for p,kind in zip(ob.data.polygons,kinds):
        p.material_index=0 if kind==PALE else 1
        for li in p.loop_indices:
            vi=ob.data.loops[li].vertex_index;u,v=uvs[vi]
            if kind==g.DM:u,v=.1+(vi%2)*.6,.36+.48*length[vi//4]
            uv.data[li].uv=(u,1-v)
    stat=g.topology(ob);assert stat['nonmanifold_edges']==0,(name,stat)
    return ob,stat

def backing(side,deep=False):
    # A folded machinery bed replaces the rejected perfectly flat rectangle.
    zs=[.55,1.8,3.1,4.5,5.7,7.1]
    lows=[.48,.48,.48,.55,.8,1.02];highs=[3.52,3.52,3.52,3.52,3.24,2.38]
    bumps=np.array([[0,.10,.04,.20,.08,0],[.1,.55,.18,.70,.25,.10],[.05,.25,.68,.28,.60,.12],[0,.20,.06,.10,.1,0]])
    if side>0:bumps=bumps*.8+np.array([0,.04,-.02,.07,0,0])
    verts=[]
    for rear in (False,True):
        for iy in range(4):
            for iz,z in enumerate(zs):
                x=(1.20 if rear else 1.40+bumps[iy,iz]*.7) if deep else (2.94 if rear else 3.08+bumps[iy,iz])
                verts.append((side*x,lows[iz]+(highs[iz]-lows[iz])*iy/3,z))
    faces=[]
    for iy in range(3):
        for iz in range(5):
            a=iy*6+iz
            for offset in (0,24):
                faces.extend([(a+offset,a+1+offset,a+7+offset),(a+offset,a+7+offset,a+6+offset)])
    perimeter=list(range(6))+[11,17,23]+list(range(22,17,-1))+[12,6]
    for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):faces.append((a,b,b+24,a+24))
    ob=g.object_from_points('Warped exposed inner structure',verts,faces,g.EQ)
    for p in ob.data.polygons:
        for li in p.loop_indices:
            co=g.C.transposed()@ob.data.vertices[ob.data.loops[li].vertex_index].co
            ob.data.uv_layers.active.data[li].uv=(.025+(co.z-.55)/6.55*.95,1-(.025+(co.y-.48)/3.04*.45))
    stat=g.topology(ob);assert stat['nonmanifold_edges']==0,stat
    return ob,stat

def author(deep=False):
    g.clear();g.materials();baseline=json.loads((OUT/'panel_damage/before.json').read_text())['damage'];out=json.loads((OUT/'damage_world.json').read_text());report={}
    for side,label in ((-1,'port'),(1,'starboard')):
        zone=label+'_side_panel';old=baseline[zone]
        # The last group is the old flat backing, authored separately in v1.
        assert old[-1]['material']==g.EQ
        ob,_=g.mesh_object(dict(groups=old[:-1]),'Torn original Q13 '+label)
        g.conform(ob)
        # Curl the actual surviving edge; UVs remain attached to the metal.
        ys=np.array([-.9,-.35,.35,.9,1.45,2.,2.55,3.15,4.5])
        zs=np.array([.40,.18,.9,.58,1.3,1.,1.9,1.5,2.45])
        moved=0
        for v in ob.data.vertices:
            p=np.array(g.C.transposed()@v.co);cut=np.interp(p[1],ys,zs)
            a=max(0.,1-abs(p[2]-cut)/.75)*max(0.,min(1.,(abs(p[0])-2.65)/.70))
            if a:
                p[0]+=side*a*(.27+.26*math.sin(p[1]*4.8+.7));p[1]+=a*.14*math.cos(p[1]*5.1);p[2]+=a*.12
                v.co=g.C@Vector(p);moved+=1
        stat=g.topology(ob);assert stat['nonmanifold_edges']==0,stat
        attachment_surfaces=[bvh(ob)]
        groups=g.groups_from_mesh(ob.data,[int(m.name) for m in ob.data.materials]);bpy.data.objects.remove(ob,do_unlink=True)
        substats=[dict(name='Curled surviving panel',**stat)]
        plate,stat=backing(side,deep);attachment_surfaces.append(bvh(plate));groups+=g.groups_from_mesh(plate.data,[g.EQ]);bpy.data.objects.remove(plate,do_unlink=True);substats.append(dict(name='Folded machinery bed',**stat))
        # Authored roots sit in surviving sheet/inner structure. Wide strips
        # pull the silhouette up, down, outwards and aft; tips vary in width
        # and twist. No floating spikes and no copied native damaged geometry.
        shapes=[
            ('Upper torn frame',[(3.18,3.55,1.05,.37,0),(3.52,3.64,1.72,.36,4),(4.12,4.25,2.35,.31,35),(4.62,4.08,2.82,.11,55)],(0,1,0)),
            ('Wide folded skin',[(3.24,2.78,.90,.85,0),(3.64,2.90,1.65,.94,10),(4.48,3.38,2.27,.75,-22),(4.77,3.12,3.08,.26,-40)],(0,1,0)),
            ('Middle split lip',[(3.18,1.87,.53,.55,0),(3.61,1.73,1.18,.61,-8),(4.11,1.15,1.83,.45,-34),(4.33,1.28,2.28,.17,-55)],(0,1,0)),
            ('Lower peeled skin',[(3.18,.72,.12,.58,0),(3.62,.60,.78,.64,4),(4.30,-.05,1.30,.48,45),(4.19,-.42,1.85,.13,65)],(0,1,0)),
            ('Upper rear tear',[(3.08,3.42,4.30,.62,0),(3.48,3.62,4.48,.58,-12),(3.95,4.30,4.66,.39,-42),(4.04,4.51,4.96,.12,-50)],(0,0,1)),
            ('Rear folded plate',[(3.05,2.18,6.78,.72,0),(3.45,2.34,6.98,.78,12),(4.03,2.68,7.57,.54,30),(4.18,2.41,7.87,.22,50)],(0,1,0)),
            ('Lower rear tear',[(3.06,1.02,5.90,.56,0),(3.43,.94,6.08,.59,10),(3.95,.20,6.31,.38,40),(4.12,.05,6.70,.11,60)],(0,0,1)),
        ]
        for i,(name,rows,axis) in enumerate(shapes):
            if deep and i>=2:
                rows=[list(r) for r in rows]
                rows[0][0]=1.52;rows[1][0]=2.20
                rows[0][2]=max(.70,rows[0][2])
            if side>0:
                rows=[list(r) for r in rows]
                for j in range(1,len(rows)):
                    rows[j][1]+=(.09 if i%2 else -.08)*j;rows[j][2]+=.035*j*(1 if i%2 else -1)
            root=g.C@Vector((side*rows[0][0],rows[0][1],rows[0][2]))
            hits=[surface.find_nearest(root) for surface in attachment_surfaces]
            hit=min((h for h in hits if h[0] is not None),key=lambda h:h[3])
            assert hit[3]<.45,(name,'root too far from the actual panel',hit[3])
            actual=g.C.transposed()@(hit[0]-hit[1]*.018)
            rows=[list(r) for r in rows];rows[0][:3]=[side*actual.x,actual.y,actual.z]
            fragment,stat=ribbon(name,side,rows,axis)
            stat['root_attachment_adjustment']=hit[3]
            stat['attachment_intersections']=sum(len(surface.overlap(bvh(fragment))) for surface in attachment_surfaces)
            print('ATTACHMENT',label,name,stat['attachment_intersections'],flush=True)
            assert stat['attachment_intersections']>0,(label,name,'unattached torn sheet')
            groups+=g.groups_from_mesh(fragment.data,[PALE,g.DM]);substats.append(dict(name=name,**stat))
            bpy.data.objects.remove(fragment,do_unlink=True)
        out[zone]=groups;report[zone]=dict(curled_vertices=moved,pieces=substats,triangles=sum(len(a['corners']) for a in groups),native_reference='references/panel_damage/source.json')
    g.dump('damage_world.json',out);g.dump('panel_damage/geometry_check.json',report)
    # Keep the old engine proof and replace panel proof with this complete set.
    stats=json.loads((OUT/'damage_geometry_check.json').read_text())
    for zone,r in report.items():stats[zone]=dict(topology={k:sum(p[k] for p in r['pieces']) for k in ('vertices','faces','boundary_edges','nonmanifold_edges')},method='Curled original edge, seven connected folded sheet fragments, warped inner machinery; native rh_freighter reference')
    g.dump('damage_geometry_check.json',stats)
    print('TORN PANEL GEOMETRY READY',[(k,v['triangles']) for k,v in report.items()],flush=True)

def review_blend():
    path=OUT/'rh_pir_freighter.blend';check=json.loads((OUT/'blend_check.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==check['sha256'],'User changed review blend'
    bpy.ops.wm.open_mainfile(filepath=str(path));col=bpy.data.collections['Damage / static flight assembly']
    actual=json.loads((OUT/'review/extra_geometry.json').read_text())['damage']
    for e in actual:
        if 'side_panel' not in e['zone']:continue
        old=bpy.data.objects['Damaged '+e['zone']];bpy.data.objects.remove(old,do_unlink=True)
        ob,_=g.mesh_object(e,'Damaged '+e['zone'])
        for owner in list(ob.users_collection):owner.objects.unlink(ob)
        col.objects.link(ob)
    bpy.context.preferences.filepaths.save_version=0;bpy.context.preferences.filepaths.file_preview_type='NONE'
    bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
    assert 'Damage / static flight assembly' in bpy.data.collections
    for name in check['hidden_collections']:assert bpy.data.collections[name].hide_viewport and bpy.data.collections[name].hide_render
    check['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();check['panel_damage_revision']='folded sheet and deformed inner bed'
    g.dump('blend_check.json',check)
    print('UPDATED ONLY DAMAGE PANEL MESHES IN REVIEW BLEND',flush=True)

if __name__=='__main__':
    if '--author' in sys.argv:author()
    if '--review' in sys.argv:review_blend()
