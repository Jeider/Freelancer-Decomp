"""Check binary exports and load the staged Server/Content against installed dependencies."""
import re
import subprocess
from build_mission import ROOT,OUT,GAME,compiler_env

def main():
    compiler,env=compiler_env();env['PATH']=str(GAME)+';'+env['PATH']
    env['INCLUDE']+=';'+str(ROOT/'src/include')
    def exports(path):
        result=subprocess.check_output([str(compiler/'dumpbin.exe'),'/exports',str(path)],env=env,text=True)
        return set(re.findall(r'^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\S+)',result,re.M))
    for name in ('Server.dll','Content.dll'):
        before=exports(GAME/name);after=exports(OUT/name)
        assert before<=after,(name,before-after)
    symbol=next(s for s in exports(OUT/'Server.dll') if s.startswith('?GetCloakEventSequence@'))
    source=OUT/'check_load.cpp'
    source.write_text(r'''
#include <windows.h>
#include <dbghelp.h>
#include <cstdio>
#include "dacom.h"
#include "dalib_core.h"
struct IFileSystem;
namespace DALib { DALIB_API extern ICOManager* Dacom; DALIB_API extern IFileSystem* Data; }
#pragma comment(lib,"dbghelp.lib")
void __cdecl QuietDump(int,const char*,...){}
LONG CALLBACK Trace(EXCEPTION_POINTERS* e){
    HMODULE m=nullptr;char name[MAX_PATH]={};
    auto pc=e->ExceptionRecord->ExceptionAddress;
    GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,static_cast<LPCSTR>(pc),&m);
    GetModuleFileNameA(m,name,MAX_PATH);
    printf("exception %08lx at %s + %lx\n",e->ExceptionRecord->ExceptionCode,name,static_cast<unsigned long>(reinterpret_cast<size_t>(pc)-reinterpret_cast<size_t>(m)));
    SymInitialize(GetCurrentProcess(),nullptr,TRUE);
    char buffer[sizeof(SYMBOL_INFO)+MAX_SYM_NAME]={};auto sym=reinterpret_cast<SYMBOL_INFO*>(buffer);
    sym->SizeOfStruct=sizeof(SYMBOL_INFO);sym->MaxNameLen=MAX_SYM_NAME;DWORD64 disp=0;
    if(SymFromAddr(GetCurrentProcess(),reinterpret_cast<DWORD64>(pc),&disp,sym))printf("symbol %s + %llu\n",sym->Name,disp);
    IMAGEHLP_LINE64 line={sizeof(line)};DWORD ld=0;
    if(SymGetLineFromAddr64(GetCurrentProcess(),reinterpret_cast<DWORD64>(pc),&ld,&line))printf("line %s:%lu\n",line.FileName,line.LineNumber);
    printf("access address %p, eax %lx ecx %lx edx %lx\n",reinterpret_cast<void*>(e->ExceptionRecord->ExceptionInformation[1]),e->ContextRecord->Eax,e->ContextRecord->Ecx,e->ContextRecord->Edx);
    fflush(stdout);return EXCEPTION_CONTINUE_SEARCH;
}
int main(int argc,char** argv){
    if(argc!=4)return 1;
    AddVectoredExceptionHandler(1,Trace);
    FDUMP=QuietDump;
    if(!LoadLibraryA("ReadFile.dll"))return 6;
    DALib::Dacom=DACOM_Acquire();DALib::OpenData(".");if(!DALib::Data)return 7;
    if(!LoadLibraryA("x86math.dll"))return 5;
    auto server=LoadLibraryA(argv[1]);if(!server){printf("Server load error %lu\n",GetLastError());return 2;}
    auto get=reinterpret_cast<unsigned long long(__cdecl*)()>(GetProcAddress(server,argv[3]));
    if(!get||get()!=0)return 3;
    auto content=LoadLibraryA(argv[2]);if(!content){printf("Content load error %lu\n",GetLastError());return 4;}
    puts("PASS staged Server/Content load with installed dependencies and cloak event export");
    FreeLibrary(content);FreeLibrary(server);DALib::CloseData();return 0;
}
''')
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/O2','/MD',str(source),'/Fo'+str(OUT/'check_load.obj'),
        '/Fe'+str(OUT/'check_load.exe'),'/link',str(ROOT/'bin/dacom.lib'),str(ROOT/'bin/DALib.lib')],env=env,cwd=OUT,check=True)
    result=subprocess.run([str(OUT/'check_load.exe'),str(OUT/'Server.dll'),str(OUT/'Content.dll'),symbol],env=env,cwd=OUT)
    if result.returncode:
        print('Checking installed Content as control',flush=True)
        subprocess.run([str(OUT/'check_load.exe'),str(OUT/'Server.dll'),str(GAME/'Content.dll'),symbol],env=env,cwd=OUT)
    result.check_returncode()
    print('PASS all installed Server/Content exports preserved')

if __name__=='__main__':main()
