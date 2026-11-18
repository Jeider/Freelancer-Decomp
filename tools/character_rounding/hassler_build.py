"""Editable, offline Meshy clothing fit to the unchanged Rheinland elite rig."""
import sys,json,gzip,math,hashlib,warnings
from pathlib import Path
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).parent))
from blender_workspace import configure
from hassler_inspect import studio
configure('character_rounding')
OUT=ROOT/'out/character_rounding/hassler';SOURCE=Path('D:/Work/Meshy/Hassler1')
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)));C4=C.to_4x4()

def load(kind):return json.loads(gzip.decompress((OUT/'source'/(kind+'.json.gz')).read_bytes()))
def dump(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def collection(name):
    col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(col);return col
def move(ob,col):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob)
def activate(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
def bindings(data):
    result=[]
    for b in data['bones']:
        a=np.array(b['native_bind']);mat=np.eye(4);mat[:3,:3]=a[:9].reshape(3,3);mat[:3,3]=a[9:]
        result.append(np.linalg.inv(mat))
    return result
def native_mesh(data,name,col,transform=None):
    M=C4 if transform is None else transform
    ps=[M@Vector(p) for p in data['points']];fs=[t for g in data['groups'] for t in g['faces']]
    me=bpy.data.meshes.new(name);me.from_pydata(ps,[],fs);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);uv=me.uv_layers.new(name='Native UV')
    for poly in me.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:uv.data[li].uv=data['uv'][me.loops[li].vertex_index]
    normal_matrix=M.to_3x3().inverted().transposed()
    me.normals_split_custom_set([(normal_matrix@Vector(data['normals'][l.vertex_index])).normalized() for l in me.loops])
    offset=0
    for gi,g in enumerate(data['groups']):
        mat=bpy.data.materials.new(g['name']);mat.use_nodes=True;mat.use_backface_culling=True
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.66
        if g['texture']:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(g['texture'],check_existing=True)
            mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        me.materials.append(mat)
        for poly in list(me.polygons)[offset:offset+len(g['faces'])]:poly.material_index=gi
        offset+=len(g['faces'])
    return ob
def rig_native(data,col):
    arm=bpy.data.armatures.new('rh_male_elite_body native skeleton');rig=bpy.data.objects.new('RIG — native Rheinland',arm);col.objects.link(rig)
    activate(rig);bpy.ops.object.mode_set(mode='EDIT')
    for b,mat in zip(data['bones'],bindings(data)):
        bone=arm.edit_bones.new(b['name']);bone.length=.065;bone.matrix=C4@Matrix(mat.tolist())
    for b in data['bones']:
        if b['parent'] and b['parent'] in arm.edit_bones:arm.edit_bones[b['name']].parent=arm.edit_bones[b['parent']]
    bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True;rig.display_type='WIRE';arm.display_type='STICK'
    for b in data['bones']:arm.bones[b['name']]['native_inverse_bind']=b['native_bind']
    return rig
def add_skin(ob,weights,names,rig):
    for name in names:ob.vertex_groups.new(name=name)
    for i,row in enumerate(weights):
        for j in np.flatnonzero(row>0):ob.vertex_groups[j].add([i],float(row[j]),'REPLACE')
    mod=ob.modifiers.new('Native linear skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
    ob.parent=rig
def attached(data,body,kind,hp,bone,col,rig):
    T=np.array(body['hardpoints'][hp]['matrix'])@np.linalg.inv(np.array(data['hardpoints'][hp]['matrix']))
    ob=native_mesh(data,kind+' — native unchanged',col,C4@Matrix(T.tolist()))
    names=[b['name'] for b in body['bones']];w=np.zeros((len(ob.data.vertices),len(names)));w[:,names.index(bone)]=1
    add_skin(ob,w,names,rig);ob['source_sha256']=data['sha256'];ob['attachment_hardpoint']=hp
    return ob
def import_mesh():
    bpy.ops.import_scene.fbx(filepath=str(next(SOURCE.glob('*.fbx'))))
    ob=next(o for o in bpy.context.selected_objects if o.type=='MESH');activate(ob)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    # FBX faces -Y; native body faces +Y in Blender. Rotate the whole input,
    # including its asymmetric red lapel, without mirroring the character.
    ob.rotation_euler[2]=math.pi;bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
    ob.name='SOURCE Meshy — full density';ob.data.name=ob.name
    mat=ob.data.materials[0];mat.name='Meshy original material';nodes=mat.node_tree.nodes;links=mat.node_tree.links
    # Preserve original UV explicitly when the new editing layout becomes active.
    ob.data.uv_layers.active.name='Meshy source UV'
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Meshy source UV'
    for node in nodes:
        if node.type=='TEX_IMAGE':links.new(uv.outputs[0],node.inputs['Vector'])
        elif node.type=='NORMAL_MAP':node.uv_map='Meshy source UV'
    # Supplied lossless maps are preferred to FBX's embedded JPEGs.
    for node in nodes:
        if node.type!='TEX_IMAGE':continue
        destinations=[link.to_socket.name for link in node.outputs[0].links]
        suffix=None
        if 'Base Color' in destinations:suffix='texture.png'
        elif 'Metallic' in destinations:suffix='texture_metallic.png'
        elif 'Roughness' in destinations:suffix='texture_roughness.png'
        elif any(link.to_node.type=='NORMAL_MAP' for link in node.outputs[0].links):suffix='texture_normal.png'
        if suffix:
            node.image=bpy.data.images.load(str(next(SOURCE.glob('*'+suffix))),check_existing=True)
            if suffix!='texture.png':node.image.colorspace_settings.name='Non-Color'
    return ob

def source_probe(ob):
    p=np.array([v.co[:] for v in ob.data.vertices]);me=ob.data
    print('SOURCE BOUNDS',p.min(0),p.max(0),flush=True)
    np.savez_compressed(OUT/'source_probe.npz',points=p)
    # Source-only closeup with coordinates retained in the file for measured cuts.
    ob.location.z=.97566;cam=studio(bpy.context.scene)
    for label,target,scale in [('upper',(0,0,1.53),.78),('hands',(0,0,1.02),1.5)]:
        cam.data.ortho_scale=scale;cam.location=Vector(target)+Vector((0,5,0));cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.scene.render.filepath=str(OUT/'source_preview'/(label+'.png'));bpy.ops.render.render(write_still=True)

def trim_and_reduce(ob):
    activate(ob);bm=bmesh.new();bm.from_mesh(ob.data)
    # Select actual skin colouring inside the collar, instead of cutting the
    # collar/lapel with an oversized cylinder.
    image=next(n.image for n in ob.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and any(l.to_socket.name=='Base Color' for l in n.outputs[0].links))
    pixels=np.array(image.pixels[:]).reshape(image.size[1],image.size[0],4);layer=bm.loops.layers.uv.active
    skin=set()
    for f in bm.faces:
        p=f.calc_center_median()
        if p.z<.585 or abs(p.x)>.12 or not -.11<p.y<.14:continue
        uv=sum((l[layer].uv for l in f.loops),Vector((0,0)))/len(f.loops)
        rgb=pixels[int(uv.y%1*(image.size[1]-1)),int(uv.x%1*(image.size[0]-1)),:3]
        if 1.11<rgb[0]/max(rgb[1],.001)<1.65 and 1.06<rgb[1]/max(rgb[2],.001)<1.8:skin.update(f.verts)
    # Anatomical removal volumes are authored from the supplied source views.
    # Open neck and wrist rims are intentional attachment openings.
    remove=[]
    for v in bm.verts:
        x,y,z=v.co
        head=z>.755 or (z>.60 and (x/.093)**2+((y-.008)/.080)**2<1) or (z>.66 and abs(x)<.10 and .02<y<.15 and v in skin)
        hand=abs(x)>.40 and Vector((abs(x)-.535,y-.025,z-.105)).dot(Vector((.56,0,-.83)))>0
        if head or hand:remove.append(v)
    bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(ob.data);bm.free()
    before=sum(len(p.vertices)-2 for p in ob.data.polygons)
    dec=ob.modifiers.new('Preview density — preserve form','DECIMATE');dec.ratio=min(1,58000/before);dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)
    print('CLOTHING REDUCED',before,'to',len(ob.data.polygons),flush=True)
    return before

def remove_holster(ob):
    """Rebuild the fused waist as a continuous sampled strip, no polygon caps."""
    me=ob.data;me.calc_loop_triangles();ps=[v.co.copy() for v in me.vertices]
    torso_tris=[t for t in me.loop_triangles if abs(sum(ps[i].x for i in t.vertices)/3)<.285]
    ts=[tuple(t.vertices) for t in torso_tris]
    luvs=[[me.uv_layers[0].data[i].uv.copy() for i in t.loops] for t in torso_tris]
    tree=BVHTree.FromPolygons(ps,ts,all_triangles=True)
    from mathutils.geometry import barycentric_transform
    lo,hi=.035,.350
    images={}
    for n in me.materials[0].node_tree.nodes:
        if n.type!='TEX_IMAGE':continue
        for link in n.outputs[0].links:
            if link.to_socket.name in ('Base Color','Metallic','Roughness'):
                im=n.image;images[link.to_socket.name]=(im,np.array(im.pixels[:]).reshape(im.size[1],im.size[0],4))
    def sample(theta,z):
        # +X side has no holster. Use its matching radial surface on -X.
        direction=Vector((math.cos(theta),math.sin(theta),0));sgn=1 if direction.x>=0 else -1
        clean=Vector((abs(direction.x),direction.y,0));origin=clean*.45;origin.z=z
        hit,no,ti,dist=tree.ray_cast(origin,-clean)
        if hit is None:raise RuntimeError(('Missing waist surface',theta,z))
        uv=barycentric_transform(hit,*[ps[k] for k in ts[ti]],*[Vector((u.x,u.y,0)) for u in luvs[ti]])
        point=Vector((hit.x*sgn,hit.y,z))
        return point,uv
    width,height=1024,512
    maps={key:np.ones((height,width,4),dtype=np.float32) for key in images}
    for j in range(height):
        z=lo+(j+.5)/height*(hi-lo)
        for i in range(width):
            theta=(i+.5)/width*2*math.pi
            point,uv=sample(theta,z)
            for key,(im,pixels) in images.items():
                xx=uv.x%1*(im.size[0]-1);yy=uv.y%1*(im.size[1]-1);x=int(xx);y=int(yy);fx=xx-x;fy=yy-y
                maps[key][j,i]=pixels[y,x]*(1-fx)*(1-fy)+pixels[y,x+1]*fx*(1-fy)+pixels[y+1,x]*(1-fx)*fy+pixels[y+1,x+1]*fx*fy
    mat=bpy.data.materials.new('Hassler reconstructed waist');mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='Meshy source UV'
    for key,pixels in maps.items():
        im=bpy.data.images.new('Waist '+key,width=width,height=height,alpha=True)
        if key!='Base Color':im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(OUT/'textures'/('waist_'+key.replace(' ','_').lower()+'.png'));im.file_format='PNG';im.save()
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(uvnode.outputs[0],tex.inputs[0]);mat.node_tree.links.new(tex.outputs[0],bs.inputs[key])
    me.materials.append(mat);mi=len(me.materials)-1
    bm=bmesh.new();bm.from_mesh(me);uv=bm.loops.layers.uv.active
    for z in (lo,hi):
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,z),plane_no=(0,0,1))
    doomed=[f for f in bm.faces if lo+1e-6<f.calc_center_median().z<hi-1e-6 and abs(f.calc_center_median().x)<.285]
    bmesh.ops.delete(bm,geom=doomed,context='FACES')
    def angle(v):return math.atan2(v.co.y,v.co.x)%(2*math.pi)
    boundary=[]
    for z in (lo,hi):
        ring={v for e in bm.edges if e.is_boundary and all(abs(v.co.z-z)<1e-5 and abs(v.co.x)<.285 for v in e.verts) for v in e.verts}
        assert len(ring)>20,(z,len(ring));boundary.append(sorted(ring,key=angle))
    rings=[boundary[0]];angles=[list(map(angle,boundary[0]))]
    sectors=80;rows=30
    for row in range(1,rows):
        z=lo+(hi-lo)*row/rows;ring=[];aa=[]
        for k in range(sectors):
            theta=k*2*math.pi/sectors;point,_=sample(theta,z)
            ring.append(bm.verts.new(point));aa.append(theta)
        rings.append(ring);angles.append(aa)
    rings.append(boundary[1]);angles.append(list(map(angle,boundary[1])))
    created=[]
    def face(vertices,uvs):
        f=bm.faces.new(vertices);f.material_index=mi;created.append(f)
        for l,t in zip(f.loops,uvs):l[uv].uv=t
    # Zipper triangulation connects different native boundary counts exactly.
    for row in range(len(rings)-1):
        a,b=rings[row:row+2];aa,bb=angles[row:row+2];i=j=0
        for _ in range(len(a)+len(b)):
            ta=aa[i%len(a)]+(2*math.pi if i>=len(a) else 0);tb=bb[j%len(b)]+(2*math.pi if j>=len(b) else 0)
            na=aa[(i+1)%len(a)]+(2*math.pi if i+1>=len(a) else 0);nb=bb[(j+1)%len(b)]+(2*math.pi if j+1>=len(b) else 0)
            va=a[i%len(a)];vb=b[j%len(b)]
            if na<=nb:
                vc=a[(i+1)%len(a)];face((va,vc,vb),[(ta/(2*math.pi),(va.co.z-lo)/(hi-lo)),(na/(2*math.pi),(vc.co.z-lo)/(hi-lo)),(tb/(2*math.pi),(vb.co.z-lo)/(hi-lo))]);i+=1
            else:
                vc=b[(j+1)%len(b)];face((va,vc,vb),[(ta/(2*math.pi),(va.co.z-lo)/(hi-lo)),(nb/(2*math.pi),(vc.co.z-lo)/(hi-lo)),(tb/(2*math.pi),(vb.co.z-lo)/(hi-lo))]);j+=1
    unused=[v for v in bm.verts if not v.link_faces]
    if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
    return {'removed_faces':len(doomed),'replacement_faces':len(created),'method':'continuous waist strip sampled from unobstructed side; joined to original boundary rings'}

def fit_and_skin(ob,data):
    names=[b['name'] for b in data['bones']];B=bindings(data)
    J={b['name']:np.array(C@Vector(m[:3,3])) for b,m in zip(data['bones'],B)}
    p=np.array([v.co[:] for v in ob.data.vertices]);q=p.copy();x,y,z=p.T;ax=abs(x)
    sz=np.array([-.950645,-.82,-.43,-.025,.19,.59,.74]);tz=np.array([-.975662,-.876,-.45,0,.18,.50,.65])
    q[:,2]=np.interp(z,sz,tz);q[:,1]=y*.78+.014;q[:,0]=x*.90
    leg=1-smooth(-.06,.12,z)
    source_x=np.interp(z,[-.95,-.82,-.43,-.025],[.235,.230,.174,.105])
    for side,sgn in [('R',1),('L',-1)]:
        member=x*sgn>=0
        target_x=np.interp(z,[-.95,-.82,-.43,-.025],[abs(J[side+'Foot'][0]),abs(J[side+'Foot'][0]),abs(J[side+'LowLeg'][0]),abs(J[side+'Thigh'][0])])
        q[member,0]=x[member]-.90*sgn*(source_x[member]-target_x[member])*leg[member]
        q[member,1]+=np.interp(z[member],[-.95,-.82,-.43,-.025],[.02,.02,.07,0])*leg[member]
    # Fit the A-pose limbs to measured native joint lines. Rotations, rather
    # than X-only compression, retain the sleeve and bracer cross sections.
    arm=smooth(np.interp(z,[.1,.4,.58,.7],[.28,.24,.20,.19]),np.interp(z,[.1,.4,.58,.7],[.32,.28,.27,.27]),ax)*smooth(-.16,-.08,z)
    for side,sgn in [('R',1),('L',-1)]:
        S=np.array([[sgn*.245,-.025,.585],[sgn*.405,.005,.325],[sgn*.535,.025,.105]])
        T=np.array([J[side+'UpArm'],J[side+'LowArm'],J[side+'Hand']])
        candidates=[]
        for k in range(2):
            a,b=S[k:k+2];d=b-a;t=np.clip((p-a)@d/(d@d),0,1);center=a+t[:,None]*d
            rot=Vector(d).rotation_difference(Vector(T[k+1]-T[k])).to_matrix()
            candidates.append((np.linalg.norm(p-center,axis=1),T[k]+t[:,None]*(T[k+1]-T[k])+(p-center)@np.array(rot).T*.88))
        # Blend the two segment fits only near the actual elbow.
        blend=smooth(.275,.375,z);aq=candidates[0][1]*blend[:,None]+candidates[1][1]*(1-blend[:,None])
        factor=arm*(x*sgn>0);q=q*(1-factor[:,None])+aq*factor[:,None]
    for v,pt in zip(ob.data.vertices,q):v.co=pt
    ob.data.update()
    # Transfer native weights on the fitted surface; topology partitions keep
    # armpits and inner thighs from borrowing the other limb's influences.
    native=np.array([C@Vector(v) for v in data['points']]);fs=[tuple(t) for g in data['groups'] for t in g['faces']]
    W=np.zeros((len(native),len(names)))
    for i,row in enumerate(data['skin']):
        for bone,w in row.items():W[i,int(bone)]=w
    parts={}
    for label,prefix in [('RArm','R'),('LArm','L'),('RLeg','R'),('LLeg','L'),('Torso','')]:
        ids=[i for i,n in enumerate(names) if (n.startswith(prefix) and ('Arm' in n or 'Hand' in n or 'Collar' in n))] if 'Arm' in label else \
            ([i for i,n in enumerate(names) if n.startswith(prefix) and any(s in n for s in ['Thigh','Leg','Foot','Toe'])] if 'Leg' in label else [i for i,n in enumerate(names) if n in ['MAXRoot','LowerTorso','UpperTorso','Spine3','Body_Neck','Body_Head']])
        selected=[t for t in fs if W[list(t)][:,ids].sum(1).max()>.25]
        parts[label]=(BVHTree.FromPolygons(native.tolist(),selected,all_triangles=True),selected)
    from mathutils.geometry import barycentric_transform
    weights=np.zeros((len(q),len(names)))
    for i,pt in enumerate(q):
        side='R' if pt[0]>=0 else 'L'
        label=side+'Arm' if arm[i]>.55 else (side+'Leg' if z[i]<-.08 else 'Torso')
        tree,faces=parts[label];loc,no,ti,dist=tree.find_nearest(Vector(pt));t=faces[ti]
        bary=barycentric_transform(loc,*[Vector(native[j]) for j in t],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        w=np.maximum(np.array(bary),0)@W[list(t)]
        keep=np.argsort(w)[-4:];row=np.zeros(len(names));row[keep]=w[keep];row[row<.005]=0;row/=row.sum();weights[i]=row
    # Coincident UV seam vertices must have identical skin weights.
    buckets={}
    for i,pt in enumerate(q):buckets.setdefault(tuple(pt.round(6)),[]).append(i)
    for ids in buckets.values():
        if len(ids)>1:weights[ids]=weights[ids].mean(0)
    return p,q,weights,names,arm

def pose_action(rig):
    scene=bpy.context.scene
    specs=[(1,'REST',[]),(30,'ELBOWS',[('LLowArm',(1,0,0),65),('RLowArm',(1,0,0),45)]),
           (60,'SHOULDERS',[('LUpArm',(0,1,0),30),('RUpArm',(0,1,0),-30)]),
           (90,'STEP',[('LThigh',(1,0,0),30),('LLowLeg',(1,0,0),-55)]),
           (120,'TURN',[('UpperTorso',(0,0,1),15),('Body_Head',(0,0,1),-25)]),(150,'REST',[])]
    for frame,label,changes in specs:
        for bone in rig.pose.bones:bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion((1,0,0,0))
        for name,axis,angle in changes:
            bone=rig.pose.bones[name];local=rig.data.bones[name].matrix_local.to_3x3().inverted()@Vector(axis)
            bone.rotation_quaternion=Quaternion(local,math.radians(angle))
        for bone in rig.pose.bones:bone.keyframe_insert('rotation_quaternion',frame=frame)
        scene.timeline_markers.new(label,frame=frame)
    scene.frame_start=1;scene.frame_end=150;scene.frame_set(1)
    rig.animation_data.action.name='Hassler — synthetic fitting checks (not game animation)'

def neck_lining(col,rig,names):
    points=[];faces=[];segments=40
    for z,rx,ry in [(.49,.102,.092),(.58,.085,.080),(.65,.067,.067)]:
        for k in range(segments):
            a=k*2*math.pi/segments;points.append((.002+rx*math.cos(a),.001+ry*math.sin(a),z))
    for j in range(2):
        for k in range(segments):faces.append((j*segments+k,j*segments+(k+1)%segments,(j+1)*segments+(k+1)%segments,(j+1)*segments+k))
    me=bpy.data.meshes.new('Black inner collar lining');me.from_pydata(points,[],faces);me.update()
    ob=bpy.data.objects.new('Hassler — inner collar lining',me);col.objects.link(ob)
    mat=bpy.data.materials.new('Hassler dark collar lining');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.012,.016,.014,1);bs.inputs['Roughness'].default_value=.8;me.materials.append(mat)
    w=np.zeros((len(points),len(names)));w[:,names.index('Spine3')]=1;add_skin(ob,w,names,rig)
    for p in me.polygons:p.use_smooth=True
    return ob

def main_build(source):
    body=load('body');oldcol=collection('ARCHIVE — native body (disabled)');refcol=collection('ARCHIVE — full Meshy (disabled)')
    editcol=collection('EDIT — Hassler clothing');rigcol=collection('RIG — native skeleton');partscol=collection('REFERENCE — native head and gloves')
    native=native_mesh(body,'rh_male_elite_body — installed original',oldcol);native.location.z=.975662
    move(source,refcol);source.location.z=.975662
    ob=source.copy();ob.data=source.data.copy();editcol.objects.link(ob);ob.location=(0,0,0);ob.name='Hassler — EDIT clothing'
    before=trim_and_reduce(ob);holster=remove_holster(ob)
    original,fitted,weights,names,arm=fit_and_skin(ob,body)
    rig=rig_native(body,rigcol);add_skin(ob,weights,names,rig);rig.location.z=.975662
    head=attached(load('head'),body,'Hassler head','hp_head','Body_Head',partscol,rig)
    left=attached(load('left_hand'),body,'Left glove','hp_left b','LHand',partscol,rig)
    right=attached(load('right_hand'),body,'Right glove','hp_right b','RHand',partscol,rig)
    lining=neck_lining(editcol,rig,names)
    refcol.hide_viewport=refcol.hide_render=True;oldcol.hide_viewport=oldcol.hide_render=True
    pose_action(rig);scene=bpy.context.scene;cam=studio(scene)
    for poly in ob.data.polygons:poly.use_smooth=True
    report={'source_triangles':656794,'clothing_before_reduction':before,'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),
            'vertices':len(ob.data.vertices),'bones':len(names),'max_influences':int((weights>0).sum(1).max()),
            'native_skeleton_preserved':True,'meshy_head_and_hands_removed':True,'native_head_and_gloves_preserved':True,
            'holster':holster,'uv_status':'original Meshy UV, next authoring pass pending','installed':False,'game_animation_validated':False}
    dump(OUT/'prototype_report.json',report)
    np.savez_compressed(OUT/'fit.npz',source_positions=original,points=fitted,weights=weights,arm=arm,bone_names=names)
    folder=OUT/'preview';folder.mkdir(exist_ok=True)
    for label,frame,direction,center,scale in [('front',1,(0,1,0),(0,0,.92),2.10),('back',1,(0,-1,0),(0,0,.92),2.10),
             ('upper',1,(.25,1,.15),(0,0,1.47),.85),('elbows',30,(.3,1,.1),(0,0,1.27),1.35),('step',90,(.5,1,.15),(0,0,.92),2.1)]:
        scene.frame_set(frame);d=Vector(direction).normalized();cam.location=Vector(center)+d*5
        cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        scene.render.filepath=str(folder/(label+'.png'));bpy.ops.render.render(write_still=True)
    scene.frame_set(1);d=Vector((.2,1,.08)).normalized();cam.location=Vector((0,0,1))+d*5
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.1
    activate(rig)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    text=bpy.data.texts.new('README — Hassler prototype');text.write(json.dumps(report,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_rigged.blend'),compress=True)
    print(json.dumps(report),flush=True)

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True);configure('character_rounding')
    source=import_mesh()
    if '--probe' in sys.argv:source_probe(source);return
    main_build(source)

if __name__=='__main__':main()
