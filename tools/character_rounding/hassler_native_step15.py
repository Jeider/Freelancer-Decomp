"""Bretonia trousers/boots and a smaller recessed waist belt below Hassler's tunic."""
import sys,json,gzip,math,copy
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step08 as s8
import hassler_native_step09 as s9
import hassler_native_step13 as s13
import hassler_native_step14 as s14
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_15';PARENT=s14.OUT/'hassler_native_upper.blend'
LOWER='00 Hassler lower — Bretonia trousers and high boots'
BELT='19 Hassler belt — lower narrow Bretonia fit';BUCKLE='20 Rheinland clasp — compact waist fit';LOOPS='21 Belt keepers — compact waist fit'
TOP_Z=.145
WAIST='23 Waist cloth — recessed below overhanging tunic'

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s9.OUT=OUT;s9.render(scene,label,direction,target,scale)

def cloth(name,path,mode):
    mat=upper.material(name,(.04,.09,.06),.82,0.,path);n=mat.node_tree.nodes;l=mat.node_tree.links;tex=next(x for x in n if x.type=='TEX_IMAGE');tex.image.pack();bs=n.get('Principled BSDF')
    sep=n.new('ShaderNodeSeparateColor');l.new(tex.outputs[0],sep.inputs[0]);bw=n.new('ShaderNodeRGBToBW');l.new(tex.outputs[0],bw.inputs[0])
    power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=.55;l.new(bw.outputs[0],power.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.006,.018,.012,1);ramp.color_ramp.elements[1].position=.28;ramp.color_ramp.elements[1].color=(.055,.135,.092,1);l.new(power.outputs[0],ramp.inputs[0])
    if mode=='sole':
        ramp.color_ramp.elements[0].color=(.004,.006,.005,1);ramp.color_ramp.elements[1].position=.55;ramp.color_ramp.elements[1].color=(.042,.05,.045,1)
        l.new(ramp.outputs[0],bs.inputs['Base Color'])
    elif mode=='boots':
        add=n.new('ShaderNodeMath');add.operation='ADD';l.new(sep.outputs[1],add.inputs[0]);l.new(sep.outputs[2],add.inputs[1])
        epsilon=n.new('ShaderNodeMath');epsilon.operation='ADD';epsilon.inputs[1].default_value=.0001;l.new(add.outputs[0],epsilon.inputs[0])
        ratio=n.new('ShaderNodeMath');ratio.operation='DIVIDE';l.new(sep.outputs[0],ratio.inputs[0]);l.new(epsilon.outputs[0],ratio.inputs[1])
        mask=n.new('ShaderNodeMapRange');mask.clamp=True;mask.inputs['From Min'].default_value=.85;mask.inputs['From Max'].default_value=1.65;l.new(ratio.outputs[0],mask.inputs['Value'])
        grey=n.new('ShaderNodeValToRGB');grey.color_ramp.elements[0].color=(.035,.042,.039,1);grey.color_ramp.elements[1].position=.34;grey.color_ramp.elements[1].color=(.27,.29,.265,1);l.new(sep.outputs[0],grey.inputs[0])
        mix=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mix.inputs[0]);l.new(ramp.outputs[0],mix.inputs[1]);l.new(grey.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    else:l.new(ramp.outputs[0],bs.inputs['Base Color'])
    return mat

def lower(d,edit,rig,names):
    p=np.array(d['points']);norm=np.array(d['normals']);uv=np.array(d['uv']);w=np.zeros((len(p),len(names)))
    for i,skin in enumerate(d['skin']):
        for j,value in skin.items():w[i,names.index(d['bones'][int(j)]['name'])]=value
    verts=[];weights=[];normals=[];uvs=[];faces=[];materials=[];source=[];lookup={}
    def emit(v):
        pp,nn,qq,ww=v;key=tuple(np.round(np.r_[pp,nn,qq,ww],9))
        if key not in lookup:
            lookup[key]=len(verts);verts.append(native.C@Vector(pp));normals.append((native.C@Vector(nn)).normalized());uvs.append(qq);weights.append(ww)
        return lookup[key]
    for gi,g in enumerate(d['groups']):
        for fi,face in enumerate(g['faces']):
            # Exclude sleeves all the way to their tips; feet may extend beyond
            # the hip width, so only apply this lateral filter above the knees.
            if (max(p[face,1])>-.4 and max(abs(p[face,0]))>.205) or min(p[face,1])>=TOP_Z:continue
            if gi==0 and max(p[face,1])>0:continue  # original belt is separate
            records=[(p[i],norm[i],uv[i],w[i]) for i in face];out=[]
            for a,b in zip(records,records[1:]+records[:1]):
                ina=a[0][1]<=TOP_Z;inb=b[0][1]<=TOP_Z
                if ina:out.append(a)
                if ina!=inb:
                    t=(TOP_Z-a[0][1])/(b[0][1]-a[0][1]);out.append(tuple(x+(y-x)*t for x,y in zip(a,b)))
            if len(out)<3:continue
            ids=[emit(v) for v in out];faces.append(ids);source.append([gi,fi]);materials.append(0 if gi==0 else (2 if gi==1 and max(p[face,1])<-.35 else (1 if gi==1 else 3)))
    mats=[cloth('Hassler 15 — dark boot soles',d['groups'][0]['texture'],'sole'),cloth('Hassler 15 — Rheinland green trousers',d['groups'][1]['texture'],'pants'),cloth('Hassler 15 — grey high boots and green knees',d['groups'][1]['texture'],'boots'),cloth('Hassler 15 — green waist under the tunic',d['groups'][2]['texture'],'pants')]
    ob=upper.geometry(LOWER,verts,faces,uvs,weights,mats[0],edit,rig,names)
    for mat in mats[1:]:ob.data.materials.append(mat)
    for f,mi in zip(ob.data.polygons,materials):f.material_index=mi
    ob.data.normals_split_custom_set([normals[l.vertex_index][:] for l in ob.data.loops]);ob['construction']='Native br_male_elite trousers and boots; original UV/weights/normals, clipped only at hidden upper waist. Green trousers, grey boot leather, dark soles.'
    return ob,{'source_faces':source,'top_cut_z':TOP_Z,'native_bind_matrices_equal':True,'original_lower_shape_preserved':True,'boot_material_faces':[i for i,m in enumerate(materials) if m==2]}

def close_waist(pants,edit,rig,names):
    me=pants.data;p=np.array([v.co[:] for v in me.vertices]);uv=me.uv_layers[0];skin=s8.weights(pants,names);adj={};key=lambda i:tuple(np.round(p[i],5))
    for face in me.polygons:
        ids=list(face.vertices);lis=list(face.loop_indices)
        for j,(a,b) in enumerate(zip(ids,ids[1:]+ids[:1])):adj.setdefault(tuple(sorted((key(a),key(b)))),[]).append((a,b,uv.data[lis[j]].uv[:],uv.data[lis[(j+1)%len(ids)]].uv[:],face.material_index))
    edges=[v[0] for k,v in adj.items() if len(v)==1 and min(p[list(v[0][:2]),2])>.10]
    assert edges,'No trouser waist boundary'
    ps=[];ws=[];qs=[];fs=[];mi=[];attachments=[]
    for a,b,ua,ub,mat in edges:
        off=len(ps)
        for i,q in ((a,ua),(b,ub)):
            ps.append(p[i]);ws.append(skin[i]);qs.append(q);attachments.append([len(ps)-1,i])
        for i,q in ((b,ub),(a,ua)):
            v=p[i].copy();v[0]*=.97;v[1]=.035+(v[1]-.035)*.97;v[2]=.237
            ps.append(v);ws.append(skin[i]);qs.append((q[0],q[1]+(.035 if q[1]<.94 else -.035)))
        fs.append(list(range(off,off+4)));mi.append(mat)
    ob=upper.geometry(WAIST,ps,fs,qs,ws,me.materials[0],edit,rig,names)
    for mat in list(me.materials)[1:]:ob.data.materials.append(mat)
    for f,mat in zip(ob.data.polygons,mi):
        f.material_index=mat
        if np.dot(f.normal,[f.center.x,f.center.y-.035,0])<0:f.flip()
    ob.data.update();ob['construction']='Actual native trouser boundary continued behind the lowered belt and into the unchanged tunic; no exposed empty waist gap.'
    return ob,{'native_boundary_edges':[[a,b] for a,b,*_ in edges],'attachments':attachments,'top_z':.237}

def band_profile(d):
    p=np.array([native.C@Vector(v) for v in d['points']]);segments=[];selected=[]
    for i,face in enumerate(d['groups'][0]['faces']):
        q=p[face]
        if not (q[:,2].min()>.10 and q[:,2].max()<.25 and np.max(abs(q[:,0]))<.2):continue
        if 140<=i<=151:continue  # raised Bretonia buckle
        selected.append(i);hits=[]
        for a,b in zip(q,np.roll(q,-1,axis=0)):
            if (a[2]-.185)*(b[2]-.185)<0:
                t=(.185-a[2])/(b[2]-a[2]);hits.append((a+(b-a)*t)[:2])
        if len(hits)==2:segments.append(hits)
    # The original strap stops at the raised buckle. Close that concealed
    # interruption with a straight span between its actual left/right ends.
    points=[q for edge in segments for q in edge]
    a=max((q for q in points if q[0]<0),key=lambda q:q[1]);b=max((q for q in points if q[0]>0),key=lambda q:q[1]);segments.append([a,b])
    center=np.array([0,.04]);xy=[]
    for i in range(s14.COUNT):
        theta=2*math.pi*i/s14.COUNT;direction=np.array([math.sin(theta),math.cos(theta)]);radii=[]
        for a,b in segments:
            mat=np.column_stack((direction,a-b))
            if abs(np.linalg.det(mat))<1e-10:continue
            radius,t=np.linalg.solve(mat,a-center)
            if radius>0 and -1e-6<=t<=1+1e-6:radii.append(radius)
        assert radii,('No native BR belt section',i)
        xy.append(center+direction*(max(radii)+.0015))
    return np.array(xy),selected

def main():
    OUT.mkdir(exist_ok=True);path=TOP/'source/bretonia/source/bretonia.json.gz';d=json.loads(gzip.decompress(path.read_bytes()));rh=native.load('body')
    assert [(b['name'],b['native_bind']) for b in d['bones']]==[(b['name'],b['native_bind']) for b in rh['bones']]
    digest=s13.sha(PARENT);bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — step14 wide belt and former trousers');archive.hide_viewport=archive.hide_render=True
    originals={n:bpy.data.objects[n] for n in (s14.BASE,s14.BELT,s14.BUCKLE,s14.LOOPS,s14.WAIST)}
    beltmat=originals[s14.BELT].data.materials[0];gold=originals[s14.BUCKLE].data.materials[0];rhlatch=originals[s14.BUCKLE].data.materials[1]
    for ob in originals.values():native.move(ob,archive)
    names=[b['name'] for b in rh['bones']];rig=bpy.data.objects['RIG — native Rheinland'];pants,pr=lower(d,edit,rig,names);waist,wr=close_waist(pants,edit,rig,names)
    xy,selected=band_profile(d);surface=s8.SampleMesh(pants,names,lambda f:min(pants.data.vertices[i].co.z for i in f.vertices)>.05)
    belt,br=s14.belt_mesh(xy,surface,beltmat,edit,rig,names);belt.name=BELT
    buckle,loops,fr=s14.fittings(xy,surface,gold,rhlatch,edit,rig,names);buckle.name=BUCKLE;loops.name=LOOPS
    for v in belt.data.vertices:v.co.z=.158+(v.co.z-.171)*.63
    front=float(xy[0,1])
    for v in buckle.data.vertices:v.co.x*=.72;v.co.y=front+(v.co.y-front)*.75;v.co.z=.158+(v.co.z-.170)*.68
    for v in loops.data.vertices:v.co.z=.158+(v.co.z-.170)*.68
    # The native BR belt has a uniform two-bone binding, which fits the identical
    # male skeleton and keeps rigid fittings together as the waist turns.
    skin=np.zeros(len(names))
    for i,value in d['skin'][d['groups'][0]['faces'][30][0]].items():skin[names.index(d['bones'][int(i)]['name'])]=value
    for ob in (belt,buckle,loops):s8.set_weights(ob,np.tile(skin,(len(ob.data.vertices),1)));s9.recalc(ob)
    belt['construction']='Cross-section sampled from the actual BR elite belt at Z=.185; lowered/narrowed below the unchanged Hassler tunic. Height 54.18 mm, top .18509, bottom .13091.'
    report={'step':'15 BR elite trousers and boots; narrower lower belt under overhanging tunic','parent':str(PARENT),'parent_sha256':digest,'upper_unchanged':True,'donor':{'json':str(path),'json_sha256':s13.sha(path),'source':d['source'],'dfm_sha256':d['sha256'],'belt_faces':selected},'pants':pr,'belt':{'z_bounds':[.13091,.18509],'height_m':.05418,'previous_height_m':.086,'tunic_hem_z':.215,'vertical_gap_m':.02991,'profile_xy':xy.tolist(),'source_cross_section_z':.185,'skin':{names[i]:float(w) for i,w in enumerate(skin) if w>0}},'buckle':{'width_m':.066*.72,'height_m':.072*.68},'game_installed':False,'game_animations_validated':False}
    report['waist_closure']=wr
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2));native.activate(pants)
    scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(PARENT)==digest
    if '--no-render' not in sys.argv:
        render(scene,'full_front',(0,1,.03),(0,0,.99),2.08);render(scene,'waist_front',(0,1,.08),(0,.02,1.15),.59);render(scene,'waist_side',(1,0,.1),(0,.02,1.15),.59)
    print('STEP15 SAVED',flush=True)

if __name__=='__main__':main()
