"""Q13 final offline geometry: native-derived wounds and projection LODs."""
import json,math,sys,copy,faulthandler
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,groups_from_mesh,C
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/rh_pir_freighter'
DATA=json.loads((OUT/'blender_input.json').read_text())
STACK=open(OUT/'blender_stack.txt','w')
faulthandler.dump_traceback_later(25,repeat=True,file=STACK)
DM=DATA['damage_material'];EQ=DATA['equipment_material']

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')

def clear():
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)

def materials(emission=False):
    for key,m in DATA['materials'].items():
        mat=bpy.data.materials.get(key) or bpy.data.materials.new(key);mat.use_nodes=True;mat.use_backface_culling=True
        ns=mat.node_tree.nodes;ns.clear();links=mat.node_tree.links;o=ns.new('ShaderNodeOutputMaterial')
        sh=ns.new('ShaderNodeEmission') if emission else ns.new('ShaderNodeBsdfPrincipled')
        socket=sh.inputs['Color'] if emission else sh.inputs['Base Color']
        if not emission:sh.inputs['Roughness'].default_value=.84
        mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*m['colour'],1)
        if m.get('image_path'):
            tex=ns.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(m['image_path'],check_existing=True)
            links.new(tex.outputs['Color'],mix.inputs[1])
        else:mix.inputs[1].default_value=(1,1,1,1)
        links.new(mix.outputs[0],socket);links.new(sh.outputs[0],o.inputs['Surface'])

def object_from_points(name,verts,faces,mid):
    me=bpy.data.meshes.new(name);me.from_pydata([C@Vector(p) for p in verts],[],faces);me.update()
    me.materials.append(bpy.data.materials[str(mid)]);me.uv_layers.new()
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    return ob

def extruded(name,yz,xlo,xhi,mid,tilt=0,cx=0):
    n=len(yz);verts=[(x,y-tilt*(x-cx),z) for x in (xlo,xhi) for y,z in yz]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return object_from_points(name,verts,faces,mid)

def tube(name,cx,cy,z0,z1,r0,r1,mid,n=12):
    a=np.arange(n)*2*math.pi/n+math.pi/12
    verts=[(cx+r*math.cos(t),cy+r*math.sin(t),z) for z,r in ((z0,r0),(z1,r1)) for t in a]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return object_from_points(name,verts,faces,mid)

def boolean(target,cutter):
    print('BOOLEAN BEGIN',target.name,cutter.name,flush=True)
    # Put semantic material slots in the same order on BOTH operands.
    mids=list(dict.fromkeys([m.name for m in target.data.materials]+[m.name for m in cutter.data.materials]))
    for ob in (target,cutter):
        old=[m.name for m in ob.data.materials];indices=[mids.index(old[p.material_index]) for p in ob.data.polygons]
        ob.data.materials.clear()
        for m in mids:ob.data.materials.append(bpy.data.materials[m])
        for p,i in zip(ob.data.polygons,indices):p.material_index=i
    bpy.context.view_layer.objects.active=target
    mod=target.modifiers.new('Authored fracture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    assert len(target.data.polygons)>0
    print('BOOLEAN END',target.name,len(target.data.polygons),flush=True)

def remap_damage(ob):
    uv=ob.data.uv_layers.active
    xyz=np.array([C.transposed()@v.co for v in ob.data.vertices]);lo=xyz.min(0);span=np.maximum(np.ptp(xyz,axis=0),1e-5)
    for p in ob.data.polygons:
        mid=int(ob.data.materials[p.material_index].name)
        if mid not in (DM,EQ):continue
        normal=C.transposed()@p.normal;axes=sorted(range(3),key=lambda a:abs(normal[a]))[:2]
        for li in p.loop_indices:
            co=C.transposed()@ob.data.vertices[ob.data.loops[li].vertex_index].co
            if mid==EQ:u,v=.26+co[axes[0]]*.16,.26+co[axes[1]]*.16
            else:u,v=co[axes[0]]*.32,.46+.39*(co[axes[1]]-lo[axes[1]])/span[axes[1]]
            uv.data[li].uv=(u,1-v)

def topology(ob):
    bm=bmesh.new();bm.from_mesh(ob.data)
    # Explicit closed pieces may touch along an edge. Count before recalculation.
    report=dict(vertices=len(bm.verts),faces=len(bm.faces),boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();return report

def conform(ob):
    """Reconnect the T-junctions introduced by clipping native atlas charts."""
    ob.data.validate(verbose=False,clean_customdata=False)
    bm=bmesh.new();bm.from_mesh(ob.data)
    splits=0
    for _ in range(4000):
        boundary=[e for e in bm.edges if e.is_boundary];vertices=list({v for e in boundary for v in e.verts});candidate=None
        kd=KDTree(len(vertices))
        for index,v in enumerate(vertices):kd.insert(v.co,index)
        kd.balance()
        for e in boundary:
            a,b=e.verts;delta=b.co-a.co;length=delta.length_squared
            if length<1e-12:continue
            for _,index,_ in kd.find_range((a.co+b.co)*.5,math.sqrt(length)*.50005):
                v=vertices[index]
                if v in e.verts or any(v in face.verts for face in e.link_faces):continue
                t=(v.co-a.co).dot(delta)/length
                if 1e-5<t<1-1e-5 and (a.co+delta*t-v.co).length<3e-5:
                    candidate=e,a,v,t;break
            if candidate:break
        if candidate is None:break
        e,a,v,t=candidate
        _,new=bmesh.utils.edge_split(e,a,t);new.co=v.co.copy()
        bmesh.ops.weld_verts(bm,targetmap={new:v});splits+=1
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
    return splits

def damage():
    clear();materials();entries={o['name']:o for o in DATA['objects']};out={};stats={}
    for side,label in [(-1,'port'),(1,'starboard')]:
        part='port_engine_lod1' if side<0 else 'starboard_engine_lod1'
        ob,_=mesh_object(entries[part],label+'_engine_survivor');cx=side*1.8
        print('ENGINE SOURCE',label,conform(ob),topology(ob),flush=True)
        # Keep our rising support and shoulder. Bore the original main barrel;
        # tear away its upper/outboard half along a jagged longitudinal fracture.
        boolean(ob,tube('cavity',cx,-.28,9.68,13.0,.79,.64,EQ))
        yz=[(5,9.82),(.45,9.82),(.12,10.12),(.26,10.39),(-.09,10.78),
            (.05,11.04),(-.25,11.38),(-.07,11.64),(-.22,12.45),(5,12.45)]
        boolean(ob,extruded('longitudinal torn half',yz,cx-3,cx+3,DM,tilt=side*.25,cx=cx))
        remap_damage(ob);stat=topology(ob);assert stat['boundary_edges']==0,stat
        groups=groups_from_mesh(ob.data,[int(m.name) for m in ob.data.materials])
        # Short substantial inner core, seated in the surviving shoulder.
        core=tube('broken inner core',cx,-.44,9.62,10.78,.39,.26,EQ,8);remap_damage(core)
        groups+=groups_from_mesh(core.data,[EQ]);bpy.data.objects.remove(core,do_unlink=True)
        out[label+'_engine']=groups;stats[label+'_engine']=dict(topology=stat,method='Intact Q13 shell, internal bore, jagged longitudinal half removed; original support preserved')
        bpy.data.objects.remove(ob,do_unlink=True)
        part='rh_port_side_lod1' if side<0 else 'rh_star_side_lod1'
        ob,_=mesh_object(entries[part],label+'_panel_survivor')
        print('PANEL SOURCE',label,conform(ob),topology(ob),flush=True)
        # Rear half of the panel tears off. Leave the front intake and a stepped,
        # slanted fracture, not an intact flat plate beneath a missing panel.
        yz=[(-4,-.2),(-1.7,-.2),(-.9,.40),(-.35,.18),(.35,.9),(.9,.58),
            (1.45,1.30),(2.,1.00),(2.55,1.9),(3.15,1.5),(4.5,2.45),(6,2.45),(6,15),(-4,15)]
        boolean(ob,extruded('rear torn panel half',yz,-8,8,DM));remap_damage(ob);stat=topology(ob)
        groups=groups_from_mesh(ob.data,[int(m.name) for m in ob.data.materials]);out[label+'_side_panel']=groups
        # A wrecked inner sheet covers the intact core only where the outer
        # panel has torn away. Both sides are closed, so no see-through plate.
        yz=[(.48,.55),(3.52,.55),(3.52,5.48),(2.38,7.10),(1.02,7.10),(.82,5.74)]
        backing=extruded('exposed inner panel machinery',yz,min(side*2.94,side*3.08),max(side*2.94,side*3.08),EQ)
        uv=backing.data.uv_layers.active
        for p in backing.data.polygons:
            for li in p.loop_indices:
                co=C.transposed()@backing.data.vertices[backing.data.loops[li].vertex_index].co
                uv.data[li].uv=(.025+(co.z-.55)/6.55*.95,1-(.025+(co.y-.48)/3.04*.45))
        groups+=groups_from_mesh(backing.data,[EQ]);bpy.data.objects.remove(backing,do_unlink=True)
        stats[label+'_side_panel']=dict(topology=stat,method='Our original panel clipped along a jagged diagonal; machinery backing added separately at actual original pockets')
        bpy.data.objects.remove(ob,do_unlink=True)
    dump('damage_world.json',out);dump('damage_geometry_check.json',stats)
    print('DAMAGE GEOMETRY READY',stats,flush=True)

def lods():
    clear();materials(True);scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
    scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.render.dither_intensity=0
    camera=bpy.data.objects.new('Projection camera',bpy.data.cameras.new('Projection lens'));scene.collection.objects.link(camera)
    scene.camera=camera;camera.data.type='ORTHO';camera.data.clip_end=200
    directions=[((1,0,0),(0,0,-1),(0,1,0)),((-1,0,0),(0,0,1),(0,1,0)),
        ((0,1,0),(1,0,0),(0,0,-1)),((0,-1,0),(1,0,0),(0,0,1)),
        ((0,0,1),(1,0,0),(0,1,0)),((0,0,-1),(-1,0,0),(0,1,0))]
    photos=OUT/'photos';photos.mkdir(exist_ok=True);projectors={};levels=[{},{}];stats=[];tile=0
    for entry in DATA['objects']:
        name=entry['name'];ob,slots=mesh_object(entry,name)
        ob.data.validate(verbose=False,clean_customdata=False)
        if name in ('glass_lod1','Baydoor_lod1'):
            for lv in levels:lv[name]=entry['groups']
            bpy.data.objects.remove(ob,do_unlink=True);continue
        p=np.array([C.transposed()@v.co for v in ob.data.vertices]);center=(p.min(0)+p.max(0))/2
        projectors[name]=[]
        for normal,u,v in directions:
            normal,u,v=map(np.array,(normal,u,v));scale=max(np.ptp(p@u),np.ptp(p@v))*1.06
            camera.location=C@Vector(center+normal*60);camera.rotation_euler=(C@Matrix(np.column_stack((u,v,normal)).tolist())).to_euler();camera.data.ortho_scale=float(scale)
            image=name+'_'+str(len(projectors[name]))+'.png';scene.render.filepath=str(photos/image)
            if not (photos/image).exists():bpy.ops.render.render(write_still=True)
            projectors[name].append(dict(center=center,u=u,v=v,normal=normal,scale=scale,tile=[tile%8,tile//8],image='photos/'+image));tile+=1
        # Remove UV-only coplanar subdivision before distance simplification.
        if name=='Root':
            bpy.data.objects.remove(ob,do_unlink=True)
            ob,slots=mesh_object(dict(groups=DATA['lod_root_working']),name)
            ob.data.validate(verbose=False,clean_customdata=False)
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.dissolve_limit(bm,angle_limit=.002,use_dissolve_boundaries=False,verts=list(bm.verts),edges=list(bm.edges),delimit=set())
        bm.to_mesh(ob.data);bm.free()
        # Coplanar UV clipping accounts for most of the near mesh count.
        # Preserve that authored form in LOD1. LOD2 is built separately below:
        # collapsing recess walls tears their distinct projection charts.
        for level,ratio in enumerate((1.0,)):
            if 'engine' in name:ratio=max(ratio,.65)
            if '_btn_' in name:ratio=max(ratio,.60)
            mod=ob.modifiers.new('Distant silhouette','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
            ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();gs=groups_from_mesh(me,slots);ev.to_mesh_clear();ob.modifiers.remove(mod)
            mapped=[]
            for g in gs:
                for t in np.array(g['corners']):
                    n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=np.linalg.norm(n)
                    proj=max(projectors[name],key=lambda a:n@a['normal']);co=t[:,:3]-proj['center'];tx,ty=proj['tile']
                    t[:,6]=(tx+co@proj['u']/proj['scale']+.5)/8;t[:,7]=(ty+.5-co@proj['v']/proj['scale'])/8;mapped.append(t)
            levels[level][name]=[dict(material=0,corners=np.array(mapped),unused=204)]
            if name=='Root':levels[level][name]+=DATA['preserved_cockpit']
            stats.append(dict(part=name,level=level+1,triangles=len(mapped)))
        bpy.data.objects.remove(ob,do_unlink=True);print('PHOTOGRAPHED AND REDUCED',name,flush=True)
    assert tile<=64
    dump('projectors.json',projectors)
    # LOD2 is a dedicated structural proxy. Further collapsing the detailed
    # LOD1 left thousands of hidden/recess triangles and a full-density shutter.
    import rh_freighter_far_lod_blender as far
    far.main()
    levels[1]=json.loads((far.OUT/'far_world.json').read_text())
    stats=[dict(part=name,level=i+1,triangles=sum(len(g['corners']) for g in gs))
           for i,lv in enumerate(levels) for name,gs in lv.items()]
    dump('lod_world.json',levels);dump('lod_generation.json',dict(parts=stats,photos=tile,total=[sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in levels]))

if __name__=='__main__':
    if '--damage' in sys.argv:damage()
    if '--lods' in sys.argv:lods()
