"""Validate vector cursor pixels on a hidden D3D9 hardware device."""
import subprocess
import hashlib
import json
from check import ROOT, OUT, VC, compiler_env
from PIL import Image, ImageDraw

OUT.mkdir(parents=True,exist_ok=True)
env=compiler_env()
env['INCLUDE']+=';C:/DXSDK_Jun10/Include'
subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/DNOMINMAX',
    f'/I{ROOT/"src/freelancer/Client"}',str(ROOT/'tools/cursors/check_gpu.cpp'),'/Fecheck_gpu.exe',
    '/link','d3d9.lib','user32.lib'],cwd=OUT,env=env,check=True)
subprocess.run([str(OUT/'check_gpu.exe'),str(OUT)],cwd=ROOT,check=True)
Image.frombytes('RGB',(320,320),(OUT/'gpu_arrow.bgra').read_bytes(),'raw','BGRX').save(OUT/'gpu_arrow.png')
names=['neutral','hostile_fire','talk_empty','talk_rumor','arrow','no_fire','friendly','cross',
       'talk_equip_dealer','talk_mission','talk_info','talk_bribe','talk_commodity_dealer','talk_ship_dealer','talk_story','stretch']
for light in (0,1):
    sheet=Image.new('RGB',(16*250,4*290),(22,28,38))
    draw=ImageDraw.Draw(sheet)
    for row,height in enumerate((720,1080,1440,2160)):
        for col,name in enumerate(names):
            shot=Image.frombytes('RGB',(320,320),(OUT/f'size_{name}_{height}_{light}.bgra').read_bytes(),'raw','BGRX')
            # Full native-size tile, no resampling: compare real on-screen strokes.
            factor=.25 if name=='arrow' else .175 if name.startswith('talk_') else .1 if name=='cross' else .1125
            side=round(256*factor*height/600)
            tile=shot.crop((32,32,32+side,32+side))
            # Allow enough room for the full 4K arrow tile.
            sheet.paste(tile,(col*250,row*290+35))
            draw.text((col*250+2,row*290+3),f'{height} {name.replace("talk_", "")}',fill='white')
    sheet.save(OUT/f'gpu_native_sizes_{light}.png')
paths=[ROOT/'src/freelancer/Client/cursor_vector_art.h',ROOT/'src/freelancer/Client/icon_vector_raster.h',ROOT/'src/freelancer/Client/base_icon_art.h',ROOT/'src/freelancer/Client/nn_icon_art.h',ROOT/'tools/cursors/check_gpu.cpp']
(OUT/'gpu_verified.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))

