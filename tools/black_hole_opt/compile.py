"""Compile using the same D3DX9_43 compiler as RP9; save bytecode and disassembly."""
from pathlib import Path
import ctypes as c
import sys,time

root=Path(__file__).resolve().parents[2]
source=Path(sys.argv[1]); stem=Path(sys.argv[2]); flags=int(sys.argv[3],0)
entry=sys.argv[4] if len(sys.argv)>4 else 'PSMain'
profile='vs_3_0' if entry.startswith('VS') else 'ps_3_0'
dll=c.WinDLL('d3dx9_43.dll')
ptr=c.c_void_p
def method(obj,idx,result,*args):
    table=c.cast(obj,c.POINTER(c.POINTER(ptr))).contents
    return c.WINFUNCTYPE(result,ptr,*args)(table[idx])
def blob(obj):
    address=method(obj,3,ptr)(obj)
    size=method(obj,4,c.c_uint32)(obj)
    return c.string_at(address,size)
code=ptr(); errors=ptr()
data=source.read_bytes()
compile=dll.D3DXCompileShader
compile.argtypes=[c.c_char_p,c.c_uint32,ptr,ptr,c.c_char_p,c.c_char_p,c.c_uint32,c.POINTER(ptr),c.POINTER(ptr),ptr]
compile.restype=c.c_long
t=time.perf_counter()
hr=compile(data,len(data),None,None,entry.encode(),profile.encode(),flags,c.byref(code),c.byref(errors),None)
stem.parent.mkdir(parents=True,exist_ok=True)
if errors: stem.with_suffix('.log').write_bytes(blob(errors))
print(f'{entry} flags={flags} compile={time.perf_counter()-t:.2f}s HRESULT={hr}',flush=True)
if hr<0:
    print(blob(errors).decode(errors='replace')[-2000:] if errors else 'no diagnostics')
    sys.exit(1)
stem.with_suffix('.cso').write_bytes(blob(code))
assembly=ptr()
dis=dll.D3DXDisassembleShader
dis.argtypes=[ptr,c.c_int,c.c_char_p,c.POINTER(ptr)]
dis.restype=c.c_long
assert dis(method(code,3,ptr)(code),0,None,c.byref(assembly))>=0
stem.with_suffix('.asm').write_bytes(blob(assembly))
for obj in (assembly,code,errors):
    if obj:method(obj,2,c.c_ulong)(obj)
