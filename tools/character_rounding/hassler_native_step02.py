"""Step 02: lower head, fitted native Wilham collar and Dietrich shoulder artwork.

Only writes an offline descendant of step_01; source/game files are read-only.
"""
import sys,json,gzip,hashlib,copy,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.geometry import barycentric_transform
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_02';PARENT=TOP/'step_01/hassler_native_upper.blend'
HEAD_DROP=.025

def load(path):return json.loads(gzip.decompress(path.read_bytes()))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def get(name):return bpy.data.objects[name]
def weights_of(ob):
    w=np.zeros((len(ob.data.vertices),len(ob.vertex_groups)))
    for v in ob.data.vertices:
        for g in v.groups:w[v.index,g.group]=g.weight
    return w
def actual_base():
    source=native.load('body');ob=get('00 Native elite — original torso and sleeves')
    data=copy.deepcopy(source);data['groups']=[]
    mapping=list(ob['native_vertex_map'])
    for key in ('points','normals','uv','skin'):data[key]=[source[key][i] for i in mapping]
    data['groups']=[{'name':'torso','faces':[list(f.vertices) for f in ob.data.polygons]}]
    return data

def lower_head(rig):
    head=get('Hassler head — native unchanged')
    for v in head.data.vertices:v.co.z-=HEAD_DROP
    head['head_fit_offset_m']=[0,0,-HEAD_DROP]
    head['construction']='Native head geometry, rigidly lowered 25 mm; matching Body_Head and Head_End rest positions'
    native.activate(rig);bpy.ops.object.mode_set(mode='EDIT')
    for name in ('Body_Head','Head_End'):
        bone=rig.data.edit_bones[name];bone.head.z-=HEAD_DROP;bone.tail.z-=HEAD_DROP
    bpy.ops.object.mode_set(mode='OBJECT')
    changes={}
    for name in ('Body_Head','Head_End'):
        bone=rig.data.bones[name];bone['original_native_inverse_bind']=list(bone['native_inverse_bind'])
        original=np.array(bone['original_native_inverse_bind']);rotation=original[:9].reshape(3,3)
        packed=original[:9].tolist()+(original[9:]+rotation@np.array([0,HEAD_DROP,0])).tolist()
        bone['native_inverse_bind']=packed;changes[name]=packed
    # Keep the body's neck attachment fixed, shorten only the upper shirt insert.
    ob=get('00 Native neck insert — recoloured black')
    attachment={tuple(round(c,5) for c in v.co) for v in get('00 Native elite — original torso and sleeves').data.vertices}
    for v in ob.data.vertices:
        if tuple(round(c,5) for c in v.co) in attachment:continue
        t=float(np.clip((v.co.z-.552)/(.622-.552),0,1));v.co.z-=HEAD_DROP*t*t*(3-2*t)
    # Its original split normals described the uncompressed donor collar.
    if ob.data.has_custom_normals:
        native.activate(ob);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    ob.data.update()
    # This insert and the red lapel previously had the same surface offset.
    # Keep the under-shirt behind both the red and gold garment layers.
    for v in get('00 Black chest insert — covers native neck clasp').data.vertices:v.co.y-=.003
    body=native.load('body');hp=copy.deepcopy(body['hardpoints']['hp_head']);hp['matrix'][1][3]-=HEAD_DROP
    return {'translation_blender_m':[0,0,-HEAD_DROP],'translation_native_m':[0,-HEAD_DROP,0],
            'modified_inverse_binds':changes,'fitted_hp_head':hp,
            'note':'Offline fitted rest poses only; DFM joint/HP export is deferred. No game animation validation.'}

def fit_wilham_collar(rig,col,surface,names):
    source=load(TOP/'source/wilham.json.gz');d=copy.deepcopy(source)
    p=np.array(d['points']);uv=np.array(d['uv']);d['groups']=d['groups'][:2]
    for g in d['groups']:
        g['faces']=[t for t in g['faces'] if all(uv[i,0]>.79 and p[i,1]>.45 for i in t)]
    d=upper.compact(d);assert sum(len(g['faces']) for g in d['groups'])==52
    old=get('01 Collar — asymmetric folded cloth');bpy.data.objects.remove(old,do_unlink=True)
    ob=native.native_mesh(d,'01 Collar — Wilham folded construction',col)
    for v in ob.data.vertices:
        x,y,z=v.co;x=(x+.0007324)*.90;y*=.96
        t=float(np.clip((z-.50)/.14,0,1));z-=.05*t*t*(3-2*t)
        front=float(np.clip((y-.045)/.10,0,1))
        left=float(np.clip(-x/.04,0,1));right=float(np.clip(x/.04,0,1))
        z+=front*(-.035*left+.012*right)
        v.co=(x,y,z)
    if ob.data.has_custom_normals:
        native.activate(ob);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    # Shared positions must remain welded through the donor's two material groups.
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.join_triangles(bm,faces=list(bm.faces),angle_face_threshold=.6,angle_shape_threshold=.7,
                           cmp_seam=True,cmp_uvs=True,cmp_materials=False)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    crease=bm.edges.layers.float.new('crease_edge')
    for edge in bm.edges:
        edge[crease]=.85 if edge.is_boundary else (.45 if edge.calc_face_angle(0)>.65 else 0)
    bm.to_mesh(ob.data);bm.free()
    # Source atlas already contains a complete grey inner field and a darkenable
    # border. Desaturating the red border preserves its original continuous UV.
    mat=upper.material('Hassler collar — Wilham grey cloth and dark border',(.25,.28,.26),.78,texture=d['groups'][0]['texture'])
    n=mat.node_tree.nodes;l=mat.node_tree.links;tex=next(n for n in n if n.type=='TEX_IMAGE');bs=n.get('Principled BSDF')
    hsv=n.new('ShaderNodeHueSaturation');hsv.inputs['Saturation'].default_value=0;hsv.inputs['Value'].default_value=.68
    l.new(tex.outputs['Color'],hsv.inputs['Color']);l.new(hsv.outputs['Color'],bs.inputs['Base Color'])
    uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map=ob.data.uv_layers.active.name;l.new(uvnode.outputs[0],tex.inputs['Vector'])
    ob.data.materials.clear();ob.data.materials.append(mat)
    for f in ob.data.polygons:f.material_index=0;f.use_smooth=True
    skin=np.array([surface.nearest_weights(np.array(v.co)) for v in ob.data.vertices]);native.add_skin(ob,skin,names,rig)
    sub=ob.modifiers.new('Smooth the native folded profile','SUBSURF');sub.levels=2;sub.render_levels=2
    sub.boundary_smooth='PRESERVE_CORNERS'
    ob['construction']='52 native Wilham collar triangles; both exterior and inner folded wall retained; fitted lower and asymmetrically to Hassler art'
    ob['source_sha256']=source['sha256'];ob['source_native_faces']=52
    return ob

def transfer_epaulette_uv(dietrich):
    ob=get('02 Epaulettes — Reichman source geometry');reich=native.load('epaulettes')
    p=np.array(dietrich['points']);uv=np.array(dietrich['uv'])
    selected=[t for t in dietrich['groups'][0]['faces'] if all(p[i,1]>.49 and abs(p[i,0])>.11 and uv[i,0]>.22 and uv[i,1]<.50 for i in t)]
    assert len(selected)>100
    trees={}
    for sign in (-1,1):
        faces=[t for t in selected if np.mean(p[t,0])*sign>0]
        trees[sign]=(BVHTree.FromPolygons(p.tolist(),faces,all_triangles=True),faces)
    old=ob.data.uv_layers[0];old.name='Reichman native UV — reference'
    layer=ob.data.uv_layers.new(name='Dietrich shoulder artwork');layer.active_render=True;ob.data.uv_layers.active_index=1
    vertex_uv={};samples=[]
    for v,source_id in zip(ob.data.vertices,ob['native_vertex_map']):
        q=np.array(reich['points'][source_id]);sign=1 if q[0]>0 else -1;tree,faces=trees[sign]
        # Preserve native shoulder orientation. Use the corresponding donor skin,
        # not a bounding rectangle cut from the texture.
        loc,no,idx,dist=tree.find_nearest(Vector(q));tri=faces[idx]
        b=np.array(barycentric_transform(loc,*[Vector(p[i]) for i in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))))
        b=np.clip(b,0,1);b/=b.sum();vertex_uv[v.index]=b@uv[tri]
        samples.append({'vertex':v.index,'donor_triangle':tri,'weights':b.tolist(),'distance_m':dist})
    for loop in ob.data.loops:layer.data[loop.index].uv=vertex_uv[loop.vertex_index]
    mat=upper.material('Hassler epaulettes — Dietrich native gold',(.5,.3,.07),.65,.05,dietrich['groups'][0]['texture'])
    tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE');uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map=layer.name
    mat.node_tree.links.new(uvnode.outputs[0],tex.inputs['Vector']);ob.data.materials[0]=mat
    ob['texture_source']='rh_deidrich_body / rh_dedrich_body_1';ob['texture_source_sha256']=dietrich['sha256']
    upper.dump(OUT/'epaulette_uv_transfer.json',{'donor_sha256':dietrich['sha256'],'method':'same-side native surface barycentric transfer','samples':samples})
    return {'donor_triangles':len(selected),'max_distance_m':max(s['distance_m'] for s in samples),'texture':dietrich['groups'][0]['texture']}

def cloth_finish(dietrich):
    mat=upper.material('Hassler brocade — Dietrich native front cloth',(.45,.3,.1),.75,.02,dietrich['groups'][3]['texture'])
    names=['03 Chest gold facing','05 Left shoulder gold facing','07 Back Y facing']
    for name in names:
        ob=get(name);old=ob.data.uv_layers[0];old.name='Step 01 gold UV — reference'
        layer=ob.data.uv_layers.new(name='Dietrich cloth patch');layer.active_render=True;ob.data.uv_layers.active_index=1
        # A single continuous cloth field at matching scale, including the Y
        # arms. The separate front-cloth atlas is all gold within this contour;
        # the blue/neck regions and painted border stay outside the UV charts.
        for loop in ob.data.loops:
            x,y,z=ob.data.vertices[loop.vertex_index].co
            layer.data[loop.index].uv=(.5+x*1.6,.08+(z-.18)*2)
        ob.data.materials[0]=mat
        ob['texture_source']='rh_deidrich_body / rh_dedrich_body_3, continuous cloth coordinates'
    uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='Dietrich cloth patch'
    tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE');mat.node_tree.links.new(uvnode.outputs[0],tex.inputs['Vector'])
    # Keep the red field calm; the donor patch provides subtle weave only.
    ob=get('04 Red asymmetrical lapel');w=load(TOP/'source/wilham.json.gz')
    red=upper.material('Hassler red lapel — Wilham cloth patch',(.35,.025,.014),.8,0,w['groups'][0]['texture'])
    layer=ob.data.uv_layers.active
    for a in layer.data:a.uv=(.115+float(a.uv.x)*.055,.94+float(a.uv.y)*.045)
    n=red.node_tree.nodes;l=red.node_tree.links;tex=next(n for n in n if n.type=='TEX_IMAGE');bs=n.get('Principled BSDF')
    bw=n.new('ShaderNodeRGBToBW');ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(.24,.018,.012,1);ramp.color_ramp.elements[1].color=(.37,.03,.02,1)
    l.new(tex.outputs['Color'],bw.inputs[0]);l.new(bw.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
    ob.data.materials[0]=red

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    cam=scene.camera;d=Vector(direction).normalized();cam.location=Vector(target)+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True);parent_hash=sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);rig=get('RIG — native Rheinland')
    source=native.load('body');names=[b['name'] for b in source['bones']]
    surface=upper.Surface(actual_base());edit=bpy.data.collections['EDIT — native costume upper study']
    fit=lower_head(rig);collar=fit_wilham_collar(rig,edit,surface,names)
    dietrich=load(TOP/'source/dietrich/source/dietrich.json.gz')
    texture=transfer_epaulette_uv(dietrich);cloth_finish(dietrich)
    scene.cycles.samples=32;scene.render.resolution_x=1000;scene.render.resolution_y=1000
    views=[('front',(0,1,0)),('three_quarter',(.65,1,.12)),('back',(0,-1,.03)),('side',(1,0,.02))]
    if '--quick' in sys.argv:views=views[:2]
    for label,direction in views:render(scene,label,direction)
    if '--quick' not in sys.argv:
        render(scene,'collar_close',(.35,1,.18),(0,0,1.56),.57)
        scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)
    native.activate(rig)
    report={'step':'02 fitted neck and Dietrich materials','parent':str(PARENT),'parent_sha256':parent_hash,
            'head_fit':fit,'collar_source':'native rh_wilham_body, 52 selected source triangles; new fitted profile',
            'epaulettes_geometry':'Reichman unchanged from step_01','epaulettes_texture':texture,
            'donor_sha256':dietrich['sha256'],'game_installed':False,'game_animation_checked':False,
            'phase':'offline upper costume refinement; native cloth crops are editable, not a final unified game atlas'}
    upper.dump(OUT/'report.json',report)
    text=bpy.data.texts.get('README — native upper prototype');text.clear();text.write(json.dumps(report,indent=2,ensure_ascii=False))
    cam=scene.camera;d=Vector((.35,1,.08)).normalized();cam.location=Vector((0,0,1.47))+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.02
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    assert sha(PARENT)==parent_hash
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
