"""Bounded, read-only inspection of the courier attachment crash minidump."""
import argparse
import bisect
import json
import mmap
from pathlib import Path
import struct

class Dump:
    def __init__(self,path):
        self.file=Path(path).open('rb');self.raw=mmap.mmap(self.file.fileno(),0,access=mmap.ACCESS_READ)
        assert self.raw[:4]==b'MDMP'
        count,directory=struct.unpack_from('<II',self.raw,8)
        self.streams={}
        for i in range(count):
            kind,size,rva=struct.unpack_from('<III',self.raw,directory+i*12);self.streams[kind]=(size,rva)
        self.ranges=[]
        if 9 in self.streams:
            _,rva=self.streams[9];n,offset=struct.unpack_from('<QQ',self.raw,rva)
            for i in range(n):
                address,size=struct.unpack_from('<QQ',self.raw,rva+16+i*16)
                self.ranges.append((address,address+size,offset));offset+=size
        else:
            _,rva=self.streams[5];n=struct.unpack_from('<I',self.raw,rva)[0]
            for i in range(n):
                address,size,offset=struct.unpack_from('<QII',self.raw,rva+4+i*16)
                self.ranges.append((address,address+size,offset))
        self.ranges.sort();self.starts=[r[0] for r in self.ranges]
    def read(self,address,size):
        i=bisect.bisect_right(self.starts,address)-1
        if i<0:raise ValueError(hex(address))
        start,end,offset=self.ranges[i]
        if not start<=address<=address+size<=end:raise ValueError(hex(address))
        return self.raw[offset+address-start:offset+address-start+size]
    def u32(self,address):return struct.unpack('<I',self.read(address,4))[0]
    def string(self,address):
        if not address:return ''
        out=bytearray()
        for i in range(512):
            b=self.read(address+i,1)
            if b==b'\0':break
            out+=b
        return out.decode('utf-8',errors='replace')
    def context(self):
        _,rva=self.streams[6];size,context=struct.unpack_from('<II',self.raw,rva+160)
        return {n:struct.unpack_from('<I',self.raw,context+offset)[0] for n,offset in
                [('edi',156),('esi',160),('ebx',164),('edx',168),('ecx',172),('eax',176),('ebp',180),('eip',184),('esp',196)]}
    def instance(self,p):
        return {'address':hex(p),'parent':hex(self.u32(p+16)),'first_child':hex(self.u32(p+28)),
                'child_count':self.u32(p+36),'user_data':hex(self.u32(p+40))}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('dump');args=parser.parse_args()
    d=Dump(args.dump);ctx=d.context();equip=ctx['esi'];owner=d.u32(equip+4);arch=d.u32(equip+12);shiparch=d.u32(owner+0x88)
    result={'registers':{k:hex(v) for k,v in ctx.items()},'equipment':hex(equip),'owner':hex(owner),
            'equipment_model':d.string(d.u32(arch+12)),'hardpoint':d.string(d.u32(equip+32)),
            'ship_model':d.string(d.u32(shiparch+12)),'ship_position':struct.unpack('<3f',d.read(owner+0x2c,12)),
            'physics_system':d.u32(owner+0x50),'root':d.instance(d.u32(owner+4)),
            'connector':d.instance(d.u32(equip+36))}
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
