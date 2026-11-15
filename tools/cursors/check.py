"""Compile/run the game's vector rasterizer; export its actual pixels, not AI art."""
from pathlib import Path
import os
import subprocess
import hashlib
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/cursor_vectors'
VC = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
SDK = Path('C:/Program Files (x86)/Windows Kits/10')
VERSION = '10.0.26100.0'

def compiler_env():
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(map(str, [VC/'include'] + [SDK/'Include'/VERSION/x for x in ('ucrt','shared','um')]))
    env['LIB'] = ';'.join(map(str, [VC/'lib/x86'] + [SDK/'Lib'/VERSION/x/'x86' for x in ('ucrt','um')]))
    return env

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'), '/nologo','/std:c++17','/O2','/EHsc','/MT','/DNOMINMAX',
        f'/I{ROOT/"src/freelancer/Client"}',str(ROOT/'tools/cursors/check.cpp'),'/Fecheck.exe'],
        cwd=OUT,env=compiler_env(),check=True)
    subprocess.run([str(OUT/'check.exe'), str(OUT)],cwd=ROOT,check=True)
    names = ['neutral','hostile_fire','talk_empty','talk_rumor','arrow','no_fire','friendly','cross',
        'talk_equip_dealer','talk_mission','talk_info','talk_bribe','talk_commodity_dealer','talk_ship_dealer','talk_story','stretch']
    atlas = Image.new('RGBA',(1024,1024),(12,20,32,255))
    for i,name in enumerate(names):
        # Renderer output is already top-down BGRA; do NOT flip like the old TGA.
        im = Image.frombytes('RGBA',(256,256),(OUT/f'{name}_256.bgra').read_bytes(),'raw','BGRA')
        im.save(OUT/f'{name}.png')
        atlas.alpha_composite(im,((i%4)*256,(i//4)*256))
    atlas.convert('RGB').save(OUT/'vector_runtime_preview.png')
    small=Image.new('RGBA',(1024,170),(12,20,32,255))
    draw=ImageDraw.Draw(small)
    for i,name in enumerate(names):
        im=Image.frombytes('RGBA',(64,64),(OUT/f'{name}_64.bgra').read_bytes(),'raw','BGRA')
        small.alpha_composite(im,(i*64,12))
        draw.text((i*64+18,90),str(i+1),fill='white')
    small.convert('RGB').save(OUT/'vector_small_preview.png')
    print('Preview:',OUT/'vector_runtime_preview.png')
    paths=[ROOT/'src/freelancer/Client/cursor_vector_art.h',ROOT/'src/freelancer/Client/icon_vector_raster.h',ROOT/'src/freelancer/Client/base_icon_art.h',ROOT/'src/freelancer/Client/nn_icon_art.h',ROOT/'tools/cursors/check.cpp']
    (OUT/'cpu_verified.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))

if __name__=='__main__':main()
