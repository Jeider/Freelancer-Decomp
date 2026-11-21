"""Render the saved prototype's actual keyed motion; never launch the game."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
OUT=HERE.parents[1]/'out/ship_design/rh_fighter/prototypes/f01_uv_01'
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant in ('f01_uv_01','f01_uv_02','f01_uv_03')
    OUT=OUT.parent/variant


def main():
    data=json.loads((OUT/'geometry.json').read_text(encoding='utf8'))
    blend=OUT/data['blend_basename']
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene=bpy.data.scenes['04 Motion study - timeline'];bpy.context.window.scene=scene
    # Read actual keyed object transforms from the reopened file, for comparison
    # against the independently exported static CMP poses.
    conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    samples=[]
    for frame in (1,37,73,90,113,127,150,180,240):
        scene.frame_set(frame)
        transforms={}
        for name in data.get('motion',{}):
            obj=next(o for o in scene.objects if o.animation_data and (o.name==name or o.name.startswith(name+'.')))
            matrix=conversion.transposed()@obj.matrix_world@conversion
            transforms[name]=[list(row) for row in matrix]
        samples.append(dict(frame=frame,game_matrices=transforms))
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4
    scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX'
    scene.render.resolution_x=840;scene.render.resolution_y=600;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.camera.data.ortho_scale=15.8
    # Low three-quarter view exposes the blade angle and carrier travel.
    center=Vector((0,1.25,.15));direction=Vector((1,1.15,.45) if OUT.name in ('f01_uv_02','f01_uv_03') else (1,.9,1.15)).normalized()
    scene.camera.location=center+direction*35
    scene.camera.rotation_euler=(center-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    temp=OUT/'motion_frames';temp.mkdir(exist_ok=True);paths=[]
    for i,frame in enumerate(range(1,241,3)):
        scene.frame_set(frame);path=temp/f'{i:04d}.png';paths.append(path)
        scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        if i%10==0:print('MOTION_FRAME',i,flush=True)
    target=OUT/'roof_and_wing_motion.mp4'
    subprocess.run(['C:/ffmpeg/bin/ffmpeg.exe','-hide_banner','-loglevel','error','-y',
        '-framerate','10','-i',str(temp/'%04d.png'),'-c:v','libx264','-crf','20',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
    probe=subprocess.check_output(['C:/ffmpeg/bin/ffprobe.exe','-v','error','-count_frames',
        '-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height,duration','-of','json',str(target)],text=True)
    info=json.loads(probe);assert int(info['streams'][0]['nb_read_frames'])==len(paths)
    report=dict(blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),
        movie_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),probe=info,
        source_frames=list(range(1,241,3)),keyed_pose_samples=samples,offline=True)
    (OUT/'motion_preview.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    # Only this invocation's exact intermediate paths, contained in this topic.
    root=OUT.resolve();assert temp.resolve().is_relative_to(root) and not temp.is_symlink()
    for path in paths:
        assert path.resolve().is_relative_to(temp.resolve()) and not path.is_symlink()
        path.unlink()
    if not any(temp.iterdir()):temp.rmdir()
    print('MOTION_PREVIEW_READY',target,flush=True)


if __name__=='__main__':main()
