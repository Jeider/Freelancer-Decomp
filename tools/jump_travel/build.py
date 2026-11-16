"""Compile and run the real D3D9 prototype; --video produces a 60 fps MP4."""
from pathlib import Path
import os, subprocess, sys
root=Path(__file__).resolve().parents[2]
out=root/'out/jump_travel';out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[Path('C:/DXSDK_Jun10/Include')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]+[Path('C:/DXSDK_Jun10/Lib/x86')]))
exe=out/'preview.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/D_CRT_SECURE_NO_WARNINGS',str(root/'tools/jump_travel/preview.cpp'),'/Fe'+str(exe),'/link','d3d9.lib','d3dx9.lib','user32.lib'],cwd=out,env=env,check=True)
with (out/'checks.log').open('w') as log:
    subprocess.run([str(exe)],cwd=root,stderr=log,check=True)
print((out/'checks.log').read_text())
if '--video' in sys.argv:
    with (out/'video.log').open('w') as log:
        renderer=subprocess.Popen([str(exe),'--video'],cwd=root,stdout=subprocess.PIPE,stderr=log)
        try:
            subprocess.run(['C:/ffmpeg/bin/ffmpeg.exe','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','bgra','-video_size','1280x720','-framerate','60','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'jump_travel_prototype.mp4')],stdin=renderer.stdout,check=True)
        finally:
            renderer.stdout.close()
            code=renderer.wait()
        if code:raise RuntimeError(f'GPU renderer failed: {code}')
    print(out/'jump_travel_prototype.mp4')
