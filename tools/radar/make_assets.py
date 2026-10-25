"""Standalone native radar assets; preserve Beta icon and current HUD background texture."""
import copy
import json
import math
from pathlib import Path
import struct as S
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generate_station_lods import Node, child, crc, read_tree, write_tree
from make_targeting_icons import branch, generate, mesh_library, digest

repo=Path(__file__).resolve().parents[2]
game=Path('D:/games/FL_MOD/DATA/INTERFACE')
out=repo/'src/obj/radar_features/assets'
out.mkdir(parents=True,exist_ok=True)
reports=[]
data,_,report=generate(Path('D:/games/Freelancer Beta/data/Interface/HUD/HUD_radar.3db'),{},'HUD_radar')
(out/'HUD_radar.3db').write_bytes(data)
reports.append(report)

# The map buttons have a separate background part. Extract only their icon quads.
shared=mesh_library(read_tree((game/'interface.generic.vms').read_bytes())[1][0])
for name in ('zoomin','zoomout'):
    header,roots=read_tree((game/f'NeuroNet/NavMap/NewNavMap/nav_{name}.cmp').read_bytes())
    root=roots[0]
    part=next(n for n in root.children if n.name.lower().startswith('nav_'+name) and
              'back' not in n.name.lower() and n.name.endswith('.3db'))
    root.children=[child(root,'Material library'),child(root,'Texture library')]+copy.deepcopy(part.children)
    source=out/f'extracted_{name}.3db'
    source.write_bytes(write_tree(header,roots))
    data,_,report=generate(source,shared,'HUD_radar_'+name)
    (out/f'HUD_radar_{name}.3db').write_bytes(data)
    reports.append(report)

# A unit disk in XY, scaled by the HUD to its viewport ellipse. Original HUD
# background texture is retained at half the previous opacity.
header,roots=read_tree((game/'HUD/hud_target2.cmp').read_bytes())
root=roots[0]
material=copy.deepcopy(next(n for n in child(root,'Material library').children if n.name.startswith('HUD_NN_tray')))
texture=copy.deepcopy(child(child(root,'Texture library'),'backgroundpattern.tga'))
material.name='HUD_radar_background'
texture.name='radar_backgroundpattern.tga'
child(material,'Dt_name').blob=texture.name.encode()+b'\0'
child(material,'Oc').blob=S.pack('<f',.25)
mesh='hud_radar_background.lod0.vms'
points=[(0.,0.,0.,.5,.5)]
for i in range(96):
    angle=i*2*math.pi/96
    x,y=math.cos(angle),math.sin(angle)
    points.append((x,y,0.,(x+1)*.5,(1-y)*.5))
indices=[]
for i in range(96):
    a,b=i+1,(i+1)%96+1
    indices.extend((0,a,b,0,b,a))
blob=S.pack('<II4H',1,4,1,len(indices),0x102,len(points))
blob+=S.pack('<I4H',crc(material.name),0,len(points)-1,len(indices),0)
blob+=S.pack(f'<{len(indices)}H',*indices)
blob+=b''.join(S.pack('<5f',*p) for p in points)
# VMeshRef bounds: max/min X,Y,Z, centre XYZ, sphere radius.
ref=S.pack('<II6H10f',60,crc(mesh),0,len(points),0,len(indices),0,1,1,-1,1,-1,0,0,0,0,0,1)
root.children=[branch('VMeshLibrary',[branch(mesh,[Node('VMeshData',blob)])]),
               branch('VMeshPart',[Node('VMeshRef',ref)]),
               branch('Material library',[Node('Material count',S.pack('<I',1)),material]),
               branch('Texture library',[texture])]
data=write_tree(header,roots)
(out/'HUD_radar_background.3db').write_bytes(data)
assert child(child(read_tree(data)[1][0],'Texture library'),texture.name).children[0].blob==texture.children[0].blob
reports.append(dict(file='HUD_radar_background.3db',vertices=len(points),triangles=len(indices)//3,
                    texture_sha256=digest(texture.children[0].blob),sha256=digest(data)))
(out/'report.json').write_text(json.dumps(reports,indent=2))
print('Validated Beta toggle, two background-free map icons, and textured native HUD disk:',out)
