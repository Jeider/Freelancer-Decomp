"""Prepare the platform-only TLR model and articulated SUR; all DATA via DataFolder."""
from pathlib import Path
import ctypes as C
import hashlib
import importlib.util
import json
import struct as S
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
OUT = ROOT/'out/tradelane_physical'
sys.path.insert(0, str(ROOT/'tools'))
import generate_station_lods as utf
from generate_industrial_lods import geometry
from repair_panel_normals import triangles
sys.path.insert(0, str(ROOT/'tools/train_sur'))
import build as sur
from docking_surface import parts as read_sur
spec = importlib.util.spec_from_file_location('tlr_data_folder', GAME/'Assets/Pythonlancer/tools/data_folder.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
DataFolder = module.DataFolder
MODEL = 'SOLAR/DOCKABLE/tlr_legal_lod5.cmp'


def digest(data): return hashlib.sha256(data).hexdigest()


def pack(groups, descriptors):
    vertices, indices, records = [], [], []
    for corners, desc in zip(groups, descriptors):
        if not corners: continue
        unique = list(dict.fromkeys(corners)); lookup = {v:i for i,v in enumerate(unique)}
        records.append(S.pack('<I4H',desc[0],len(vertices),len(vertices)+len(unique)-1,len(corners),desc[2]))
        vertices.extend(unique); indices.extend(lookup[v] for v in corners)
    assert len(vertices)<65536 and len(indices)<65536
    return S.pack('<II4H',1,4,len(records),len(indices),0x112,len(vertices))+b''.join(records)+S.pack('<%dH'%len(indices),*indices)+b''.join(vertices)


def xyz(groups):
    return np.array([S.unpack_from('<3f',v) for g in groups for v in g]).reshape(-1,3,3)


def components(tris):
    parents=list(range(len(tris))); seen={}
    def find(i):
        while parents[i]!=i: parents[i]=parents[parents[i]];i=parents[i]
        return i
    for i,t in enumerate(tris):
        for v in t:
            j=seen.setdefault(tuple(v.round(3)),i); parents[find(i)]=find(j)
    groups={}
    for i,t in enumerate(tris): groups.setdefault(find(i),[]).append(t)
    return [np.array(v) for v in groups.values()]


def encode_parts(hulls_by_name):
    result=bytearray(b'vers'+S.pack('<f',2))
    for name,hulls in hulls_by_name.items():
        surface,lo,hi=sur.encode_surface(hulls)
        # !fxd creates an individual physics body for each animated CMP child.
        result+=S.pack('<II',utf.crc(name),3)+b'!fxd'
        result+=b'exts'+S.pack('<6f',*lo,*hi)+b'surf'+S.pack('<I',len(surface))+surface
    return bytes(result)


def leaves(nodes, prefix=''):
    for n in nodes:
        path=prefix+'/'+n.name
        if n.blob is not None: yield path,n.blob
        yield from leaves(n.children,path)


def build():
    live=DataFolder(root=GAME); original=DataFolder(root=OUT/'originals'); stage=DataFolder(root=OUT/'stage')
    relative=[MODEL,MODEL.replace('.cmp','.sur'),'SOLAR/DOCKABLE/tlr_root.sur','SOLAR/solararch.ini']
    for rel in relative:
        if not original.data_path(rel).exists(): original.sync_data_file(rel,live.data_path(rel).read_bytes())
    source=original.data_path(MODEL).read_bytes(); header,roots=utf.read_tree(source); root=roots[0]
    lib=utf.child(root,'VMeshLibrary'); platform=utf.child(lib,'new_tlr_platform.lod0-112.vms')
    oldblob=geometry(utf.child(platform,'VMeshData').blob); h,ds,gs=triangles(oldblob)
    assert h[2]==7 and [len(g)//3 for g in gs]==[896,1440,544,388,64,8,104], 'Review changed source geometry'
    # Groups 0/1 are the stationary perimeter frames; groups 2..6 are the
    # modified weapons platform. Keep original vertices, normals, UVs/materials.
    clean=pack(gs[2:],ds[2:]); base=xyz(gs[2:]); assert np.max(np.abs(base[:,:,:2]))<106
    utf.child(platform,'VMeshData').blob=clean
    # Keep the two central components of the authored coarse mesh. The other
    # 28 components are perimeter segments, including pieces near the centre.
    coarse=geometry(utf.child(utf.child(lib,'tlr_legal_lod_alt_roott.lod0-112.vms'),'VMeshData').blob)
    _,cd,cg=triangles(coarse)
    keep=[p for p in components(xyz(cg)) if np.max(np.abs(p[:,:,0]))<60 and np.max(np.abs(p[:,:,1]))<85]
    assert len(keep)==2 and sum(len(p) for p in keep)==132
    positions={tuple(v.round(3)) for p in keep for v in p.reshape(-1,3)}
    coarse_groups=[]
    for group in cg:
        selected=[]
        for i in range(0,len(group),3):
            if all(tuple(np.array(S.unpack_from('<3f',v)).round(3)) in positions for v in group[i:i+3]):selected.extend(group[i:i+3])
        coarse_groups.append(selected)
    clean_coarse=pack(coarse_groups,cd)
    part=utf.child(root,'platform_lod1.3db'); ml=utf.child(part,'MultiLevel')
    levels=[]
    for level,ratio in enumerate((1,.45,.22)):
        blob=clean if level==0 else clean_coarse
        name=platform.name if level==0 else f'tlr_platform_clean.lod{level}-112.vms'
        if level: node=utf.Node(name);node.children=[utf.Node('VMeshData',blob)];lib.children.append(node)
        hh,dd,gg=triangles(blob); pts=xyz(gg).reshape(-1,3); lo=pts.min(0);hi=pts.max(0);center=(lo+hi)/2
        ref=utf.child(utf.child(utf.child(ml,f'Level{level}'),'VMeshPart'),'VMeshRef')
        b=bytearray(ref.blob);S.pack_into('<I6H',b,4,utf.crc(name),0,hh[-1],0,hh[3],0,hh[2])
        S.pack_into('<10f',b,20,hi[0],lo[0],hi[1],lo[1],hi[2],lo[2],*center,float(np.max(np.linalg.norm(pts-center,axis=1))))
        ref.blob=bytes(b);levels.append(hh[3]//3)
    # The target wireframe also must not retain the removed perimeter frames.
    wire=utf.child(part,'VMeshWire'); vwire=utf.child(wire,'VWireData')
    from wireframe import feature_wire
    vwire.blob=feature_wire(clean,utf.crc(platform.name))
    ring_blob=geometry(utf.child(utf.child(lib,'new_tlr_ring.lod0-112.vms'),'VMeshData').blob)
    ring=xyz(triangles(ring_blob)[2]); pieces=components(ring);assert len(pieces)==4
    body=sur.Part('Root',base,{})
    own={'Root':sur.hulls_for(body,35)}
    for name in ('tlr1_lod1','tlr2_lod1'):
        own[name]=[h for piece in pieces for h in sur.hulls_for(sur.Part(name,piece,{}),25)]
    packed=utf.write_tree(header,roots)
    before=dict(leaves(utf.read_tree(source)[1]));after=dict(leaves(utf.read_tree(packed)[1]))
    for p,b in before.items():
        if any(x in p for x in ('/Animation/','/Cmpnd/','/Hardpoints/','/tlr1_lod1.3db/','/tlr2_lod1.3db/')):assert after[p]==b,p
    stage.sync_data_file(MODEL,packed)
    surf=encode_parts(own);stage.sync_data_file(MODEL.replace('.cmp','.sur'),surf)
    # The current dummy parent remains attached: replace its old large collider
    # by the same retained platform, with the 3DB root id 0.
    parent=bytearray(encode_parts({'Root':own['Root']}));S.pack_into('<I',parent,8,0)
    stage.sync_data_file('SOLAR/DOCKABLE/tlr_root.sur',parent)
    import re
    text=live.data_path('SOLAR/solararch.ini').read_bytes().decode('cp1251')
    def edit(m):
        b=m[0]
        if not re.search(r'(?mi)^nickname\s*=\s*Trade_Lane_Ring\s*$',b):return b
        if 'physical_ring_anim' in b:return b
        return re.sub(r'(?mi)^(right_ring_anim[^\r\n]*)(\r?\n)',r'\1\2physical_ring_anim = true\2',b)
    modified=re.sub(r'(?ms)^\[Solar\].*?(?=^\[|\Z)',edit,text)
    assert 'physical_ring_anim = true' in modified
    stage.sync_data_file('SOLAR/solararch.ini',modified.encode('cp1251'))
    report={'source_sha256':digest(source),'platform_triangles':levels,'ring_triangles_each':len(ring),
            'hulls':{n:len(hs) for n,hs in own.items()},'files':{rel:{'before':digest(live.data_path(rel).read_bytes()),'after':digest(stage.data_path(rel).read_bytes())} for rel in relative}}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'manifest.json').write_text(json.dumps(report,indent=2))
    preview(xyz(gs),base,ring,own)
    print(json.dumps(report))


def preview(old,base,ring,own):
    im=Image.new('RGB',(1500,620),'#18212c');d=ImageDraw.Draw(im)
    for panel,title in enumerate(('BEFORE','PLATFORM + ROTORS','COLLISION HULLS (orange)')):
        d.text((panel*500+15,20),title,fill='white')
        meshes=[(old if panel==0 else base,np.zeros(3),'#9db1bc')]
        meshes += [(ring,np.array(off),'#f5cf53') for off in ((225,125,0),(-225,-125,0))]
        def screen(p):return [(panel*500+250+float(x)*.46,310-float(y)*.46) for x,y,z in p]
        for ts,off,color in meshes:
            for t in sorted(ts+off,key=lambda t:t[:,2].mean()):d.polygon(screen(t),fill=color)
        if panel==2:
            for name,offset in [('Root',(0,0,0)),('tlr1_lod1',(225,125,0)),('tlr2_lod1',(-225,-125,0))]:
                for hull in own[name]:
                    xy=hull.points[:,:2];idx=sur.ConvexHull(xy).vertices
                    poly=screen(hull.points[idx]+offset);d.line(poly+[poly[0]],fill='#ff753c',width=2)
    im.save(OUT/'comparison.png')


if __name__=='__main__':build()
