"""Add two attribute-aware LODs to a rigid XYZ/N/UV Freelancer UTF model.

Original Level0, hardpoints, bounds and unrelated leaves stay byte-identical.
Run with an x64 Python after building tools/lod_simplify.cpp and meshoptimizer.
The output is separate; this tool never installs or overwrites the source.
"""
import argparse
import collections
import ctypes as C
import hashlib
import json
import math
import re
import struct as S
from pathlib import Path
from lod_uv_guard import UvGuard
from repair_panel_normals import leaves, triangles, face_normal


class Node:
    def __init__(self,name,blob=None,raw=None):
        self.name,self.blob,self.children=name,blob,[]
        self.raw=bytearray(raw or bytes(44))


def read_tree(data):
    header=list(S.unpack_from('<14I',data))
    tree,strings,payload=header[2],header[6],header[9]
    def walk(offset):
        result=[]
        while True:
            raw=data[tree+offset:tree+offset+44]
            sibling,name,flags=S.unpack_from('<3I',raw)
            a=strings+name
            n=Node(data[a:data.index(0,a)].decode('ascii'),raw=raw)
            child=S.unpack_from('<I',raw,16)[0]
            if flags&16:
                n.children=walk(child) if child else []
            else:
                size=S.unpack_from('<I',raw,28)[0]
                n.blob=data[payload+child:payload+child+size]
            result.append(n)
            if not sibling:break
            offset=sibling
        return result
    return header,walk(0)


def write_tree(header,roots):
    nodes=[]
    def collect(siblings):
        for n in siblings:
            nodes.append(n);collect(n.children)
    collect(roots)
    ids={id(n):i*44 for i,n in enumerate(nodes)}
    strings=bytearray();names={};payload=bytearray();records={}
    def emit(siblings):
        for i,n in enumerate(siblings):
            if n.name not in names:
                names[n.name]=len(strings);strings.extend(n.name.encode('ascii')+b'\0')
            raw=bytearray(n.raw)
            S.pack_into('<3I',raw,0,ids[id(siblings[i+1])] if i+1<len(siblings) else 0,
                        names[n.name],16 if n.blob is None else 128)
            if n.blob is None:
                S.pack_into('<I',raw,16,ids[id(n.children[0])] if n.children else 0)
            else:
                payload.extend(b'\0'*((-len(payload))%4))
                S.pack_into('<4I',raw,16,len(payload),len(n.blob),len(n.blob),len(n.blob))
                payload.extend(n.blob)
            records[id(n)]=raw
            emit(n.children)
    emit(roots)
    used=len(strings);strings.extend(b'\0'*((-used)%4))
    h=header[:];h[2]=56;h[3]=44*len(nodes);h[6]=56+h[3]
    h[7]=len(strings);h[8]=used;h[9]=h[6]+len(strings)
    return S.pack('<14I',*h)+b''.join(records[id(n)] for n in nodes)+strings+payload


def child(n,name):
    return next(c for c in n.children if c.name.lower()==name.lower())


def crc(name):
    # The port's exporter-compatible DACOM table differs from IEEE CRC32.
    source=Path('src/dacom/dacom.cpp').read_text()
    block=source.split('G_Crc32Table[256] = {',1)[1].split('};',1)[0]
    table=[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)u',block)]
    assert len(table)==256
    value=0xffffffff
    for b in name.lower().encode('ascii'):value=table[(value&255)^b]^(value>>8)
    return value^0xffffffff


def simplify(blob,dll,ratio,error,protect_flat_caps=True,retain_missing_materials=False,preserve_materials=()):
    header,descriptors,groups=triangles(blob)
    uv_guard=UvGuard(descriptors,groups)
    materials=collections.OrderedDict()
    # Same material groups can share one draw in a coarse, opaque rigid LOD.
    for (material,_,unused),corners in zip(descriptors,groups):
        materials.setdefault(material,[]).extend(corners)
    def position(v):return tuple(round(x,4) for x in S.unpack_from('<3f',v))
    entries=list(dict.fromkeys((m,v) for m,cs in materials.items() for v in cs))
    remap={v:i for i,v in enumerate(entries)}
    indices=[remap[(m,v)] for m,cs in materials.items() for v in cs]
    tags={m:i for i,m in enumerate(materials)}
    vin=(C.c_float*(9*len(entries))).from_buffer_copy(b''.join(v+S.pack('<f',tags[m]) for m,v in entries))
    idx=(C.c_uint*len(indices))(*indices);out=(C.c_uint*len(indices))()
    # Keep thin structural bars intact; their cross-section otherwise disappears
    # before the rest of this large model reaches its geometry error limit.
    protected=set()
    for m,cs in materials.items():
        if m in preserve_materials:
            protected.update(position(v) for v in cs)
    for m,cs in materials.items():
        adjacency=collections.defaultdict(set)
        for i in range(0,len(cs),3):
            ps=[position(v) for v in cs[i:i+3]]
            for a in ps:adjacency[a].update(ps)
        seen=set()
        for start in adjacency:
            if start in seen:continue
            stack=[start];component=set()
            while stack:
                q=stack.pop()
                if q in seen:continue
                seen.add(q);component.add(q);stack.extend(adjacency[q]-seen)
            faces=sum(position(cs[i]) in component for i in range(0,len(cs),3))
            extent=sorted(max(p[k] for p in component)-min(p[k] for p in component) for k in range(3))
            thin=(8<=faces<=32 and extent[2]>10*max(extent[0],1.e-4))
            if not protect_flat_caps:
                thin=(faces>=8 and extent[0]>1.e-3 and
                      (extent[2]>4*max(extent[1],1.e-4) or thin))
            if thin:
                protected.update(component)
    locks=(C.c_ubyte*len(entries))(*(1 if position(v) in protected else 0 for m,v in entries))
    metric=C.c_float()
    count=dll.simplify_lod(out,idx,len(indices),vin,len(entries),locks,
                          max(3,int(len(indices)*ratio)//3*3),error,C.byref(metric))
    assert count and count%3==0
    result=collections.OrderedDict((m,[]) for m in materials)
    for i in range(0,count,3):
        face=[entries[out[i+k]] for k in range(3)]
        assert len(set(m for m,v in face))==1, 'A material seam was crossed'
        assert face_normal([v for m,v in face]) is not None
        result[face[0][0]].extend(v for m,v in face)
    if retain_missing_materials:
        # Small caps/decals can be an entire material island. Retain their
        # original triangles if the simplifier would eliminate the island.
        for m,cs in result.items():
            if not cs:result[m]=materials[m]
    for m in preserve_materials:
        # Preserve authored triangle order on alpha-tested/blended islands.
        # The caller must ensure each protected material occurs in one group.
        if m in materials:result[m]=materials[m]
    uv_rejected={}
    for m,cs in result.items():
        issues=uv_guard.issues(m,cs)
        if issues:
            uv_rejected[m]=dict(issues)
            # Keep the authored topology for this material instead of shipping
            # a smaller mesh with shifted/stretched atlas coordinates.
            result[m]=materials[m]
    assert all(result.values()), 'A complete material component disappeared'
    out_groups=list(result.items())
    stats=[dict(material=hex(m),triangles_before=len(materials[m])//3,
                triangles_after=len(cs)//3,error=float(metric.value),uv_rejected=uv_rejected.get(m,{})) for m,cs in out_groups]
    vertex_data=bytearray();index_data=bytearray();group_data=bytearray();offset=0
    for material,corners in out_groups:
        # Exact attribute welding only: retain UV seams and hard normals.
        unique=list(dict.fromkeys(corners));mapping={v:i for i,v in enumerate(unique)}
        group_data.extend(S.pack('<I4H',material,offset,offset+len(unique)-1,len(corners),204))
        index_data.extend(S.pack('<'+'H'*len(corners),*(mapping[v] for v in corners)))
        vertex_data.extend(b''.join(unique));offset+=len(unique)
    count=len(index_data)//2
    assert offset<65536 and count<65536
    result=S.pack('<II4H',1,4,len(out_groups),count,0x112,offset)+group_data+index_data+vertex_data
    triangles(result)  # Validate all indices/ranges and group counts.
    return bytes(result),stats


def generate(source,destination,dll_path):
    assert source.resolve()!=destination.resolve()
    data=source.read_bytes();header,roots=read_tree(data);root=roots[0]
    library=child(root,'VMeshLibrary');multilevel=child(root,'MultiLevel')
    original_ref=child(child(child(multilevel,'Level0'),'VMeshPart'),'VMeshRef').blob
    key=S.unpack_from('<I',original_ref,4)[0]
    main=next(n for n in library.children if crc(n.name)==key)
    original=child(main,'VMeshData').blob
    h=triangles(original)[0]
    assert S.unpack_from('<6H',original_ref,8)==(0,h[-1],0,h[3],0,h[2]), 'Partial mesh reference unsupported'
    dll=C.CDLL(str(dll_path.resolve()))
    dll.simplify_lod.argtypes=[C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.c_size_t,
        C.POINTER(C.c_float),C.c_size_t,C.POINTER(C.c_ubyte),C.c_size_t,C.c_float,C.POINTER(C.c_float)]
    dll.simplify_lod.restype=C.c_size_t
    report={'source_sha256':hashlib.sha256(data).hexdigest(),'levels':[]}
    # Keep the old invisible far level at its original 8 km switch distance.
    # Extra visible geometry beyond that would counter the optimisation goal.
    hidden=child(multilevel,'Level1')
    hidden_ref=child(child(hidden,'VMeshPart'),'VMeshRef').blob
    hidden.name='Level3'
    multilevel.children=[n for n in multilevel.children if n.name.lower() not in ('level1','level2')]
    for level,ratio,error in ((1,.55,.008),(2,.35,.012)):
        blob,stats=simplify(original,dll,ratio,error)
        name=f'space_trade_station_part_auto.lod{level}-112.vms'
        mesh=Node(name);mesh.children=[Node('VMeshData',blob)];library.children.append(mesh)
        h,_,_=triangles(blob)
        ref=bytearray(original_ref)
        S.pack_into('<I6H',ref,4,crc(name),0,h[-1],0,h[3],0,h[2])
        part=Node('VMeshPart');part.children=[Node('VMeshRef',bytes(ref))]
        lod=Node(f'Level{level}');lod.children=[part];multilevel.children.append(lod)
        report['levels'].append(dict(level=level,vertices=h[-1],triangles=h[3]//3,
                                     groups=h[2],requested_ratio=ratio,metric_limit=error,materials=stats))
    child(multilevel,'Switch2').blob=S.pack('<5f',0,1800,4500,8000,27000)
    output=write_tree(header,roots)
    before={p:b for p,_,b in leaves(data)[1]};after={p:b for p,_,b in leaves(output)[1]}
    for path,b in before.items():
        if '/multilevel/level1/' in path.lower() or path.lower().endswith('/switch2'):continue
        assert after[path]==b,path
    assert child(child(child(multilevel,'Level3'),'VMeshPart'),'VMeshRef').blob==hidden_ref
    assert crc(main.name)==key
    report['original']=dict(vertices=triangles(original)[0][-1],triangles=triangles(original)[0][3]//3,
                            groups=triangles(original)[0][2])
    report['switch_distances']=[0,1800,4500,8000,27000]
    report['output_sha256']=hashlib.sha256(output).hexdigest()
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(output)
    destination.with_suffix('.report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='levels'},indent=2))
    for level in report['levels']:print({k:v for k,v in level.items() if k!='materials'})


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path);ap.add_argument('destination',type=Path)
    ap.add_argument('--dll',type=Path,default=Path('bin/lod_meshopt.dll'))
    args=ap.parse_args();generate(args.source,args.destination,args.dll)
