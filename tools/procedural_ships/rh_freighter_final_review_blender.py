"""Reopen final assets, verify full motion, save a review blend with hidden LOD/damage collections."""
import json,sys,hashlib
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_freighter_rig_blender as review
from rh_concept_b_final_blender import mesh_object,C
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/rh_pir_freighter'

def main():
    review.OUT=OUT/'review';sys.argv=['review','--quick','--review-open'];review.main()
    data=json.loads((review.OUT/'extra_geometry.json').read_text());collections=[]
    for level,parts in enumerate(data['levels'],1):
        col=bpy.data.collections.new('LOD '+str(level)+' / static flight inspection');bpy.context.scene.collection.children.link(col)
        for name,gs in parts.items():
            ob,_=mesh_object(dict(groups=gs),name+' LOD '+str(level))
            for owner in list(ob.users_collection):owner.objects.unlink(ob)
            col.objects.link(ob)
        col.hide_viewport=True;col.hide_render=True;collections.append(col.name)
    # Static damaged assembly contains the surviving part in its exact HP placement.
    col=bpy.data.collections.new('Damage / static flight assembly');bpy.context.scene.collection.children.link(col)
    damaged={x['part'] for x in data['damage']}
    for original in list(bpy.context.scene.objects):
        if original.type!='MESH' or original.name in damaged or '_btn_' in original.name or ' LOD ' in original.name:continue
        clone=original.copy();clone.data=original.data;clone.animation_data_clear();clone.parent=None;clone.matrix_world=original.matrix_world.copy();clone.name='Surviving '+original.name;col.objects.link(clone)
    mats=json.loads((OUT/'blender_input.json').read_text())['materials']
    for key,m in mats.items():
        if key in bpy.data.materials:continue
        mat=bpy.data.materials.new(key);mat.use_nodes=True;mat.use_backface_culling=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.85
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(m['image_path'],check_existing=True);tex.image.pack()
        mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*m['colour'],1)
        mat.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
    for e in data['damage']:
        ob,_=mesh_object(e,'Damaged '+e['zone'])
        for owner in list(ob.users_collection):owner.objects.unlink(ob)
        col.objects.link(ob)
    col.hide_viewport=True;col.hide_render=True;collections.append(col.name)
    bpy.context.scene.frame_set(211);path=OUT/'rh_pir_freighter.blend'
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
    assert bpy.context.scene.frame_current==211
    for name in collections:assert bpy.data.collections[name].hide_render and bpy.data.collections[name].hide_viewport
    (OUT/'blend_check.json').write_text(json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),saved_reopened=True,frame=211,hidden_collections=collections),indent=2))
    print('FINAL BLEND READY',path,flush=True)

if __name__=='__main__':main()
