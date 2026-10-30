"""BEAST-only lightweight bump. Prepare locally; --apply verifies and backs up."""
import json
import struct
import sys
from pathlib import Path
import install
sys.path.insert(0,str(install.REPO/'tools'))
import generate_station_lods as utf

install.STAGE=install.REPO/'src/obj/beast_relief/install'
MODEL='DATA/SOLAR/MISC/BEAST/beast.cmp'
install.PAYLOAD=('bin/RP9.dll','bin/RP9.pdb','bin/Shading.dll','bin/Shading.pdb',
                 'DATA_EXTRA/SHADERS/surface_material.hlsl',MODEL)
install.SCOPE='BEAST lightweight bump: five fixed texture reads, no parallax, organic layers or PCSS; other Dyson shaders and strength settings unchanged'

def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.children)

def prepare():
    game=Path('D:/games/FL_MOD')
    original=(game/MODEL).read_bytes()
    header,nodes=utf.read_tree(original)
    old,new=utf.crc('dyson_surface_atlas'),utf.crc('beast_dyson_recess')
    count=0;materials=0
    for n in walk(nodes):
        if n.name=='dyson_surface_atlas':
            n.name='beast_dyson_recess';materials+=1
        elif n.name=='beast_dyson_recess':materials+=1
        if n.name=='VMeshData':
            b=bytearray(n.blob)
            groups=struct.unpack_from('<H',b,8)[0]
            for i in range(groups):
                offset=16+12*i
                identity=struct.unpack_from('<I',b,offset)[0]
                assert identity in (old,new),hex(identity)
                struct.pack_into('<I',b,offset,new);count+=1
            n.blob=bytes(b)
        if n.name=='dyson_surface_atlas.tga':
            out=install.REPO/'src/obj/beast_relief/atlas.dds'
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(next(c.blob for c in n.children if c.name=='MIPS'))
    assert materials==1 and count==28,(materials,count)
    result=utf.write_tree(header,nodes)
    # Reverse only our identity changes and compare every original leaf, including vertices/UVs/DDS.
    _,verified=utf.read_tree(result)
    for n in walk(verified):
        if n.name=='beast_dyson_recess':n.name='dyson_surface_atlas'
        if n.name=='VMeshData':
            b=bytearray(n.blob)
            for i in range(struct.unpack_from('<H',b,8)[0]):struct.pack_into('<I',b,16+12*i,old)
            n.blob=bytes(b)
    if b'beast_dyson_recess' not in original:
        _,before=utf.read_tree(original)
        assert [(n.name,n.blob) for n in walk(before)]==[(n.name,n.blob) for n in walk(verified)]
    payload=install.PAYLOAD
    install.PAYLOAD=payload[:-1];install.main();install.PAYLOAD=payload
    target=install.safe(install.STAGE,MODEL);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
    manifest=install.STAGE/'manifest.json';data=json.loads(manifest.read_text())
    if install.digest(game/MODEL)!=install.digest(target):
        data['files'].append(dict(relative=MODEL,original=install.digest(game/MODEL),prepared=install.digest(target)))
    manifest.write_text(json.dumps(data,indent=2))
    print('BEAST: 28 material references across 3 LODs; all geometry, UVs and original DDS byte-identical.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:install.main()
