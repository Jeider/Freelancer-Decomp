"""Render material comparisons or a geometry prototype with original textures."""
from pathlib import Path
import os, sys, subprocess, hashlib, json, re
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools'))
from repair_panel_normals import leaves
matter_fast='--matter-fast' in sys.argv
matter_textured='--matter-textured' in sys.argv
matter_light='--matter-light' in sys.argv
cloud_reference='--cloud-reference' in sys.argv
matter_parallax='--matter-parallax' in sys.argv or matter_light or cloud_reference
matter='--matter' in sys.argv or matter_fast or matter_textured or matter_parallax
energy='--energy' in sys.argv or matter
classic='--classic' in sys.argv or energy
assets=root/'out/jump_travel/comparison';assets.mkdir(parents=True,exist_ok=True)
out=root/('out/jump_travel/cloud_reference' if cloud_reference else 'out/jump_travel/matter_light' if matter_light else 'out/jump_travel/matter_parallax' if matter_parallax else 'out/jump_travel/matter_textured' if matter_textured else 'out/jump_travel/matter_fast' if matter_fast else 'out/jump_travel/matter' if matter else 'out/jump_travel/energy' if energy else 'out/jump_travel/classic' if classic else 'out/jump_travel/comparison');out.mkdir(parents=True,exist_ok=True)
texture=Path('D:/Games/FL_MOD/DATA/FX/jumpeffect.txm')
if cloud_reference:
    import prepare_game
    # Read existing presets only; never write Pythonlancer's DATA tree.
    presets=[]
    for block in re.split(r'(?mi)^\[gate_tunnel\]',Path('D:/Games/FL_MOD/DATA/FX/gate_tunnel.ini').read_text()):
        if not re.search(r'(?mi)^hyperspace_clouds\s*=\s*1',block):continue
        name=re.search(r'(?mi)^nickname\s*=\s*(\w+)',block)[1]
        colours=re.findall(r'(?mi)^color\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)',block)
        if len(colours)!=2:raise ValueError(name)
        presets.append(name+' '+' '.join(str(int(c)/255) for colour in colours for c in colour))
    (out/'palettes.txt').write_text('\n'.join(presets))
for name,_,data in leaves(texture.read_bytes())[1]:
    for key in ('jumptube','jumptube5'):
        if name.lower().endswith('/'+key+'/mips'):(assets/(key+'.dds')).write_bytes(data)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231');sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[Path('C:/DXSDK_Jun10/Include')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]+[Path('C:/DXSDK_Jun10/Lib/x86')]))
exe=out/'compare.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/D_CRT_SECURE_NO_WARNINGS',str(root/'tools/jump_travel/compare.cpp'),'/Fe'+str(exe),'/link','d3d9.lib','d3dx9.lib','user32.lib'],cwd=out,env=env,check=True)
args=['--cloud-reference'] if cloud_reference else ['--matter-light'] if matter_light else ['--matter-parallax'] if matter_parallax else ['--matter-textured'] if matter_textured else ['--matter-fast'] if matter_fast else ['--matter'] if matter else ['--energy'] if energy else ['--classic'] if classic else []
if '--cloud-diagnostic' in sys.argv:args.append('--cloud-diagnostic')
subprocess.run([str(exe),*args],cwd=root,check=True)
if '--cloud-diagnostic' in sys.argv:sys.exit(0)
if '--check-only' in sys.argv:
    if cloud_reference:
        from PIL import Image, ImageDraw
        sheet=Image.new('RGB',(960,202*((len(presets)+2)//3)),(12,15,22))
        draw=ImageDraw.Draw(sheet)
        for i,preset in enumerate(presets):
            name=preset.split()[0];x=(i%3)*320;y=(i//3)*202
            sheet.paste(Image.open(out/('palette_'+name+'.png')).resize((320,180)),(x,y+22))
            draw.text((x+5,y+4),name,fill='white')
        sheet.save(out/'palettes.png')
    sys.exit(0)
renderer=subprocess.Popen([str(exe),'--video',*args],cwd=root,stdout=subprocess.PIPE)
try:
    subprocess.run(['C:/ffmpeg/bin/ffmpeg.exe','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','bgra','-video_size','1920x540','-framerate','60','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'comparison_raw.mp4')],stdin=renderer.stdout,check=True)
finally:
    renderer.stdout.close();code=renderer.wait()
if code:raise RuntimeError(code)
if classic:
    # Lossless crop of the raw rendered half is unnecessary: CRF 18 preserves
    # the same viewing quality while providing an easy standalone preview.
    subprocess.run(['C:/ffmpeg/bin/ffmpeg.exe','-y','-hide_banner','-loglevel','error','-i',str(out/'comparison_raw.mp4'),'-vf','crop=960:540:960:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'tunnel.mp4')],check=True)
from PIL import Image, ImageDraw, ImageFont
sheet=Image.new('RGB',(1920,596),(12,15,22));draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
for x,filename,title in [(0,'base.png','Базовый вариант'),(960,'new.png' if classic else 'current.png','Новая геометрия, исходные текстуры' if classic else 'Базовый материал + текущий шейдер')]:
    if energy and x:title='Новый энергетический туннель'
    if matter and x:title='Плотная клубящаяся материя'
    if matter_fast and x:title='Материя: скорость ×2, усиленный контраст'
    if matter_textured and x:title='Материя: скорость ×4, фактура оригинала'
    if matter_parallax and x:title='Пролёт −30%, динамичная фактура, стабильная камера'
    if matter_light and x:title='Материя и свет в глубине туннеля'
    if cloud_reference and x:title='Облачный туннель по референсам'
    sheet.paste(Image.open(out/filename).convert('RGB'),(x,56));draw.text((x+18,15),title,font=font,fill='white')
sheet.save(out/'comparison.png')
sheet.crop((0,0,1920,56)).save(out/'labels.png')
subprocess.run(['C:/ffmpeg/bin/ffmpeg.exe','-y','-hide_banner','-loglevel','error','-i',str(out/'comparison_raw.mp4'),'-i',str(out/'labels.png'),'-filter_complex','[1:v][0:v]vstack=inputs=2[v]','-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'comparison.mp4')],check=True)
report={'scope':'Material comparison, synthetic shared path, not an in-game/retail capture. Uses live jumpeffect.txm and current hyperspace_tunnel.hlsl. No launch, refraction, ship or ALE layers.','texture_sha256':hashlib.sha256(texture.read_bytes()).hexdigest(),'shader_sha256':hashlib.sha256((root/'DATA_EXTRA/SHADERS/hyperspace_tunnel.hlsl').read_bytes()).hexdigest()}
if classic:
    report['scope']='Geometry prototype, not an in-game/retail capture. Left: previous comparison reference. Right: new continuous swept path. Both use the same original textures and texture-times-vertex-colour material; no cloud overlay.'
    report['geometry_sha256']=hashlib.sha256((root/'tools/jump_travel/classic_mesh.h').read_bytes()).hexdigest()
if energy:
    report['scope']='Standalone art prototype, not a game capture. Left: baseline reference from previous comparisons. Right: new procedural energy material on a curved two-shell mesh; does not sample the original textures. No ship or jump transitions.'
    report['energy_shader_sha256']=hashlib.sha256((root/'tools/jump_travel/energy_tunnel.hlsl').read_bytes()).hexdigest()
if matter:
    report['scope']='Standalone art prototype, not game footage. Left: previous baseline reference. Right: empty-space traversal and dense turbulent volume integration, new shader. No ship, transitions or in-game performance validation.'
    report.pop('energy_shader_sha256',None)
    report.pop('geometry_sha256',None)
    report['matter_shader_sha256']=hashlib.sha256((root/'tools/jump_travel/matter_tunnel.hlsl').read_bytes()).hexdigest()
    report['simulation_speed']=8 if matter_parallax else 4 if matter_textured else 2 if matter_fast else 1
    report['simulation_start']=3
    report['original_style_contrast']=matter_fast or matter_textured or matter_parallax
    report['original_textures_on_matter']=matter_textured or matter_parallax
    if matter_parallax:
        report['camera_travel_speed']=5.6
        report['camera_speed_relative_to_requested_x8']=.7
        report['material_advection_speed']=8
        report['deformation_rate_relative_to_material_clock']=2
        report['camera']='Fixed world-forward orientation; shallow slow path; no angular shake.'
        report['texture_depth']='Texture displaces 3D density boundary; separately advected inner membrane at 0.55 units; material sampled per volume step.'
if matter_light:
    report['distant_light']='World-space source on centreline 52 units ahead; bright core and soft halo occluded by integrated matter opacity; depth-weighted illumination of folds.'
if cloud_reference:
    report={'scope':'Standalone cloud art study based on user image references; not game footage. No retail textures sampled in new effect. Rolling volume with a seamless baked modulation texture; broad cubic spline turns with calm camera following.',
            'shader_sha256':hashlib.sha256((root/'DATA_EXTRA/SHADERS/jump_cloud.hlsl').read_bytes()).hexdigest(),
            'camera_travel_speed':11.2,'material_clock_speed':16,
            'retail_textures_bound':False,'modulation_texture_sha256':hashlib.sha256((root/'DATA_EXTRA/FX/JUMP_CLOUD/modulation.png').read_bytes()).hexdigest(),
            'modulation_net_pan_uv_per_second':-.7408,'path':'Catmull-Rom, 32-unit segments, width 12, height 8; smoothed camera tangent -12/+20 units; no camera roll',
            'wall_rotation':'None: fixed cross-section, no axial twist or circumferential texture pan; animated cloud deformation only',
            'tunnel_depth':240,'depth_fade_start':80,'depth_fade_end':225,
            'destination':'No endpoint sphere or halo; illuminated cloud walls and diffuse depth fade only.',
            'validation':'Pause pixel-identical; cloud deformation verified with camera locked; continuous moving destination along bends; authored palettes rendered; no in-game performance validation.'}
(out/'manifest.json').write_text(json.dumps(report,indent=2))
print(out/'comparison.png');print(out/'comparison.mp4')
if classic:print(out/'tunnel.mp4')
