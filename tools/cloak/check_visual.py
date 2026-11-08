"""Exercise the production cloak decoder on installed ship assets and shader on D3D9 HAL."""
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/nebula_control')]
from generate_station_lods import read_tree,crc
from build_asf_hq import compiler_env
OUT=ROOT/'src/obj/cloak_visual'


def walk(nodes,path=()):
    for n in nodes:
        p=path+(n.name,)
        if n.blob is not None:yield p,n.blob
        yield from walk(n.children,p)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    # Vanilla compounds, custom ships, all LODs, translated parts and equipment references.
    models=sorted(Path('D:/games/FL_MOD/DATA/SHIPS').rglob('*.cmp'))
    fighter=next(p for p in models if p.name.lower()=='li_fighter.cmp')
    models.remove(fighter);models.insert(0,fighter)
    used=0
    for model in models:
        leaves=list(walk(read_tree(model.read_bytes())[1]))
        data={crc(p[-2]):b for p,b in leaves if p[-1].lower()=='vmeshdata'}
        refs=[(p,b) for p,b in leaves if p[-1].lower()=='vmeshref']
        for p,ref in refs:
            blob=data.get(struct.unpack_from('<I',ref,4)[0])
            if blob is None:continue # external VMesh libraries aren't stored in this CMP
            part=struct.unpack_from('<6H',ref,8)
            if not part[3]:continue
            name=(str(model.relative_to(Path('D:/games/FL_MOD/DATA/SHIPS')))+'/'+ '/'.join(p)).encode()
            records.append(struct.pack('<II6I',len(name),len(blob),*part)+name+blob)
        used+=1
    (OUT/'meshes.bin').write_bytes(struct.pack('<I',len(records))+b''.join(records))
    print(f'Prepared {len(records)} part/LOD records from {used} ship models',flush=True)
    compiler,env=compiler_env()
    cmd=[str(compiler/'cl.exe'),'/nologo','/EHsc','/O2','/std:c++17','/I',str(Path('C:/DXSDK_Jun10/Include')),
         str(ROOT/'tools/cloak/check_visual.cpp'),'/Fo'+str(OUT/'check.obj'),'/Fe'+str(OUT/'check.exe'),
         '/link','/LIBPATH:C:/DXSDK_Jun10/Lib/x86','d3d9.lib','d3dx9.lib','user32.lib']
    subprocess.run(cmd,cwd=ROOT,env=env,check=True)
    subprocess.run([str(OUT/'check.exe')],cwd=ROOT,check=True)
    from PIL import Image,ImageDraw
    frames=[]
    for i in range(48):
        frame=Image.open(OUT/f'frame_{i}.png').convert('RGB')
        draw=ImageDraw.Draw(frame);draw.rectangle((0,0,960,34),fill=(16,20,28))
        draw.text((14,10),'Cloaked Liberty fighter hull | production shader | diagnostic background',fill='white')
        frames.append(frame)
    frames[0].save(OUT/'refraction.gif',save_all=True,append_images=frames[1:],duration=125,loop=0)
    print('Saved diagnostic animation:',OUT/'refraction.gif')


if __name__=='__main__':main()
