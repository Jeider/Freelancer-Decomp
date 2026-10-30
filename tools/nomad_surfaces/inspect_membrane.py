"""Read-only inventory of Nomad energy material and texture references."""
from pathlib import Path
import sys
import json
import io
import struct
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_station_lods as utf

def walk(nodes, prefix=''):
    for n in nodes:
        path = prefix+'/'+n.name
        yield path, n
        yield from walk(n.children, path)

for name in ('beta_nomad_lair.mat', 'beta_nomad.mat', 'nomad_lair.mat', 'nomad.mat'):
    _, roots = utf.read_tree((Path('D:/games/FL_MOD/DATA/SOLAR')/name).read_bytes())
    print('\nLIBRARY', name)
    for path, n in walk(roots):
        if n.children and ('material library/' in path.lower()):
            leaves = {c.name: c.blob.rstrip(b'\0').decode('ascii', errors='replace') for c in n.children if c.blob and c.name in ('Type','Dt_name','Et_name','Bt_name','Ot_name')}
            if leaves: print(n.name, json.dumps(leaves))
            if any(k in n.name.lower() for k in ('mbrn','mem_','energy')):
                print('PROPERTIES',[(c.name, c.blob.hex() if len(c.blob)<24 else str(len(c.blob)), struct.unpack('<'+'f'*(len(c.blob)//4),c.blob) if len(c.blob) in (4,12) else '') for c in n.children if c.blob])
        if n.children and 'texture library/' in path.lower() and any(k in n.name.lower() for k in ('membrane','energy','lair_op')):
            out=Path(__file__).resolve().parents[2]/'src/obj/nomad_membrane'/name
            out.mkdir(parents=True,exist_ok=True)
            for leaf in n.children:
                if leaf.name in ('MIPS','MIP0'):
                    im=Image.open(io.BytesIO(leaf.blob)).convert('RGBA')
                    im.save(out/(n.name+'.png'))
                    (out/(n.name+'.dds')).write_bytes(leaf.blob)
                    print('TEXTURE',n.name,im.size,'alpha',im.getchannel('A').getextrema())
