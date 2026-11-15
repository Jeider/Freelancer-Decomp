"""Read-only extraction of original BASESIDE artwork for visual reconstruction."""
import sys
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from generate_station_lods import read_tree
root=Path('D:/Games/FL_MOD/DATA/INTERFACE/BASESIDE')
out=Path('src/obj/base_icons');out.mkdir(parents=True,exist_ok=True)
def walk(nodes,path=''):
    for n in nodes:
        yield path+n.name,n
        yield from walk(n.children,path+n.name+'/')
tiles=[]
for file in sorted(root.glob('*.3db')):
    _,nodes=read_tree(file.read_bytes())
    for name,n in walk(nodes):
        if n.blob and ('texture' in name.lower() or 'material' in name.lower()):
            print(file.stem,name,len(n.blob),repr(n.blob) if len(n.blob)<90 else '')
        if n.blob and name.lower().endswith(('/mip0','/mips')):
            try:
                im=Image.open(BytesIO(n.blob)).convert('RGBA')
                im.save(out/(file.stem+'_source.png'))
                tile=Image.new('RGBA',(256,290),(12,20,32,255))
                tile.alpha_composite(im.resize((256,256)),(0,24))
                ImageDraw.Draw(tile).text((4,4),file.stem,fill='white')
                tiles.append(tile)
            except Exception as e:print(e)
sheet=Image.new('RGBA',(256*5,290*((len(tiles)+4)//5)),(12,20,32,255))
for i,tile in enumerate(tiles):sheet.paste(tile,(i%5*256,i//5*290))
sheet.convert('RGB').save(out/'originals.png')
