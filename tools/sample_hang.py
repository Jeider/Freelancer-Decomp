"""Read x86 thread registers and frame chains; always resume each sampled thread."""
import ctypes as c
from ctypes import wintypes as w
import sys,struct,json
from pathlib import Path
k=c.WinDLL('kernel32',use_last_error=True)
def api(name,args,rest=w.BOOL):
 f=getattr(k,name);f.argtypes=args;f.restype=rest;return f
op=api('OpenProcess',[w.DWORD,w.BOOL,w.DWORD],w.HANDLE)
ot=api('OpenThread',[w.DWORD,w.BOOL,w.DWORD],w.HANDLE)
close=api('CloseHandle',[w.HANDLE])
suspend=api('SuspendThread',[w.HANDLE],w.DWORD);resume=api('ResumeThread',[w.HANDLE],w.DWORD)
ctx=api('Wow64GetThreadContext',[w.HANDLE,c.c_void_p])
read=api('ReadProcessMemory',[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.c_void_p])
snap=api('CreateToolhelp32Snapshot',[w.DWORD,w.DWORD],w.HANDLE)
class TE(c.Structure):
 _fields_=[('size',w.DWORD),('usage',w.DWORD),('tid',w.DWORD),('pid',w.DWORD),('base',w.LONG),('delta',w.LONG),('flags',w.DWORD)]
first=api('Thread32First',[w.HANDLE,c.POINTER(TE)]);nxt=api('Thread32Next',[w.HANDLE,c.POINTER(TE)])
pid=int(sys.argv[1]);process=op(0x410,False,pid)
assert process,c.get_last_error()
threads=snap(4,0);entry=TE();entry.size=c.sizeof(entry);ok=first(threads,c.byref(entry));results=[]
while ok:
 if entry.pid==pid:
  thread=ot(0x5A,False,entry.tid)
  if thread:
   paused=suspend(thread)!=0xffffffff
   try:
    if paused:
     buf=c.create_string_buffer(716);struct.pack_into('<I',buf,0,0x10007)
     if ctx(thread,buf):
      ebp,eip,esp=struct.unpack_from('<I',buf,180)[0],struct.unpack_from('<I',buf,184)[0],struct.unpack_from('<I',buf,196)[0]
      frames=[eip];fp=ebp
      for _ in range(45):
       pair=c.create_string_buffer(8)
       if not read(process,fp,pair,8,None):break
       nextfp,ret=struct.unpack('<II',pair.raw)
       if ret:frames.append(ret)
       if nextfp<=fp or nextfp-fp>1048576:break
       fp=nextfp
      stack=c.create_string_buffer(2048);raw=stack.raw.hex() if read(process,esp,stack,2048,None) else ''
      regs=dict(zip(('edi','esi','ebx','edx','ecx','eax','ebp','eip'),struct.unpack_from('<8I',buf,156)))
      memory={}
      local=c.create_string_buffer(64)
      if read(process,ebp-64,local,64,None):
       memory['locals']=local.raw.hex()
       pool=struct.unpack_from('<I',local,48)[0]
       head=c.create_string_buffer(20)
       if read(process,pool,head,20,None):memory['pool']=head.raw.hex()
      for key,ptr in regs.items():
       block=c.create_string_buffer(256)
       if ptr and read(process,ptr,block,256,None):memory[key]=block.raw.hex()
      results.append(dict(tid=entry.tid,eip=hex(eip),esp=hex(esp),frames=[hex(x) for x in frames],stack=raw,registers=regs,memory=memory))
   finally:
    if paused:resume(thread)
    close(thread)
 ok=nxt(threads,c.byref(entry))
close(threads)
class ME(c.Structure):
 _fields_=[('size',w.DWORD),('id',w.DWORD),('pid',w.DWORD),('globaluse',w.DWORD),('processuse',w.DWORD),('base',c.c_void_p),('length',w.DWORD),('module',w.HMODULE),('name',w.WCHAR*256),('path',w.WCHAR*260)]
mf=api('Module32FirstW',[w.HANDLE,c.POINTER(ME)]);mn=api('Module32NextW',[w.HANDLE,c.POINTER(ME)])
ms=snap(0x18,pid);me=ME();me.size=c.sizeof(me);ok=mf(ms,c.byref(me));modules=[]
while ok:
 modules.append(dict(name=me.name,path=me.path,base=me.base,size=me.length))
 ok=mn(ms,c.byref(me))
close(ms);close(process)
out=Path('out/tau4_hang');out.mkdir(exist_ok=True,parents=True)
(out/'threads.json').write_text(json.dumps(results,indent=2))
(out/'modules.json').write_text(json.dumps(modules,indent=2))
for row in results:print(row['tid'],row['frames'])
