"""Import the supplied FBX, inspect it and render source-only orthographic views."""
import sys,json,hashlib,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from blender_workspace import configure
configure('character_rounding')
OUT=ROOT/'out/character_rounding/hassler';SOURCE=Path('D:/Work/Meshy/Hassler1')

def studio(scene):
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        if any(d.use for d in prefs.devices):scene.cycles.device='GPU'
    except Exception:pass
    scene.render.resolution_x=700;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.13,.13,1)
    scene.view_settings.view_transform='AgX'
    for loc,power,size in [((-3,4,4),450,3),((3,2,2),280,2.5),((1,-4,3),500,2)]:
        ld=bpy.data.lights.new('Softbox','AREA');ld.energy=power;ld.size=size
        ob=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(ob);ob.location=loc
        ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam)
    scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.3;cam.data.clip_start=.001
    return cam

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True);configure('character_rounding')
    bpy.ops.import_scene.fbx(filepath=str(next(SOURCE.glob('*.fbx'))))
    report={'objects':[]}
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob.select_set(False)
        p=np.array([v.co[:] for v in ob.data.vertices])
        report['objects'].append({'name':ob.name,'vertices':len(p),'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons),
              'bounds':[p.min(0).tolist(),p.max(0).tolist()],'materials':[m.name for m in ob.data.materials],
              'vertex_groups':[g.name for g in ob.vertex_groups]})
    for im in bpy.data.images:
        if im.source=='FILE':
            p=SOURCE/Path(im.filepath.replace('\\','/')).name
            if p.exists():im.filepath=str(p);im.reload()
    report['images']=[{'name':im.name,'path':im.filepath,'size':list(im.size)} for im in bpy.data.images]
    folder=OUT/'source_preview';folder.mkdir(exist_ok=True)
    (OUT/'meshy_audit.json').write_text(json.dumps(report,indent=2))
    # Normalize a temporary preview instance only; source geometry stays untouched.
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];p=np.array([o.matrix_world@v.co for o in meshes for v in o.data.vertices])
    lo,hi=p.min(0),p.max(0);scale=1.9/(hi[2]-lo[2]);offset=(lo+hi)*.5;offset[2]=lo[2]
    for ob in meshes:
        for v in ob.data.vertices:v.co=(v.co-Vector(offset))*scale
    cam=studio(bpy.context.scene)
    for label,direction in [('plus_y',(0,1,0)),('minus_y',(0,-1,0)),('side',(1,0,0))]:
        cam.location=Vector((0,0,.95))+Vector(direction)*5
        cam.rotation_euler=(-Vector(direction)).to_track_quat('-Z','Y').to_euler()
        bpy.context.scene.render.filepath=str(folder/(label+'.png'));bpy.ops.render.render(write_still=True)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
