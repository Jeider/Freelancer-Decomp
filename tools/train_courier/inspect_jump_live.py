"""Read-only courier transit and client visibility snapshot using matching PDBs.

No debugger attachment, thread suspension, remote calls or process writes.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import struct

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pid',type=int,required=True)
parser.add_argument('--ship-id',type=int,action='append',default=[],help='Limit detailed ship output to this ID (repeatable)')
args=parser.parse_args()
k=C.WinDLL('kernel32',use_last_error=True)
d=C.WinDLL('C:/Program Files (x86)/Windows Kits/10/Debuggers/x64/dbghelp.dll',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.CloseHandle.argtypes=[W.HANDLE]
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.K32EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
k.K32GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
class Symbol(C.Structure):
    _fields_=[('SizeOfStruct',W.ULONG),('TypeIndex',W.ULONG),('Reserved',C.c_ulonglong*2),
              ('Index',W.ULONG),('Size',W.ULONG),('ModBase',C.c_ulonglong),('Flags',W.ULONG),
              ('Value',C.c_ulonglong),('Address',C.c_ulonglong),('Register',W.ULONG),
              ('Scope',W.ULONG),('Tag',W.ULONG),('NameLen',W.ULONG),('MaxNameLen',W.ULONG),('Name',C.c_char*1)]
Callback=C.WINFUNCTYPE(W.BOOL,C.POINTER(Symbol),W.ULONG,C.c_void_p)
d.SymInitializeW.argtypes=[W.HANDLE,W.LPCWSTR,W.BOOL]
d.SymLoadModuleExW.argtypes=[W.HANDLE,W.HANDLE,W.LPCWSTR,W.LPCWSTR,C.c_ulonglong,W.DWORD,C.c_void_p,W.DWORD]
d.SymLoadModuleExW.restype=C.c_ulonglong
d.SymEnumSymbols.argtypes=[W.HANDLE,C.c_ulonglong,C.c_char_p,Callback,C.c_void_p]
d.SymCleanup.argtypes=[W.HANDLE]
symbols={}
types={}
@Callback
def visit(pointer,size,ctx):
    s=pointer.contents
    name=C.string_at(C.addressof(s)+Symbol.Name.offset,s.NameLen).decode(errors='replace')
    if s.Tag==7:symbols[name]=(s.Address,s.Size)
    if 'Courier' in name and 'std::' not in name:types[name]=s.TypeIndex
    return True
handle=k.OpenProcess(0x410,False,args.pid)
if not handle:raise C.WinError(C.get_last_error())
def read(address,size):
    if address<0x10000 or not 0<size<=65536:raise ValueError('Invalid bounded read')
    buf=C.create_string_buffer(size);n=C.c_size_t()
    if not k.ReadProcessMemory(handle,address,buf,size,C.byref(n)) or n.value!=size:raise C.WinError(C.get_last_error())
    return buf.raw
def u32(address):return struct.unpack('<I',read(address,4))[0]
d.SymEnumTypes.argtypes=[W.HANDLE,C.c_ulonglong,Callback,C.c_void_p]
d.SymGetTypeInfo.argtypes=[W.HANDLE,C.c_ulonglong,W.ULONG,C.c_int,C.c_void_p]
k.LocalFree.argtypes=[C.c_void_p]
def fields(base,typeid):
    count=W.ULONG()
    if not d.SymGetTypeInfo(handle,base,typeid,13,C.byref(count)):return []
    children=(W.ULONG*(2+count.value))();children[0]=count.value
    if not d.SymGetTypeInfo(handle,base,typeid,7,children):return []
    result=[]
    for child in children[2:]:
        name=C.c_void_p();offset=W.ULONG()
        if not d.SymGetTypeInfo(handle,base,child,1,C.byref(name)):continue
        value=C.wstring_at(name);k.LocalFree(name)
        if d.SymGetTypeInfo(handle,base,child,10,C.byref(offset)):result.append((value,offset.value))
    return result
try:
    mods=(W.HMODULE*2048)();needed=W.DWORD()
    if not k.K32EnumProcessModulesEx(handle,mods,C.sizeof(mods),C.byref(needed),3):raise C.WinError(C.get_last_error())
    d.SymSetOptions(0x2|0x200)
    if not d.SymInitializeW(handle,'D:/Games/FL_MOD/bin',False):raise C.WinError(C.get_last_error())
    for m in mods[:needed.value//C.sizeof(W.HMODULE)]:
        path=C.create_unicode_buffer(32768);k.K32GetModuleFileNameExW(handle,m,path,len(path))
        name=Path(path.value).name
        if name.lower() not in ('content.dll','server.dll','common.dll','freelancer.exe'):continue
        base=d.SymLoadModuleExW(handle,None,path.value,name,m,0,None,0)
        symbols.clear();d.SymEnumSymbols(handle,base,b'*',visit,None)
        print(name)
        types.clear();d.SymEnumTypes(handle,base,visit,None)
        for t,idx in types.items():
            if t.endswith('Courier') or t.endswith('CourierMission'):print('TYPE',t,fields(base,idx))
        for n,(a,size) in symbols.items():
            if any(v in n for v in ('couriers','controllers','GInTransitObjects')):
                print(n,hex(a),size,read(a,min(size,32)).hex())
                if size==12:
                    head=u32(a+4);count=u32(a+8)
                    print('head',hex(head),'count',count)
                    if count and count<20:
                        node=u32(head)
                        print('first',hex(node),'key',u32(node+16),'value',read(node+20,128).hex())
                        obj=u32(node+20) if n=='controllers' else node+20
                        for t,idx in types.items():
                            if (n=='controllers' and t.endswith('CourierMission')) or (n=='couriers' and t.endswith('Courier')):
                                for field,offset in fields(base,idx):
                                    if field in ('trailer','jumping','jumpDestination','ready','started','restoreCargo','failed','state','inTransit','transitSystem','transitStatus'):
                                        print('FIELD',field,offset,read(obj+offset,4).hex())
        if name.lower()=='common.dll':
            for n,(a,size) in symbols.items():
                if n=='G_ClassLists':
                    head=u32(a+7*12+4);node=u32(head)
                    for _ in range(1024):
                        if node==head:break
                        obj=u32(node+8)
                        if not args.ship_id or u32(obj+0xb0) in args.ship_id:print('SHIP',u32(obj+0xb0),hex(obj),'owner',u32(obj+0xb4),'physics',hex(u32(obj+0x50)),'body',hex(u32(obj+0x54)),'pos',struct.unpack('<3f',read(obj+0x2c,12)),'hp',struct.unpack('<f',read(obj+0xb8,4))[0],'db',hex(u32(obj+0xac)))
                        node=u32(node)
        if name.lower()=='freelancer.exe':
            for n,(a,size) in symbols.items():
                if n=='G_ClientObjDb':
                    count=u32(a+16);go=u32(a+20);ids=[]
                    for _ in range(min(count,1024)):
                        if not go:break
                        obj=u32(go+16);id=u32(obj+0xb0) if obj else 0;ids.append(id)
                        if not args.ship_id or id in args.ship_id:print('CLIENT_SHIP',id,hex(go),hex(obj),'draw',read(go+0x38,16).hex())
                        go=u32(go+20)
                    print('CLIENT_IDS',ids)
finally:
    d.SymCleanup(handle);k.CloseHandle(handle)
