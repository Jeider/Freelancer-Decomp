"""Build/check/install vector-authored BASESIDE textures; preserve original meshes."""
import argparse, hashlib, importlib.util, json, struct, subprocess, sys
from datetime import datetime
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw
from check import ROOT, VC, compiler_env
sys.path.insert(0,str(ROOT/'tools'))
from generate_station_lods import read_tree, write_tree, Node
from repair_panel_normals import triangles

GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/base_icons'
PREVIEW=ROOT/'src/obj/base_icons'
NAMES=('cityscape','equipment_dealer','commod_trader','bar','deck','ship_dealer','planetscape')
spec=importlib.util.spec_from_file_location('base_icon_data_folder',GAME/'Assets/Pythonlancer/tools/data_folder.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
DataFolder=module.DataFolder
def digest(data):return hashlib.sha256(data).hexdigest()
def walk(nodes,path=''):
    for n in nodes:
        yield path+n.name,n
        yield from walk(n.children,path+n.name+'/')
def relative(name):return f'INTERFACE/BASESIDE/{name}.3db'
def tga(pixels,size):
    # Bottom-left origin (8 alpha bits), as expected by DecodeTgaTexture.
    rows=[pixels[y*size*4:(y+1)*size*4] for y in range(size)]
    return struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,size,size,32,8)+b''.join(reversed(rows))
def build():
    PREVIEW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/DNOMINMAX',
        f'/I{ROOT/"src/freelancer/Client"}',str(ROOT/'tools/cursors/base_export.cpp'),'/Febase_export.exe'],
        cwd=PREVIEW,env=compiler_env(),check=True)
    subprocess.run([str(PREVIEW/'base_export.exe'),str(PREVIEW)],check=True)
    stage=DataFolder(root=OUT/'stage');originals=DataFolder(root=OUT/'originals')
    sheet=Image.new('RGBA',(7*256,600),(12,20,32,255));draw=ImageDraw.Draw(sheet)
    manifest={}
    for index,name in enumerate(NAMES):
        rel=relative(name);live=DataFolder(root=GAME).data_path(rel).read_bytes()
        original_path=originals.data_path(rel)
        if not original_path.exists():originals.sync_data_file(rel,live)
        source=original_path.read_bytes();header,tree=read_tree(source)
        before={p:n.blob for p,n in walk(tree) if n.blob is not None}
        textures=[n for p,n in walk(tree) if '/Texture library/' in p and n.blob is None and any(c.name=='MIP0' for c in n.children)]
        assert len(textures)==1,(name,'single texture expected')
        texture=textures[0];old=Image.open(BytesIO(next(c.blob for c in texture.children if c.name=='MIP0'))).convert('RGBA')
        texture.children=[n for n in texture.children if not n.name.startswith('MIP')]
        for level,size in enumerate((512,256,128,64,32)):
            raw=(PREVIEW/f'{name}_{size}.bgra').read_bytes();assert len(raw)==size*size*4
            blob=tga(raw,size);decoded=Image.open(BytesIO(blob)).convert('RGBA')
            expected=Image.frombytes('RGBA',(size,size),raw,'raw','BGRA')
            assert decoded.tobytes()==expected.tobytes(), 'TGA orientation/channels changed'
            assert 0<sum(a>128 for a in expected.getchannel('A').tobytes())<size*size*.8
            texture.children.append(Node(f'MIP{level}',blob))
        packed=write_tree(header,tree);_,reloaded=read_tree(packed)
        after={p:n.blob for p,n in walk(reloaded) if n.blob is not None}
        for p,blob in before.items():
            if '/Texture library/' not in p:assert after[p]==blob,(name,p,'non-texture data changed')
        # Exact original geometry/UVs/material flags keep orientation, rotation and hit tests.
        mesh=[b for p,b in before.items() if p.endswith('/VMeshData')]
        assert mesh or any(p.endswith('/VMeshRef') for p in before),name
        for blob in mesh:triangles(blob)
        stage.sync_data_file(rel,packed)
        new=Image.frombytes('RGBA',(256,256),(PREVIEW/f'{name}_256.bgra').read_bytes(),'raw','BGRA')
        new.save(PREVIEW/f'{name}.png')
        sheet.alpha_composite(old.resize((256,256)),(index*256,25))
        sheet.alpha_composite(new,(index*256,315))
        draw.text((index*256+4,4),name+' / original',fill='white')
        draw.text((index*256+4,294),'vector geometry',fill='white')
        manifest[rel]={'before':digest(live),'after':digest(packed),'original':digest(source)}
    sheet.convert('RGB').save(PREVIEW/'comparison_v9.png')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PASS: seven models, 35 mip levels; TGA orientation/channel roundtrip; unchanged geometry, UVs and materials')
    print('Preview:',PREVIEW/'comparison_v9.png')
def install(label='BASESIDE'):
    manifest=json.loads((OUT/'manifest.json').read_text())
    tasks=subprocess.check_output(['tasklist','/FO','CSV','/NH']).decode(errors='replace').lower()
    assert 'freelancer.exe' not in tasks,f'Close Freelancer before applying {label} icons'
    game=DataFolder(root=GAME);stage=DataFolder(root=OUT/'stage')
    files={rel:stage.data_path(rel).read_bytes() for rel in manifest}
    before={rel:game.data_path(rel).read_bytes() for rel in manifest}
    for rel,info in manifest.items():
        assert digest(files[rel])==info['after'] and digest(before[rel])==info['before'],rel+' changed after staging'
    files={rel:data for rel,data in files.items() if data!=before[rel]}
    before={rel:before[rel] for rel in files}
    backup=DataFolder(root=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S'))
    for rel,data in before.items():backup.sync_data_file(rel,data)
    touched=[]
    try:
        for rel,data in files.items():
            touched.append(rel);game.sync_data_file(rel,data)
            assert digest(game.data_path(rel).read_bytes())==manifest[rel]['after']
    except Exception:
        for rel in touched:game.sync_data_file(rel,before[rel])
        raise
    print(f'Installed {len(files)} changed {label} files. Verified backup:',backup.get_root())
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    install() if args.apply else build()









