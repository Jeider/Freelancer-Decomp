"""Compare stripe interpretations offline; never writes into the game tree."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/tradelane_stripe_fix'
OUT.mkdir(parents=True, exist_ok=True)
game_shader = Path('D:/Games/FL_MOD/DATA_EXTRA/SHADERS/tradelane_corridor.hlsl')
before = hashlib.sha256(game_shader.read_bytes()).hexdigest()
current = (ROOT / 'DATA_EXTRA/SHADERS/tradelane_corridor.hlsl').read_text()
original = (ROOT / 'out/tradelane_mix/corridor_before_install.hlsl').read_text()
# Compare the original material without reintroducing its refraction pass.
original = original[:original.index('float4 PSWarp(')] + current[current.index('float4 PSWarp('):]
variants = [('installed', 'До: прореживание участками', game_shader.read_text()),
            ('restored', 'После: полный объём трубы, шаг фактуры ×4', current)]

vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')] + [Path('C:/DXSDK_Jun10/Include')]))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')] + [Path('C:/DXSDK_Jun10/Lib/x86')]))
exe = OUT/'preview.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/O2', '/EHsc', '/MT', '/D_CRT_SECURE_NO_WARNINGS',
                str(ROOT/'tools/tradelane/bands_preview.cpp'), '/Fe'+str(exe), '/link', 'd3d9.lib', 'd3dx9.lib', 'user32.lib'], cwd=OUT, env=env, check=True)
sheet = Image.new('RGB', (960, 590*len(variants)), (10, 14, 22))
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
for i, (name, title, source) in enumerate(variants):
    folder = OUT/name
    folder.mkdir(exist_ok=True)
    shader = folder/'corridor.hlsl'
    shader.write_text(source)
    with (folder/'render.log').open('w') as log:
        subprocess.run([str(exe), str(shader), str(folder)+os.sep, 'still'], cwd=ROOT, stdout=log, stderr=log, check=True)
    sheet.paste(Image.open(folder/'preview.png').convert('RGB'), (0, i*590+50))
    draw.text((16, i*590+12), title, font=font, fill='white')
    print('Rendered', name, flush=True)
    if '--video' in sys.argv and name == 'restored':
        with (folder/'video.log').open('w') as log:
            renderer = subprocess.Popen([str(exe), str(shader), str(folder)+os.sep, 'video'], cwd=ROOT, stdout=subprocess.PIPE, stderr=log)
            try:
                subprocess.run(['C:/ffmpeg/bin/ffmpeg.exe', '-y', '-hide_banner', '-loglevel', 'error',
                                '-f', 'rawvideo', '-pixel_format', 'bgra', '-video_size', '960x540',
                                '-framerate', '60', '-i', 'pipe:0', '-an', '-c:v', 'libx264', '-preset', 'fast',
                                '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(folder/'preview.mp4')],
                               stdin=renderer.stdout, check=True)
            finally:
                renderer.stdout.close()
                code = renderer.wait()
            if code:
                raise RuntimeError(f'Video renderer failed: {code}')
        subprocess.run(['C:/ffmpeg/bin/ffmpeg.exe', '-y', '-hide_banner', '-loglevel', 'error',
                        '-ss', '2', '-i', str(folder/'preview.mp4'), '-vf', 'fps=1,scale=640:360,tile=2x2',
                        '-frames:v', '1', str(folder/'motion.png')], check=True)
sheet.save(OUT/'comparison.png')
assert hashlib.sha256(game_shader.read_bytes()).hexdigest() == before, 'Game shader changed during preview'
print('Offline comparison:', OUT/'comparison.png')
