"""Read-only validation of the exact Beta code/vtables used by this patch."""
import argparse, hashlib, pathlib, struct

class PE:
    def __init__(self, path):
        self.data=path.read_bytes()
        pe=struct.unpack_from('<I',self.data,0x3c)[0]
        assert self.data[pe:pe+4]==b'PE\0\0'
        assert struct.unpack_from('<H',self.data,pe+4)[0]==0x14c
        self.base=struct.unpack_from('<I',self.data,pe+24+28)[0]
        count=struct.unpack_from('<H',self.data,pe+6)[0]
        sh=pe+24+struct.unpack_from('<H',self.data,pe+20)[0]
        self.sections=[struct.unpack_from('<8sIIII',self.data,sh+i*40) for i in range(count)]
    def read(self, rva, size):
        for _,vs,va,rs,raw in self.sections:
            if va<=rva and rva+size<=va+rs:
                return self.data[raw+rva-va:raw+rva-va+size]
        raise AssertionError(f'Unmapped RVA {rva:x}')
    def u32(self, rva): return struct.unpack('<I',self.read(rva,4))[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('--beta-root',type=pathlib.Path,required=True);p.add_argument('--payload',type=pathlib.Path,required=True);a=p.parse_args()
    ex=PE(a.beta_root/'exe/FreeLancer.exe');co=PE(a.beta_root/'exe/Common.dll')
    assert hashlib.sha256(ex.data).hexdigest()=='ce31304cf0e3353e72926281b612697a1815cc94042dfc80be6c252c9fb5c920'
    assert hashlib.sha256(co.data).hexdigest()=='7d358c16d2285d9e0d1ef0248a7acb8f26f6828c4a9f300320a11da77aff1d0c'
    assert ex.read(0xbd7f0,6)==bytes.fromhex('81 ec c0 00 00 00')
    assert ex.read(0xbd04f,5)==bytes.fromhex('83 f8 12 75 08')
    assert ex.read(0xbcfbc,2)==bytes.fromhex('75 50')
    for cell,fn in [(0x143064,0x6a240),(0x1430dc,0x6a240),(0x143058,0x6a7b0),(0x14305c,0x6ab30),(0x143068,0x6a2b0),(0x1430d4,0x6af20),(0x1430e0,0x6afa0)]:
        assert co.u32(cell)==co.base+fn,(hex(cell),hex(fn))
    assert co.read(0x6a240,8)==bytes.fromhex('b8 02 00 00 00 c2 04 00')
    for id in (5,18):
        idx=ex.read(0xbdd58+id+1,1)[0]
        assert ex.u32(0xbdd30+idx*4)==ex.base+0xbdccf
    assert co.read(0x7ea40,9)==bytes.fromhex('8b c1 33 c9 c7 40 04 0a 00')
    assert co.read(0x7eaa0,9)==bytes.fromhex('8b c1 33 c9 c7 40 04 0b 00')
    assert ex.read(0xbdccf,6)==bytes.fromhex('8b ce ff d5 8b f0')
    assert ex.read(0xbdd1d,6)==bytes.fromhex('ff 92 fc 00 00 00')
    for name in ('beta_evade_patch.dll','beta_evade_launcher.exe'):
        PE(a.payload/name)
    print('PASS: exact Beta hashes, x86 payload, detour and HUD instructions, seven vtable slots, both default dispatch cases, directive types and native SetManeuver tail.')

if __name__=='__main__': main()
