"""Read-only train/autopilot snapshot. Never suspends or writes the game process."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import struct
import time

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pid',type=int,required=True)
parser.add_argument('--seconds',type=float,default=0)
parser.add_argument('--symbols',action='store_true')
parser.add_argument('--coupling',action='store_true',help='Inspect the one-body locomotive approach controller')
args=parser.parse_args()
k=C.WinDLL('kernel32',use_last_error=True)
d=C.WinDLL('C:/Program Files (x86)/Windows Kits/10/Debuggers/x64/dbghelp.dll',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.CloseHandle.argtypes=[W.HANDLE]
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.K32EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
k.K32GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
class MemoryInfo(C.Structure):
    _fields_=[('base',C.c_void_p),('allocation',C.c_void_p),('allocation_protect',W.DWORD),
              ('region_size',C.c_size_t),('state',W.DWORD),('protect',W.DWORD),('kind',W.DWORD)]
k.VirtualQueryEx.argtypes=[W.HANDLE,C.c_void_p,C.POINTER(MemoryInfo),C.c_size_t]
k.VirtualQueryEx.restype=C.c_size_t
h=k.OpenProcess(0x410,False,args.pid)
if not h:raise C.WinError(C.get_last_error())

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
def read(address,size):
    if address<0x10000 or not 0<size<=65536:raise ValueError('Invalid bounded read')
    buf=C.create_string_buffer(size);n=C.c_size_t()
    if not k.ReadProcessMemory(h,address,buf,size,C.byref(n)) or n.value!=size:raise C.WinError(C.get_last_error())
    return buf.raw
def u32(p):return struct.unpack('<I',read(p,4))[0]
def floats(p,n=1):return struct.unpack('<'+'f'*n,read(p,n*4))
def ship_snapshot(ship):
    body=u32(ship+0x54)
    result=dict(ship=hex(ship),position=floats(ship+0x2c,3),throttle=floats(ship+0x29c)[0],
                nudge=floats(ship+0x274,3),lane=bool(read(ship+0x2bc,1)[0]),
                orientation=floats(ship+0x8,9),steering=floats(ship+0x24c,3),
                lane_speed=floats(ship+0x2b8)[0],control_exclusion=u32(ship+0x190),body=hex(body))
    manager=u32(ship+0x194)
    if manager:
        result['behavior']=u32(manager+0xc0)
        dock=u32(manager+0x190)
        if dock:
            sys=u32(dock+0x24)
            result['dock']=dict(state=u32(dock+0x320),flags=hex(u32(dock+0x32c)),
                cleared=read(dock+0x334,1)[0],destination=floats(dock+0x3cc,3),
                saved_point=floats(dock+0x3fc,3),mount_offset=floats(dock+0x430,3),
                max_speed=floats(dock+0x46c)[0],move_throttle=floats(dock+0x70)[0],
                spline_throttle=floats(dock+0x168+0x14+0x40)[0],
                spline_cap=floats(dock+0x168+0x154)[0],
                spline_t=floats(dock+0x168+0x170)[0],
                spline_length=floats(dock+0x168+0x164)[0],
                nav_radius=floats(sys+0x1514)[0],nav_center=floats(sys+0x1508,3),
                spline_points=floats(u32(dock+0x168+0x14c),12))
    return result
train_address=0
def train_head(address,vtable):
    if u32(address)!=vtable:raise ValueError('Train controller replaced')
    first,end=struct.unpack('<2I',read(address+0x14,8))
    if end-first!=(1 if args.coupling else 21)*4:raise ValueError('Wrong train body count')
    ship=u32(first)
    if u32(ship+0x4c)!=0x503:raise ValueError('Not a ship')
    return ship

def coupling_snapshot(ship):
    # Offsets verified with MSVC /d1reportSingleClassLayoutTrain for the smooth
    # capture build. Read-only; no remote calls, suspension or process writes.
    pos=floats(ship+0x2c,3);rot=floats(ship+0x8,9)
    target=struct.unpack('<3d',read(train_address+136,24))
    rear=struct.unpack('<3d',read(train_address+160,24))
    pin=tuple(pos[i]+sum(rot[3*i+j]*rear[j] for j in range(3)) for i in range(3))
    tail=u32(train_address+84)
    result=dict(controller=hex(train_address),ship=hex(ship),position=pos,orientation=rot,
        capture_tail=hex(tail),capture_time=struct.unpack('<d',read(train_address+216,8))[0],
        align_time=struct.unpack('<d',read(train_address+224,8))[0],ready=bool(read(train_address+232,1)[0]),
        pin=pin,target_pin=target,pin_error=tuple(pin[i]-target[i] for i in range(3)))
    if tail:result['tail_position']=floats(tail+0x2c,3);result['tail_orientation']=floats(tail+0x8,9)
    return result
def snapshot():
    global train_address
    tables=[a for n,(a,size) in symbols.items() if 'Train::' in n and 'vftable' in n]
    if len(tables)!=1:raise ValueError('Expected unique Train controller vtable')
    vtable=tables[0]
    if train_address:
        ship=train_head(train_address,vtable)
        return coupling_snapshot(ship) if args.coupling else ship_snapshot(ship)
    # Optimized PDBs omit the function-local registry. Find the typed controller
    # in committed private pages, checking its vector and ship before use.
    pattern=struct.pack('<I',vtable);address=0x10000;rejected=[]
    while address<0x100000000:
        info=MemoryInfo()
        if not k.VirtualQueryEx(h,address,C.byref(info),C.sizeof(info)):break
        end=info.base+info.region_size
        if info.state==0x1000 and info.kind==0x20000 and info.protect&0xcc and not info.protect&0x100:
            for at in range(info.base,end,65536):
                try:data=read(at,min(65536,end-at))
                except OSError:continue
                start=0
                while True:
                    offset=data.find(pattern,start)
                    if offset<0:break
                    start=offset+4
                    try:
                        ship=train_head(at+offset,vtable)
                        train_address=at+offset
                        return coupling_snapshot(ship) if args.coupling else ship_snapshot(ship)
                    except (OSError,ValueError) as e:
                        if len(rejected)<8:rejected.append(str(e))
        address=end
    raise ValueError('No active 20-wagon controller found: '+str(rejected))
try:
    mods=(W.HMODULE*2048)();needed=W.DWORD()
    if not k.K32EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3):raise C.WinError(C.get_last_error())
    module=None
    for m in mods[:needed.value//C.sizeof(W.HMODULE)]:
        name=C.create_unicode_buffer(32768)
        k.K32GetModuleFileNameExW(h,m,name,len(name))
        if Path(name.value).name.lower()=='common.dll':module=(m,name.value);break
    if not module:raise ValueError('Common.dll not loaded')
    d.SymSetOptions(0x2|0x200)
    if not d.SymInitializeW(h,str(Path(module[1]).parent),False):raise C.WinError(C.get_last_error())
    base=d.SymLoadModuleExW(h,None,module[1],'Common',module[0],0,None,0)
    if not base:raise C.WinError(C.get_last_error())
    if not d.SymEnumSymbols(h,base,b'*' if args.symbols else b'*CmnTrain*',visit,None):raise C.WinError(C.get_last_error())
    if args.symbols:
        print(json.dumps({n:a for n,a in symbols.items() if 'value' in n.lower() or 'registry' in n.lower()}))
        raise SystemExit(0)
    until=time.monotonic()+min(max(args.seconds,0),45)
    while True:
        try:print(json.dumps(snapshot()),flush=True)
        except (OSError,ValueError) as e:print(json.dumps({'read_error':str(e),'symbols':symbols}),flush=True)
        if time.monotonic()>=until:break
        time.sleep(.5)
finally:
    d.SymCleanup(h);k.CloseHandle(h)
