"""Read-only flight controls snapshot using the running client's matching PDB.

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
parser.add_argument('--poses',action='store_true',help='Read nearby ship poses from Common object lists')
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
@Callback
def visit(pointer,size,ctx):
    s=pointer.contents
    name=C.string_at(C.addressof(s)+Symbol.Name.offset,s.NameLen).decode(errors='replace')
    if s.Tag==7:symbols[name]=(s.Address,s.Size)
    return True
handle=k.OpenProcess(0x410,False,args.pid)
if not handle:raise C.WinError(C.get_last_error())
def read(address,size):
    if address<0x10000 or not 0<size<=65536:raise ValueError('Invalid bounded read')
    buf=C.create_string_buffer(size);n=C.c_size_t()
    if not k.ReadProcessMemory(handle,address,buf,size,C.byref(n)) or n.value!=size:raise C.WinError(C.get_last_error())
    return buf.raw
def u32(address):return struct.unpack('<I',read(address,4))[0]
try:
    mods=(W.HMODULE*2048)();needed=W.DWORD()
    if not k.K32EnumProcessModulesEx(handle,mods,C.sizeof(mods),C.byref(needed),3):raise C.WinError(C.get_last_error())
    module=None
    for m in mods[:needed.value//C.sizeof(W.HMODULE)]:
        path=C.create_unicode_buffer(32768);k.K32GetModuleFileNameExW(handle,m,path,len(path))
        if Path(path.value).name.lower()=='freelancer.exe':module=(m,path.value);break
    if not module:raise ValueError('Client not found')
    d.SymSetOptions(0x2|0x200)
    if not d.SymInitializeW(handle,str(Path(module[1]).parent),False):raise C.WinError(C.get_last_error())
    base=d.SymLoadModuleExW(handle,None,module[1],'freelancer',module[0],0,None,0)
    if not base:raise C.WinError(C.get_last_error())
    if not d.SymEnumSymbols(handle,base,b'*',visit,None):raise C.WinError(C.get_last_error())
    result={}
    for name,(address,size) in symbols.items():
        if any(key in name for key in ['G_PlayerShipWatcher','G_bNnScreenUp','G_bPlayerLaunchAcknowledged',
            'G_PlayerBase','G_SpaceNextState','G_CourierTransferBase','G_Letterbox','G_HudKey','G_Input','G_Keyboard',
            'G_KeyFocus','G_HudCmdMode1Filter','G_HudCmdFocusStack','G_HudCmdCancelCount','G_bInput','G_bActive','G_bConsole','GCurrentKey','G_KeyMap',
            'GActiveGroups','G_HudCmdRegistryPtr','Dialog','G_HudCmdRecord','G_bLocationInTransition','G_MouseCursorDrawFlag']):
            if 0<size<=32:result[name]={'address':hex(address),'size':size,'hex':read(address,size).hex()}
    matches=[a for n,(a,s) in symbols.items() if n.endswith('G_PlayerShipWatcher')]
    if len(matches)==1:
        watched=u32(matches[0]);gameobj=watched-8;ship=u32(gameobj+0x10)
        manager=u32(ship+0x194)
        result['player']={'ship':hex(ship),'id':u32(ship+0xb0),'class':hex(u32(ship+0x4c)),
            'exclusion':u32(ship+0x190),'throttle':struct.unpack('<f',read(ship+0x29c,4))[0],
            'manager':hex(manager)}
        if manager:result['player'].update(maneuver_mask=hex(u32(manager+0xb8)),
            maneuver_lock=read(manager+0xbc,1)[0],behavior=u32(manager+0xc0))
    else:result['watcher_matches']=matches
    if args.poses and len(matches)==1:
        origin=struct.unpack('<3f',read(ship+0x2c,12))
        result={'player_id':u32(ship+0xb0),'ships':[]}
        for m in mods[:needed.value//C.sizeof(W.HMODULE)]:
            path=C.create_unicode_buffer(32768);k.K32GetModuleFileNameExW(handle,m,path,len(path))
            if Path(path.value).name.lower()!='common.dll':continue
            common=d.SymLoadModuleExW(handle,None,path.value,'Common',m,0,None,0)
            if not common:raise C.WinError(C.get_last_error())
            d.SymEnumSymbols(handle,common,b'*G_ClassLists*',visit,None)
            lists=[a for n,(a,s) in symbols.items() if n.endswith('G_ClassLists')]
            if len(lists)!=1:raise ValueError('Missing Common class list symbol')
            head=u32(lists[0]+7*12+4);node=u32(head)
            for _ in range(1024):
                if node==head:break
                obj=u32(node+8);pos=struct.unpack('<3f',read(obj+0x2c,12))
                if sum((p-q)**2 for p,q in zip(pos,origin))<2500**2:
                    result['ships'].append(dict(id=u32(obj+0xb0),object=hex(obj),
                        position=pos,rotation=struct.unpack('<9f',read(obj+8,36))))
                node=u32(node)
            break
    print(json.dumps(result,indent=2))
finally:
    d.SymCleanup(handle);k.CloseHandle(handle)
