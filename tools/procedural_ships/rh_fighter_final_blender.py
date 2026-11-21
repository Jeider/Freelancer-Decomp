"""Offline projection photography, LOD1, torn surviving fighter pieces."""
import sys,json,math,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
from rh_concept_b_final_blender import mesh_object,groups_from_mesh,C
OUT=HERE.parents[1]/'out/ship_design/rh_fighter/rh_pir_fighter'
DATA=json.loads((OUT/'blender_input.json').read_text(encoding='utf8'))
DM=DATA['damage_material'];EQ=DATA['equipment_material']

def shifted(gs,delta):
    out=[]
    for g in gs:
        t=np.array(g['corners'],float);t[...,:3]+=delta;out.append(dict(g,corners=t))
    return out

def dump(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')
def clear():
    for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
def materials(emission=False):
    for key,m in DATA['materials'].items():
        mat=bpy.data.materials.get(key) or bpy.data.materials.new(key);mat.use_nodes=True;mat.use_backface_culling=True
        ns=mat.node_tree.nodes;ns.clear();links=mat.node_tree.links;out=ns.new('ShaderNodeOutputMaterial')
        sh=ns.new('ShaderNodeEmission') if emission else ns.new('ShaderNodeBsdfPrincipled')
        socket=sh.inputs['Color'] if emission else sh.inputs['Base Color']
        if not emission:sh.inputs['Roughness'].default_value=.82
        mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*m['colour'],1)
        if m.get('image_path'):
            tex=ns.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(m['image_path'],check_existing=True);links.new(tex.outputs['Color'],mix.inputs[1])
        else:mix.inputs[1].default_value=(1,1,1,1)
        links.new(mix.outputs[0],socket);links.new(sh.outputs[0],out.inputs['Surface'])
def raw_mesh(name,pts,faces,mid):
    me=bpy.data.meshes.new(name);me.from_pydata([C@Vector(p) for p in pts],[],faces);me.update();me.uv_layers.new();me.materials.append(bpy.data.materials[str(mid)])
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();return ob
def prism(name,poly,axis,lo,hi,mid):
    axes=[a for a in range(3) if a!=axis];pts=[];n=len(poly)
    for k in (lo,hi):
        for p in poly:
            co=np.zeros(3);co[axis]=k;co[axes]=p;pts.append(co)
    return raw_mesh(name,pts,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mid)
def tube(name,cx,cy,z0,z1,r0,r1,mid):
    n=12;pts=[(cx+r*math.cos(a),cy+r*math.sin(a),z) for z,r in ((z0,r0),(z1,r1)) for a in np.arange(n)*math.tau/n]
    return raw_mesh(name,pts,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mid)
def boolean(ob,cutter):
    mids=list(dict.fromkeys([m.name for m in ob.data.materials]+[m.name for m in cutter.data.materials]))
    for o in (ob,cutter):
        old=[m.name for m in o.data.materials];idx=[mids.index(old[p.material_index]) for p in o.data.polygons];o.data.materials.clear()
        for m in mids:o.data.materials.append(bpy.data.materials[m])
        for p,i in zip(o.data.polygons,idx):p.material_index=i
    bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Torn current part','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
def finish_damage(ob,kind,side):
    uv=ob.data.uv_layers.active;mi={int(m.name):i for i,m in enumerate(ob.data.materials)}
    if DM not in mi:mi[DM]=len(mi);ob.data.materials.append(bpy.data.materials[str(DM)])
    for face in ob.data.polygons:
        co=np.array([C.transposed()@ob.data.vertices[ob.data.loops[i].vertex_index].co for i in face.loop_indices]);mid=int(ob.data.materials[face.material_index].name)
        burned=kind=='wing' and np.mean(co[:,0])*side>2.42
        if burned:face.material_index=mi[DM];mid=DM
        if mid not in (DM,EQ):continue
        normal=C.transposed()@face.normal;axes=sorted(range(3),key=lambda a:abs(normal[a]))[:2]
        for i,p in zip(face.loop_indices,co):
            u=.12+p[axes[0]]*.30;v=.48+(p[axes[1]]%1.15)*.29
            if mid==EQ:u=.12+p[axes[0]]*.22;v=.16+p[axes[1]]*.22
            uv.data[i].uv=(u,1-v)
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
    # Repair within the connected mesh, before extracting material charts.
    bmesh.ops.dissolve_degenerate(bm,dist=1e-5,edges=list(bm.edges))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    report=dict(boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),volume=bm.calc_volume(signed=True))
    bm.to_mesh(ob.data);bm.free()
    assert report['boundary_edges']==0,(ob.name,report)
    # Preserve thin Boolean triangles until a topology-aware cleanup can
    # collapse/flip them. Dropping each in isolation opens the torn skin.
    return groups_from_mesh(ob.data,[int(m.name) for m in ob.data.materials],area_epsilon=1e-15),report
def damage():
    clear();materials();objects={o['name']:o for o in DATA['objects']};out={};report={}
    origin=np.array(DATA.get('origin_offset',[0,0,0]))
    for side,label in [(-1,'port'),(1,'starboard')]:
        entry=objects[label+'_engine_lod1']
        ob,_=mesh_object(dict(entry,groups=shifted(entry['groups'],origin)),label+'_engine')
        cx=side*1.814;cy=-1.4919585
        boolean(ob,tube('Open burned engine bore',cx,cy,2.19,4.6,.39,.36,EQ))
        poly=[(5,2.28),(-1.14,2.28),(-1.44,2.48),(-1.25,2.65),(-1.58,2.86),(-1.39,3.06),(-1.70,3.31),(-1.50,3.53),(-1.77,3.91),(-1.68,4.6),(5,4.6)]
        boolean(ob,prism('Longitudinal jagged half',poly,0,cx-2,cx+2,DM))
        gs,st=finish_damage(ob,'engine',side);out[label+'_engine']=shifted(gs,-origin);report[label+'_engine']=st
        bpy.data.objects.remove(ob,do_unlink=True)
        entry=objects[label+'_wing_mesh']
        ob,_=mesh_object(dict(entry,groups=shifted(entry['groups'],origin)),label+'_wing')
        # Remove the outer ~70%; the inboard 25-35% remains a substantial torn blade.
        boundary=[(2.79,-4),(2.79,-3.2),(3.06,-2.88),(2.65,-2.55),(2.94,-2.21),(2.59,-1.86),(2.89,-1.50),(2.56,-1.14),(2.79,-.78),(2.54,-.39),(2.88,.05),(2.57,.45),(2.85,1.4)]
        poly=[(x*side,z) for x,z in boundary+[(8,1.4),(8,-4)]]
        boolean(ob,prism('Ripped outer wing',poly,1,-8,8,DM))
        gs,st=finish_damage(ob,'wing',side);out[label+'_wing']=shifted(gs,-origin);report[label+'_wing']=st
        bpy.data.objects.remove(ob,do_unlink=True)
    dump('damage_world.json',out);dump('damage_geometry_check.json',report);print('TORN SURVIVORS',report,flush=True)

def damage_lods():
    """Keep the approved wound at LOD0; simplify each torn shell separately."""
    clear();materials();objects={o['name']:o['groups'] for o in DATA['objects']}
    damaged=json.loads((OUT/'damage_world.json').read_text(encoding='utf8'))
    result={};stats={}
    for zone,groups in damaged.items():
        pieces=[groups]
        if zone.endswith('_wing'):pieces += [objects[zone+'_lod1'],objects[zone+'_slide']]
        result[zone]=[];stats[zone]=[]
        for level,ratio in ((1,.38),(2,.13)):
            output=[];counts=[]
            for i,gs in enumerate(pieces):
                ob,slots=mesh_object(dict(groups=gs),zone+f' LOD{level} piece{i}',position_decimals=7)
                ob.data.validate(verbose=False,clean_customdata=False)
                mod=ob.modifiers.new('Torn survivor distance mesh','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
                ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
                simplified=groups_from_mesh(me,slots,area_epsilon=1e-15)
                bm=bmesh.new();bm.from_mesh(me)
                boundary=sum(e.is_boundary for e in bm.edges);volume=bm.calc_volume(signed=True)
                bm.free();ev.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True)
                # The visible torn engine/wing shell must still be closed.
                if i==0:assert boundary==0 and volume>0,(zone,level,boundary,volume)
                output+=simplified;counts.append(sum(len(g['corners']) for g in simplified))
            before=sum(len(g['corners']) for gs in pieces for g in gs);after=sum(counts)
            assert 0<after<before and (level!=2 or after<400),(zone,level,after)
            result[zone].append(output);stats[zone].append(dict(level=level,triangles=after,pieces=counts,ratio=ratio))
    dump('damage_lods_world.json',result)
    dump('damage_lods_check.json',dict(source_damage_sha256=hashlib.sha256((OUT/'damage_world.json').read_bytes()).hexdigest(),
        source_geometry_sha256=hashlib.sha256((OUT/'blender_input.json').read_bytes()).hexdigest(),levels=stats))
    print('DAMAGE LODS READY',stats,flush=True)
def lods():
    clear();materials(True);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
    scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.render.dither_intensity=0
    camera=bpy.data.objects.new('Projection camera',bpy.data.cameras.new('Projection lens'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.clip_end=200
    directions=[((1,0,0),(0,0,-1),(0,1,0)),((-1,0,0),(0,0,1),(0,1,0)),((0,1,0),(1,0,0),(0,0,-1)),((0,-1,0),(1,0,0),(0,0,1)),((0,0,1),(1,0,0),(0,1,0)),((0,0,-1),(-1,0,0),(0,1,0))]
    photos=OUT/'photos';photos.mkdir(exist_ok=True);projectors={};level={};tile=0;stats=[]
    cachefile=OUT/'projection_sources.json';cache=json.loads(cachefile.read_text()) if cachefile.exists() else {};newcache={}
    for entry in DATA['objects']:
        name=entry['name'];ob,slots=mesh_object(entry,name)
        if name!='Root' and not name.endswith(('_engine_lod1','_wing_mesh')):
            level[name]=entry['groups'];bpy.data.objects.remove(ob,do_unlink=True);continue
        companions=[];photo_entries=[entry]
        if name=='Root':
            for other in DATA['objects']:
                if other['name']=='glass_lod1' or '_baydoor_' in other['name']:
                    companion,_=mesh_object(other,other['name']+' for closed root photography');companions.append(companion);photo_entries.append(other)
        fingerprint=hashlib.sha256(json.dumps(photo_entries,separators=(',',':')).encode()).hexdigest();newcache[name]=fingerprint
        p=np.array([C.transposed()@v.co for v in ob.data.vertices]);center=(p.min(0)+p.max(0))/2;projectors[name]=[]
        for normal,u,v in directions:
            normal,u,v=map(np.array,(normal,u,v));scale=max(np.ptp(p@u),np.ptp(p@v))*1.045
            camera.location=C@Vector(center+normal*60);camera.rotation_euler=(C@Matrix(np.column_stack((u,v,normal)).tolist())).to_euler();camera.data.ortho_scale=float(scale)
            image=name+'_'+str(len(projectors[name]))+'.png';scene.render.filepath=str(photos/image)
            if not (photos/image).exists() or cache.get(name)!=fingerprint:bpy.ops.render.render(write_still=True)
            projectors[name].append(dict(center=center,u=u,v=v,normal=normal,scale=scale,tile=[tile%8,tile//8],image='photos/'+image));tile+=1
        for companion in companions:bpy.data.objects.remove(companion,do_unlink=True)
        # Keep intersecting authored assemblies separate while simplifying.
        # Blender 5.2 dissolve_limit crashes on their coincident welded borders.
        bpy.data.objects.remove(ob,do_unlink=True);gs=[]
        if name=='Root':
            excluded={'glass_lod1','Port_BayDoor','Starboard_BayDoor'}
            pieces=[o for o in DATA['original_objects'] if o['name'] not in excluded and not any(o['name'].endswith(s) for s in ('sculpted_engine','swept_wing','slide_carriage','slide_guide'))]
        else:pieces=[entry]
        for piece in pieces:
            work,slots=mesh_object(piece,piece['name']);work.data.validate(verbose=False,clean_customdata=False)
            mod=work.modifiers.new('Medium silhouette','DECIMATE');mod.ratio=1 if piece['name'] in ('Native_cabin','Native_cabin_transition') or piece['name'].endswith('_ventral_thruster_pylon') else .21;mod.use_collapse_triangulate=True
            ev=work.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();gs+=groups_from_mesh(me,slots);ev.to_mesh_clear();bpy.data.objects.remove(work,do_unlink=True)
        mapped=[]
        for g in gs:
            for t in np.array(g['corners']):
                n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=np.linalg.norm(n);proj=max(projectors[name],key=lambda a:n@a['normal']);co=t[:,:3]-proj['center'];tx,ty=proj['tile']
                t[:,6]=(tx+co@proj['u']/proj['scale']+.5)/8;t[:,7]=(ty+.5-co@proj['v']/proj['scale'])/8;mapped.append(t)
        level[name]=[dict(material=0,corners=np.array(mapped),unused=204)];stats.append(dict(part=name,triangles=len(mapped)))
        print('LOD PHOTO READY',name,len(mapped),flush=True)
    dump('projectors.json',projectors);dump('medium_world.json',level);dump('lod_photo_check.json',dict(parts=stats,photos=tile))
    dump('projection_sources.json',newcache)

if __name__=='__main__':
    if '--damage' in sys.argv:damage()
    if '--damage-lods' in sys.argv:damage_lods()
    if '--lods' in sys.argv:lods()
