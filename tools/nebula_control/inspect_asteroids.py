"""Read bounded asteroid/render state from an existing process and its local PDB.
Never launches, suspends, injects into or writes the game process.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import struct

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pid', required=True, type=int)
parser.add_argument('--routes', action='store_true', help='Sample live RP9 route flags without pausing the game')
parser.add_argument('--output', type=Path, help='Separate read-only snapshot destination')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/graphics_settings/nebula_asteroid_mesh/fog_surface/runtime.json'
if args.output: OUT=args.output.resolve()
k = C.WinDLL('kernel32', use_last_error=True)
d = C.WinDLL('C:/Program Files (x86)/Windows Kits/10/Debuggers/x64/dbghelp.dll', use_last_error=True)
k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]; k.OpenProcess.restype = W.HANDLE
k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
k.K32EnumProcessModulesEx.argtypes = [W.HANDLE, C.POINTER(W.HMODULE), W.DWORD, C.POINTER(W.DWORD), W.DWORD]
k.K32GetModuleFileNameExW.argtypes = [W.HANDLE, W.HMODULE, W.LPWSTR, W.DWORD]
k.CloseHandle.argtypes = [W.HANDLE]
k.LocalFree.argtypes = [C.c_void_p]
class Symbol(C.Structure):
    _fields_ = [('SizeOfStruct', W.ULONG), ('TypeIndex', W.ULONG), ('Reserved', C.c_ulonglong*2),
                ('Index', W.ULONG), ('Size', W.ULONG), ('ModBase', C.c_ulonglong), ('Flags', W.ULONG),
                ('Value', C.c_ulonglong), ('Address', C.c_ulonglong), ('Register', W.ULONG),
                ('Scope', W.ULONG), ('Tag', W.ULONG), ('NameLen', W.ULONG), ('MaxNameLen', W.ULONG), ('Name', C.c_char*1)]
Callback = C.WINFUNCTYPE(W.BOOL, C.POINTER(Symbol), W.ULONG, C.c_void_p)
d.SymInitializeW.argtypes = [W.HANDLE, W.LPCWSTR, W.BOOL]
d.SymLoadModuleExW.argtypes = [W.HANDLE, W.HANDLE, W.LPCWSTR, W.LPCWSTR, C.c_ulonglong, W.DWORD, C.c_void_p, W.DWORD]
d.SymLoadModuleExW.restype = C.c_ulonglong
d.SymEnumSymbols.argtypes = [W.HANDLE, C.c_ulonglong, C.c_char_p, Callback, C.c_void_p]
d.SymGetTypeInfo.argtypes = [W.HANDLE, C.c_ulonglong, W.ULONG, C.c_int, C.c_void_p]
d.SymCleanup.argtypes = [W.HANDLE]
handle = k.OpenProcess(0x410, False, args.pid)
if not handle: raise C.WinError(C.get_last_error())
def read(address, size):
    assert address >= 0x10000 and 0 < size <= 65536
    data = C.create_string_buffer(size); received = C.c_size_t()
    if not k.ReadProcessMemory(handle, address, data, size, C.byref(received)) or received.value != size:
        raise C.WinError(C.get_last_error())
    return data.raw
def u32(address): return struct.unpack('<I', read(address, 4))[0]
def info(typ, what, cls=W.ULONG):
    out = cls()
    if not d.SymGetTypeInfo(handle, base, typ, what, C.byref(out)): return None
    return out.value
def name(typ):
    pointer = info(typ, 1, C.c_void_p)
    if not pointer: return ''
    result = C.wstring_at(pointer); k.LocalFree(pointer); return result
def children(typ):
    count = info(typ, 13) or 0
    assert count < 512
    out = (W.ULONG*(count+2))(count, 0)
    if count and not d.SymGetTypeInfo(handle, base, typ, 7, out): raise C.WinError(C.get_last_error())
    return list(out)[2:]
def fields(typ, offset=0, depth=0):
    if depth > 10: return {}
    if info(typ,0)==17: return fields(info(typ,4),offset,depth+1)
    result = {}
    for child in children(typ):
        at, ct = info(child, 10), info(child, 4)
        if at is None or ct is None: continue
        key = name(child)
        if info(child, 0) == 18: result.update(fields(ct, offset+at, depth+1))
        else: result[key] = dict(offset=offset+at, type=ct, size=info(ct, 2, C.c_ulonglong), tag=info(ct, 0))
    return result
def member(typ, address, key):
    f=fields(typ)[key]
    return f['type'], address+f['offset']
def nested(typ,address,*keys):
    for key in keys: typ,address=member(typ,address,key)
    return typ,address

def vector_size(typ,address,stride):
    vt,vp=nested(typ,address,'_Mypair','_Myval2')
    while '_Myfirst' not in fields(vt):vt,vp=member(vt,vp,'_Myval2')
    vf=fields(vt);begin=u32(vp+vf['_Myfirst']['offset']);end=u32(vp+vf['_Mylast']['offset'])
    assert 0<=end-begin<=16*1024*1024 and (end-begin)%stride==0
    return (end-begin)//stride
def far_fields(s):
    typ, address=nested(s['type'],s['address'],'_Mypair','_Myval2')
    while '_Myhead' not in fields(typ): typ,address=member(typ,address,'_Myval2')
    ht,hp=member(typ,address,'_Myhead');head=u32(hp);node_type=info(ht,4)
    nt=fields(node_type);count=u32(member(typ,address,'_Mysize')[1]);assert count<128
    pt=nt['_Myval']['type'];pair=fields(pt)
    value_type=pair['second']['type']
    if 'unique_ptr' not in name(value_type):return {'type':name(value_type)}
    results=[];pending=[u32(head+nt['_Parent']['offset'])];seen=set()
    while pending:
        node=pending.pop()
        if node==head:continue
        assert node not in seen and len(seen)<128
        seen.add(node)
        for key in ('_Left','_Right'):pending.append(u32(node+nt[key]['offset']))
        val=node+nt['_Myval']['offset']
        ptr_type,ptr_at=nested(value_type,val+pair['second']['offset'],'_Mypair','_Myval2')
        while info(ptr_type,0)!=14:ptr_type,ptr_at=member(ptr_type,ptr_at,'_Myval2')
        obj=u32(ptr_at);ot=info(ptr_type,4);of=fields(ot)
        item={'field':hex(u32(val+pair['first']['offset'])),'address':hex(obj),'type':name(ot)}
        if 'Meshes' in of:
            data=read(obj,info(ot,2,C.c_ulonglong))
            for key in ('TexCount','bBuilt','bFailed','AmbientRgb','SunColour','SunDir','Sunlit','TexTint'):
                f=of[key];raw=data[f['offset']:f['offset']+f['size']]
                item[key]=list(struct.unpack('<'+'f'*(len(raw)//4),raw)) if key not in ('TexCount','bBuilt','bFailed') else int.from_bytes(raw,'little')
            ptype,paddr=member(ot,obj,'P');pfields=fields(ptype)
            item['local']=bool(read(paddr+pfields['bNebulaLocal']['offset'],1)[0])
            mesh_array=of['Meshes'];mt=info(mesh_array['type'],4);ms=info(mt,2,C.c_ulonglong);mf=fields(mt)
            item['meshes']=[]
            for i in range(item['TexCount']):
                mesh=obj+mesh_array['offset']+ms*i
                vt,vp=nested(mf['Vertices']['type'],mesh+mf['Vertices']['offset'],'_Mypair','_Myval2')
                while '_Myfirst' not in fields(vt):vt,vp=member(vt,vp,'_Myval2')
                vf=fields(vt);begin=u32(vp+vf['_Myfirst']['offset']);end=u32(vp+vf['_Mylast']['offset'])
                assert 0<=end-begin<=65536
                vertices=list(struct.iter_unpack('<8f',read(begin,end-begin))) if end>begin else []
                item['meshes'].append({'vertices':len(vertices),'ranges':[(min(v[j] for v in vertices),max(v[j] for v in vertices)) for j in range(8)]})
                row=item['meshes'][-1]
                row['instances']=vector_size(mf['Instances']['type'],mesh+mf['Instances']['offset'],36)
                if 'Lods' in mf:
                    la=mf['Lods'];lt=info(la['type'],4);ls=info(lt,2,C.c_ulonglong);lf=fields(lt);row['lods']=[]
                    for level in range(3):
                        at=mesh+la['offset']+ls*level
                        row['lods'].append({'level':level,
                            'vertices':len(vertices) if level==0 else vector_size(lf['Vertices']['type'],at+lf['Vertices']['offset'],32),
                            'instances':vector_size(lf['Instances']['type'],at+lf['Instances']['offset'],36),
                            'geometry':hex(u32(mesh+mf['Geometry']['offset']) if level==0 else u32(at+lf['Geometry']['offset'])),
                            'placement':hex(u32(at+lf['Placement']['offset']))})
        results.append(item)
    assert u32(hp)==head
    return results
symbols = []
@Callback
def visit(pointer, size, context):
    s = pointer.contents
    if s.Tag == 7:
        symbols.append(dict(name=C.string_at(C.addressof(s)+Symbol.Name.offset, s.NameLen).decode(errors='replace'),
                            address=s.Address, size=s.Size, type=s.TypeIndex))
    return True
try:
    modules=(W.HMODULE*2048)(); needed=W.DWORD()
    if not k.K32EnumProcessModulesEx(handle, modules, C.sizeof(modules), C.byref(needed), 3): raise C.WinError(C.get_last_error())
    module=None; loaded={}
    for m in modules[:needed.value//C.sizeof(W.HMODULE)]:
        path=C.create_unicode_buffer(32768); k.K32GetModuleFileNameExW(handle,m,path,len(path))
        loaded[Path(path.value).name.lower()]=(m,path.value)
        if Path(path.value).name.lower()=='freelancer.exe': module=(m,path.value)
    assert module
    d.SymSetOptions(0x2|0x200)
    if not d.SymInitializeW(handle,str(Path(module[1]).parent),False): raise C.WinError(C.get_last_error())
    base=d.SymLoadModuleExW(handle,None,module[1],'freelancer',module[0],0,None,0)
    assert base
    if args.routes:
        from rp9_route_snapshot import capture
        capture(globals(), loaded)
        raise SystemExit(0)
    for mask in (b'*G_Fields*', b'*GCompositeConstants*', b'*GRaymarchConstants*', b'*GEntryCount*', b'*GEntries*', b'*G_FieldController*', b'*G_FieldEnclosure*',
                 b'*G_SimpleProgram*',b'*G_bSimpleProgramTried*',b'*GVolumeTargetScale*',b'*GVolumeTarget',b'*GExecutedLimit*',b'*GbProgramFailed*'):
        if not d.SymEnumSymbols(handle,base,mask,visit,None): raise C.WinError(C.get_last_error())
    report=[]
    for s in symbols:
        s['fields']=fields(s['type'])
        s['raw']=read(s['address'],min(s['size'],4096)).hex() if s['size'] else ''
        if s['name']=='G_Fields':
            try:s['fields_live']=far_fields(s)
            except (KeyError,OSError,AssertionError) as e:s['read_error']=str(e)
        report.append(s)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2))
    print(json.dumps([{k:v for k,v in s.items() if k not in ('raw','fields')} for s in report],indent=2))
finally:
    d.SymCleanup(handle); k.CloseHandle(handle)
