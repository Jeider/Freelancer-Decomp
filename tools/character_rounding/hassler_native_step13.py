"""Texture the accepted collar and inner shirt using pinned native Wilham atlases."""
import sys,json,gzip,math,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step08 as s8
import hassler_native_step09 as s9
import hassler_native_step12 as s12
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_13';PARENT=s12.OUT/'hassler_native_upper.blend'
GARMENT='10 Sewn uniform — Wilham cloth collar'
SHIRT='12 Inner shirt — Wilham dark woven cloth'
COLLAR_UV='Collar grey cloth — Wilham UV';SHIRT_UV='Inner shirt — Wilham UV'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s9.OUT=OUT;s9.render(scene,label,direction,target,scale)

def cloth_material(name,texture,uvname,kind):
    mat=upper.material(name,(.2,.2,.2),.88,0.,texture)
    n=mat.node_tree.nodes;l=mat.node_tree.links;tex=next(x for x in n if x.type=='TEX_IMAGE');bs=n.get('Principled BSDF')
    tex.extension='EXTEND';uv=n.new('ShaderNodeUVMap');uv.uv_map=uvname;l.new(uv.outputs[0],tex.inputs['Vector'])
    bw=n.new('ShaderNodeRGBToBW');l.new(tex.outputs['Color'],bw.inputs[0])
    if kind=='collar':
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.025;ramp.color_ramp.elements[0].color=(.055,.059,.058,1)
        ramp.color_ramp.elements[1].position=.65;ramp.color_ramp.elements[1].color=(.24,.26,.25,1)
        l.new(bw.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
    else:
        power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=.72;l.new(bw.outputs[0],power.inputs[0])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.004,.005,.006,1);ramp.color_ramp.elements[1].color=(.38,.41,.43,1)
        l.new(power.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
    mat['donor_texture']=texture;mat['purpose']='Native diffuse cloth; no procedural bump, displacement or geometry change'
    tex.image.pack()
    return mat

def interpolate_extras(me,rows,mapping,ids):
    segments=[(a,b) for row in rows for a,b in zip(row,row[1:])]+[(a[j],b[j]) for a,b in zip(rows,rows[1:]) for j in range(6)]
    p=np.array([v.co[:] for v in me.vertices])
    for i in ids-set(mapping):
        best=None
        for a,b in segments:
            d=p[b]-p[a];t=float(np.clip(np.dot(p[i]-p[a],d)/max(np.dot(d,d),1e-15),0,1));dist=np.linalg.norm(p[i]-p[a]-t*d)
            if best is None or dist<best[0]:best=(dist,(1-t)*np.array(mapping[a])+t*np.array(mapping[b]))
        assert best[0]<1e-5,(i,best[0]);mapping[i]=best[1]

def collar(old,edit,archive,texture):
    ob=s8.clone(old,GARMENT,edit,archive);me=ob.data;faces,rows=s12.collar_rows(ob)
    layer=me.uv_layers.new(name=COLLAR_UV)
    for a,b in zip(layer.data,me.uv_layers[0].data):a.uv=b.uv
    arc=[0.]
    for a,b in zip(rows,rows[1:]):arc.append(arc[-1]+(me.vertices[a[2]].co-me.vertices[b[2]].co).length)
    widths=[sum((me.vertices[b].co-me.vertices[a].co).length for a,b in zip(row,row[1:])) for row in rows]
    mapping={}
    # The donor's narrow collar strip stretches its weave across Hassler's broad
    # lapel. Use the same grey uniform fabric from the larger uninterrupted back
    # field instead, avoiding straps/pockets. Arc length and physical transverse
    # width keep one continuous chart across the whole folded collar.
    for row,distance in zip(rows,arc):
        u=.06+.56*distance/arc[-1];width=0.
        for j,i in enumerate(row):
            if j:width+=(me.vertices[i].co-me.vertices[row[j-1]].co).length
            mapping[i]=(u,.57+.80*width)
    ids={i for f in faces for i in me.polygons[f].vertices};interpolate_extras(me,rows,mapping,ids)
    for f in faces:
        for li,i in zip(me.polygons[f].loop_indices,me.polygons[f].vertices):layer.data[li].uv=mapping[i]
    mat=cloth_material('Hassler 13 — Wilham grey collar cloth',texture,COLLAR_UV,'collar')
    for slot in (4,15,22,33):me.materials[slot]=mat
    me.uv_layers.active_index=0;ob['collar_inside']='Both sides use grey Wilham collar cloth; red edge remains the accepted separate piping'
    return ob,{'uv_layer':COLLAR_UV,'material':mat.name,'slots':[4,15,22,33],'faces':faces,'source_uv_bounds':[.06,.57,.62,.57+.80*max(widths)],'source':'Wilham atlas 2, uninterrupted grey upper-back cloth. Narrow donor collar strip rejected because its weave stretched across Hassler wide lapels.','mapping':{str(i):list(q) for i,q in mapping.items()},'arc_length_m':arc[-1],'max_unfolded_width_m':max(widths),'geometry_unchanged':True}

def shirt(old,edit,archive,texture):
    ob=s8.clone(old,SHIRT,edit,archive);me=ob.data;layer=me.uv_layers.new(name=SHIRT_UV)
    p=np.array([v.co[:] for v in me.vertices]);lower=min(p[:6*48,2]);upper=float(np.mean(p[6*48:7*48,2]))
    # A continuous cylindrical chart, with its only seam at the concealed back.
    # The donor's folded black undershirt is the top-right island of atlas 2.
    for face in me.polygons:
        angles=[(2*math.pi*(i%48)/48+math.pi)%(2*math.pi)-math.pi for i in face.vertices]
        if max(angles)-min(angles)>math.pi:angles=[a+2*math.pi if a<0 else a for a in angles]
        for li,i,a in zip(face.loop_indices,face.vertices,angles):
            t=float(np.clip((p[i,2]-lower)/(upper-lower),0,1));v=.55+.35*t
            width=.085-.040*t;u=.868+width*math.sin(a/2)
            layer.data[li].uv=(u,v)
    mat=cloth_material('Hassler 13 — Wilham charcoal shirt folds',texture,SHIRT_UV,'shirt')
    for i in range(len(me.materials)):me.materials[i]=mat
    me.uv_layers.active_index=0;ob['texturing']='Native Wilham black undershirt; separate cylindrical UV with seam at the back; open neck and skin weights unchanged'
    return ob,{'uv_layer':SHIRT_UV,'material':mat.name,'source_uv_bounds':[.783,.55,.953,.90],'source':'Black folded undershirt island, not a metal or leather patch','geometry_unchanged':True}

def main():
    OUT.mkdir(parents=True,exist_ok=True);donor=TOP/'source/wilham.json.gz';d=json.loads(gzip.decompress(donor.read_bytes()));digest=sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — accepted step12 before cloth texturing');archive.hide_render=archive.hide_viewport=True
    coat,c=collar(bpy.data.objects[s12.GARMENT],edit,archive,d['groups'][2]['texture'])
    inner,s=shirt(bpy.data.objects[s12.SHIRT],edit,archive,d['groups'][2]['texture'])
    report={'step':'13 Wilham cloth textures on accepted step12 geometry','parent':str(PARENT),'parent_sha256':digest,'accepted_shape':{'step':12,'user_quote':'давай пока так оставим. мне нравится. теперь идём дальше.','sha256':digest},'donor':{'source':d['source'],'source_sha256':d['sha256'],'pinned_model':str(TOP/'source/rh_wilham_body.dfm'),'json':str(donor),'json_sha256':sha(donor),'textures':[{'path':d['groups'][i]['texture'],'sha256':sha(Path(d['groups'][i]['texture']))} for i in (0,2)]},'collar':c,'shirt':s,'geometry_unchanged':True,'game_installed':False,'game_animations_validated':False}
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(coat);scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert sha(PARENT)==digest
    if '--no-render' not in sys.argv:
        render(scene,'front',(0,1,0));render(scene,'collar_close',(.18,1,.15),(0,.02,1.53),.55)
    print('STEP13 SAVED',flush=True)

if __name__=='__main__':main()
