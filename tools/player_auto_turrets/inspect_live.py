"""Read-only Win32 turret diagnostics using the matching local release PDB.

Does not attach a debugger, suspend threads, or write process memory.
Pass --pid and --base (the executable's runtime base) for live inspection.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import struct
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pid', type=int, default=0)
parser.add_argument('--base', type=lambda s: int(s, 0), default=0x400000)
parser.add_argument('--seconds', type=float, default=0)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
kernel = C.WinDLL('kernel32', use_last_error=True)
debug = C.WinDLL('C:/Program Files (x86)/Windows Kits/10/Debuggers/x64/dbghelp.dll', use_last_error=True)
kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
kernel.OpenProcess.restype = W.HANDLE
kernel.GetCurrentProcess.restype = W.HANDLE
kernel.CloseHandle.argtypes = [W.HANDLE]
kernel.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
kernel.ReadProcessMemory.restype = W.BOOL
handle = kernel.OpenProcess(0x410, False, args.pid) if args.pid else kernel.GetCurrentProcess()
if not handle:
    raise C.WinError(C.get_last_error())

class Symbol(C.Structure):
    _fields_ = [('SizeOfStruct', W.ULONG), ('TypeIndex', W.ULONG), ('Reserved', C.c_ulonglong * 2),
                ('Index', W.ULONG), ('Size', W.ULONG), ('ModBase', C.c_ulonglong), ('Flags', W.ULONG),
                ('Value', C.c_ulonglong), ('Address', C.c_ulonglong), ('Register', W.ULONG),
                ('Scope', W.ULONG), ('Tag', W.ULONG), ('NameLen', W.ULONG), ('MaxNameLen', W.ULONG), ('Name', C.c_char * 1)]
Callback = C.WINFUNCTYPE(W.BOOL, C.POINTER(Symbol), W.ULONG, C.c_void_p)
debug.SymInitializeW.argtypes = [W.HANDLE, W.LPCWSTR, W.BOOL]
debug.SymInitializeW.restype = W.BOOL
debug.SymLoadModuleExW.argtypes = [W.HANDLE, W.HANDLE, W.LPCWSTR, W.LPCWSTR, C.c_ulonglong, W.DWORD, C.c_void_p, W.DWORD]
debug.SymLoadModuleExW.restype = C.c_ulonglong
debug.SymEnumSymbols.argtypes = [W.HANDLE, C.c_ulonglong, C.c_char_p, Callback, C.c_void_p]
debug.SymEnumSymbols.restype = W.BOOL
debug.SymCleanup.argtypes = [W.HANDLE]
symbols = {}

@Callback
def visit(pointer, size, context):
    symbol = pointer.contents
    name = C.string_at(C.addressof(symbol) + Symbol.Name.offset, symbol.NameLen).decode('utf-8', errors='replace')
    if symbol.Tag == 7:  # SymTagData; exclude functions and parameters.
        symbols[name] = (symbol.Address, symbol.Size)
    return True

def read(address, size):
    if address <= 0 or size < 0 or size > 65536:
        raise ValueError('Invalid bounded read')
    buffer = C.create_string_buffer(size)
    received = C.c_size_t()
    if not kernel.ReadProcessMemory(handle, address, buffer, size, C.byref(received)) or received.value != size:
        raise C.WinError(C.get_last_error())
    return buffer.raw

def global_data(key):
    matches = [value for name, value in symbols.items() if name.endswith('::' + key)]
    if len(matches) != 1:
        raise ValueError(f'Expected one symbol for {key}, got {len(matches)}')
    address, size = matches[0]
    return read(address, size)

def u32(address):
    return struct.unpack('<I', read(address, 4))[0]

def scanner_snapshot(owner):
    result = {'ship': hex(owner), 'db': hex(u32(owner+0xac)), 'physics_system': u32(owner+0x50), 'contacts': []}
    origin = struct.unpack('<3f', read(owner+0x2c,12))
    for offset in (0x08, 0x14):
        equip_list = u32(owner+0xe4+offset)
        if not equip_list:
            continue
        head = u32(equip_list+4)  # Release checked-iterator std::list proxy/head/size
        node = u32(head)
        for _ in range(256):
            if node == head:
                break
            equip = u32(node+8)
            if u32(equip+0x14) & 0x80000:
                count = u32(equip+0x824)
                result['count'] = count
                result['mask'] = hex(u32(equip+0x83c))
                if count > 256:
                    raise ValueError('Invalid scanner count')
                for i in range(count):
                    watched = u32(equip+0x24+i*8)
                    if not watched:
                        continue
                    obj = u32(watched-8+0x10)
                    pos = struct.unpack('<3f',read(obj+0x2c,12))
                    result['contacts'].append(dict(object=hex(obj), id=u32(obj+0xb0),
                        kind=hex(u32(obj+0x4c)), db=hex(u32(obj+0xac)), physics_system=u32(obj+0x50),
                        flags=hex(u32(obj+0xa0)),
                        distance=sum((a-b)**2 for a,b in zip(pos,origin))**.5))
            node = u32(node)
    return result

def snapshot():
    result = {}
    for key in ('mode', 'status', 'reserve', 'energyHold', 'system'):
        data = global_data(key)
        result[key] = int.from_bytes(data, 'little')
    result['status_name'] = ['Off','Ready','NoTurrets','NoTarget','NoScanner','Suspended','Energy','Aiming','Blocked','Firing','Multiplayer'][result['status']]
    proxy, first, last, end = struct.unpack('<4I', global_data('members'))
    if last < first or last - first > 24 * 128 or (last - first) % 24:
        raise ValueError('Unexpected member layout or concurrent replacement')
    result['members'] = []
    if first != last:
        data = read(first, last-first)
        for at in range(0, len(data), 24):
            equip_id, gun, selected, manual, target, search, held = struct.unpack_from('<H2xIBB2xIff', data, at)
            equip = read(gun, 0x54)
            owner, arch = struct.unpack_from('<I', equip, 4)[0], struct.unpack_from('<I', equip, 12)[0]
            result['members'].append(dict(id=equip_id, gun=hex(gun), selected=bool(selected), manual=bool(manual),
                active=equip[0x10], destroyed=equip[0x11], target=target,
                refire=struct.unpack_from('<f', equip, 0x50)[0],
                power_usage=struct.unpack('<f',read(arch+0x8c,4))[0],
                refire_delay=struct.unpack('<f',read(arch+0x90,4))[0],
                power=struct.unpack('<2f',read(owner+0x198,8))))
        result['scanner'] = scanner_snapshot(owner)
    return result

try:
    debug.SymSetOptions(0x00000002 | 0x00000200)  # undecorated names, no critical-error dialogs
    if not debug.SymInitializeW(handle, str(repo / 'bin'), False):
        raise C.WinError(C.get_last_error())
    base = debug.SymLoadModuleExW(handle, None, str(repo / 'bin/freelancer.exe'), 'freelancer', args.base, 0, None, 0)
    if not base:
        raise C.WinError(C.get_last_error())
    if not debug.SymEnumSymbols(handle, base, b'*PlayerAutoTurrets*', visit, None):
        raise C.WinError(C.get_last_error())
    if not args.pid:
        print(json.dumps(symbols, indent=2))
    else:
        until = time.monotonic() + min(max(args.seconds, 0), 45)
        while True:
            try:
                print(json.dumps(snapshot()), flush=True)
            except (OSError, ValueError) as error:
                print(json.dumps({'read_error': str(error)}), flush=True)
            if time.monotonic() >= until:
                break
            time.sleep(0.25)
finally:
    debug.SymCleanup(handle)
    if args.pid:
        kernel.CloseHandle(handle)
