"""Audit the approved editable Hassler for native export without game writes."""
import sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'game';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(TOP/'step_17/hassler_native_upper.blend'));configure('character_rounding');bpy.context.scene.frame_set(1)
rig=bpy.data.objects['RIG — native Rheinland'];objects=[];materials={}
for ob in bpy.data.collections['EDIT — native costume upper study'].objects:
    if ob.type!='MESH':continue
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    objects.append({'name':ob.name,'base_vertices':len(ob.data.vertices),'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'uv_layers':[q.name for q in me.uv_layers],'modifiers':[(m.name,m.type,m.show_render,m.show_viewport) for m in ob.modifiers],'matrix':np.array(ob.matrix_world).tolist()})
    for mi in {p.material_index for p in me.polygons}:
        mat=me.materials[mi]
        if mat.name in materials:continue
        bs=mat.node_tree.nodes.get('Principled BSDF')
        materials[mat.name]={'nodes':[{'name':n.name,'type':n.type,'uv':getattr(n,'uv_map',None),'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None,'image_size':list(n.image.size) if n.type=='TEX_IMAGE' and n.image else None} for n in mat.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links],'base_color':list(bs.inputs['Base Color'].default_value) if bs else None,'roughness':float(bs.inputs['Roughness'].default_value) if bs else None,'metallic':float(bs.inputs['Metallic'].default_value) if bs else None}
    ev.to_mesh_clear()
bones=[{'name':b.name,'matrix':np.array(b.matrix_local).tolist(),'native_inverse_bind':list(b['native_inverse_bind']),'original_native_inverse_bind':list(b['original_native_inverse_bind']) if 'original_native_inverse_bind' in b else None} for b in rig.data.bones]
r={'objects':objects,'materials':materials,'bones':bones,'rig_world':np.array(rig.matrix_world).tolist()}
(OUT/'source_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'objects':[(o['name'],o['vertices'],o['triangles']) for o in objects],'materials':{n:[a['type'] for a in m['nodes']] for n,m in materials.items()}},ensure_ascii=False),flush=True)
