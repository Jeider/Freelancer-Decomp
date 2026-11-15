import ctypes as c,json
from ctypes import wintypes as w
from pathlib import Path
d=c.WinDLL('dbghelp',use_last_error=True)
h=w.HANDLE(0x123456)
d.SymSetOptions.argtypes=[w.DWORD];d.SymSetOptions(0x10|0x2000|0x80000000)
d.SymInitializeW.argtypes=[w.HANDLE,w.LPCWSTR,w.BOOL]
assert d.SymInitializeW(h,'D:/Games/FL_MOD/bin;D:/work/Freelancer-Decomp/bin',False)
d.SymLoadModuleExW.argtypes=[w.HANDLE,w.HANDLE,w.LPCWSTR,w.LPCWSTR,c.c_ulonglong,w.DWORD,c.c_void_p,w.DWORD];d.SymLoadModuleExW.restype=c.c_ulonglong
d.SymFromAddr.argtypes=[w.HANDLE,c.c_ulonglong,c.POINTER(c.c_ulonglong),c.c_void_p]
mods=json.loads(Path('out/tau4_hang/modules.json').read_text());threads=json.loads(Path('out/tau4_hang/threads.json').read_text())
for m in mods:
 if 'fl_mod' in m['path'].lower():d.SymLoadModuleExW(h,None,m['path'],None,m['base'],m['size'],None,0)
lines=[]
for frame in threads[0]['frames']:
 addr=int(frame,16);buf=c.create_string_buffer(2104)
 c.c_ulong.from_buffer(buf,0).value=88;c.c_ulong.from_buffer(buf,80).value=2000
 disp=c.c_ulonglong()
 module=next((m['name'] for m in mods if m['base']<=addr<m['base']+m['size']),'?')
 name=c.string_at(c.addressof(buf)+84).decode(errors='replace') if d.SymFromAddr(h,addr,c.byref(disp),buf) else '?'
 lines.append(f'{frame} {module}!{name}+{disp.value:x}')
print('\n'.join(lines))
Path('out/tau4_hang/stack.txt').write_text('\n'.join(lines))
