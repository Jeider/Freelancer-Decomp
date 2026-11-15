"""Read-only PE metadata/import inspection; does not load or execute images."""
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parent

def inspect(path):
    data=path.read_bytes()
    def u16(n): return struct.unpack_from('<H',data,n)[0]
    def u32(n): return struct.unpack_from('<I',data,n)[0]
    pe=u32(0x3c)
    assert data[pe:pe+4]==b'PE\0\0'
    opt=pe+24
    assert u16(opt)==0x10b
    sections=[]
    for i in range(u16(pe+6)):
        p=opt+u16(pe+20)+40*i
        name=data[p:p+8].split(b'\0')[0].decode('ascii',errors='replace')
        size,offset=u32(p+16),u32(p+20)
        blob=data[offset:offset+size]
        counts=collections.Counter(blob)
        entropy=-sum((n/len(blob))*math.log2(n/len(blob)) for n in counts.values()) if blob else 0
        sections.append(dict(name=name,rva=u32(p+12),vsize=u32(p+8),size=size,offset=offset,flags=hex(u32(p+36)),entropy=round(entropy,3)))
    def off(rva):
        for s in sections:
            if s['rva']<=rva<s['rva']+max(s['vsize'],s['size']): return s['offset']+rva-s['rva']
        if rva<u32(opt+60): return rva
        raise ValueError(hex(rva))
    def string(n): return data[n:data.index(b'\0',n)].decode('ascii',errors='replace')
    imports={}
    import_rva=u32(opt+104)
    if import_rva:
        p=off(import_rva)
        while any(data[p:p+20]):
            thunk=u32(p) or u32(p+16)
            dll=string(off(u32(p+12)))
            names=[]
            t=off(thunk)
            while u32(t):
                v=u32(t);t+=4
                names.append('#'+str(v&0xffff) if v&0x80000000 else string(off(v)+2))
            imports[dll]=names;p+=20
    end=max(s['offset']+s['size'] for s in sections)
    strings=[m.group().decode('ascii') for m in re.finditer(rb'[\x20-\x7e]{8,}',data)]
    return dict(path=str(path),sha256=hashlib.sha256(data).hexdigest(),size=len(data),
                timestamp=u32(pe+8),entry_rva=hex(u32(opt+16)),image_base=hex(u32(opt+28)),
                dll_characteristics=hex(u16(opt+70)),certificate_size=u32(opt+96+4*8+4),
                overlay_bytes=len(data)-end,sections=sections,imports=imports,
                pdb=[s for s in strings if '.pdb' in s.lower()],
                urls=[s for s in strings if re.search(r'https?://',s)])

paths=[Path('D:/Games/FL_MOD/bin/freelancer.exe'),Path('D:/work/Freelancer-Decomp/bin/freelancer.exe')]
result=[inspect(p) for p in paths if p.exists()]
(ROOT/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for r in result:
    print(json.dumps({k:v for k,v in r.items() if k!='imports'},indent=2))
    for dll,names in r['imports'].items():
        print(dll, ', '.join(names))
