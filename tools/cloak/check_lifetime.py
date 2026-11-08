"""Run the actual cloak cache functions after the engine frees its borrowed facet."""
from pathlib import Path
import subprocess
from build_visual import ROOT,OUT,compiler_env

PREFIX=r'''
#define NOMINMAX
#include <windows.h>
#include <map>
#include <memory>
#include <vector>
#include <cassert>
#include <cstdio>
#include "cloak_geometry.h"
struct FRPExBuffer {std::vector<unsigned char> Bytes;};
struct FRPExProgram {};struct FRPExTexture {};struct IRPSceneCapture {};
struct Ref {unsigned VertexStart,VertexCount,IndexStart,IndexCount,FacegroupStart,FacegroupCount;};
struct IVMeshPart {virtual Ref* GetRef()=0;virtual void* GetHeader()=0;virtual void Release()=0;};
static unsigned Releases=0,Created=0,Destroyed=0;
struct Borrowed:IVMeshPart {
 Ref R={0,3,0,3,0,1};unsigned char Data[106]={};
 Borrowed(){
  unsigned header[]={1,4};memcpy(Data,header,8);
  unsigned short counts[]={1,3,0x12,3};memcpy(Data+8,counts,8);
  unsigned short group[]={0,2,3,0};memcpy(Data+20,group,8);
  unsigned short indices[]={0,1,2};memcpy(Data+28,indices,6);
  float vertices[]={0,0,0,0,0,1, 1,0,0,0,0,1, 0,1,0,0,0,1};memcpy(Data+34,vertices,72);
 }
 Ref* GetRef() override{return &R;}void* GetHeader() override{return Data;}
 void Release() override{++Releases;}
};
struct Renderer {int Lod=0,Count=2;int GetInstanceCurrentLod(void*,int* p){*p=Lod;return 0;}
 int GetInstanceLodCount(void*,int* p){*p=Count;return 0;}
 int SetInstanceLod(void*,int n){Lod=n;return n==Count?-1:0;}};
struct Engine {IVMeshPart* Part=nullptr;bool Fail=false;int QueryInstance(void*,const char*,void** p){*p=Fail?nullptr:Part;return Fail?-1:0;}};
struct Pipeline {int CreateExVertexBuffer(unsigned size,void* data,FRPExBuffer** p){
 *p=new FRPExBuffer;(*p)->Bytes.assign((unsigned char*)data,(unsigned char*)data+size);++Created;return 0;}
 void DestroyExVertexBuffer(FRPExBuffer* p){delete p;++Destroyed;}};
namespace DALib {static ::Renderer R;static ::Engine E;static ::Renderer* Renderer=&R;static ::Engine* Engine=&E;}
namespace Iids {static const char* VMeshLibrary="borrowed facet";}
namespace RenderEx {static Pipeline P;Pipeline* GetPipelineEx(){return &P;}}
static const int GR_OK=0;
'''
MAIN=r'''
int main(){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 void* page=VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);assert(page);
 auto* part=new(page)Borrowed;DALib::E.Part=part;
 auto* first=Geometry((void*)1);assert(first&&first->Count==3&&Created==1);
 assert(Geometry((void*)1)==first&&Created==1);
 // The renderer destroys archetypes directly, regardless of queried interfaces.
 part->~Borrowed();DWORD old;assert(VirtualProtect(page,4096,PAGE_NOACCESS,&old));
 ClearMeshes();assert(Destroyed==1&&Releases==0);
 puts("PASS: cache clear after system unload never touches the freed engine facet");
 assert(VirtualProtect(page,4096,PAGE_READWRITE,&old));part=new(page)Borrowed;DALib::E.Part=part;
 first=Geometry((void*)1);assert(first&&Created==2);
 auto* buffer=first->Buffer;
 // Address reuse / model reload within the same system must not return stale geometry.
 float changed=7;memcpy(part->Data+34,&changed,4);
 FrameLibraries.clear();auto* second=Geometry((void*)1);assert(second&&second->Buffer!=buffer&&Created==3);
 puts("PASS: same-address replacement uses new vertex content");
 DALib::R.Lod=2;assert(Geometry((void*)1)==second&&DALib::R.Lod==2);
 DALib::E.Fail=true;assert(!Geometry((void*)1)&&DALib::R.Lod==2);DALib::E.Fail=false;
 puts("PASS: hidden LOD restored after both successful and failed queries");
 part->~Borrowed();assert(VirtualProtect(page,4096,PAGE_NOACCESS,&old));ClearMeshes();ClearMeshes();
 assert(Created==Destroyed&&Releases==0);VirtualFree(page,0,MEM_RELEASE);
 puts("PASS: repeated teardown releases GPU copies once and engine facets never");
}
'''


def run(source,tag,negative=False):
    code=source[source.index('struct Mesh {'):source.index('bool Ready()')]
    code+=source[source.index('Mesh* Geometry('):source.index('void AddPart(')]
    if negative:code+='\nstd::map<const void*,unsigned long long> FrameLibraries;\n'
    cpp=OUT/f'lifetime_{tag}.cpp';cpp.write_text(PREFIX+code+MAIN)
    compiler,env=compiler_env();exe=OUT/f'lifetime_{tag}.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/O2','/std:c++17',
        '/I'+str(ROOT/'src/freelancer/Client'),str(cpp),'/Fo'+str(OUT/f'lifetime_{tag}.obj'),
        '/Fe'+str(exe)],cwd=ROOT,env=env,check=True)
    result=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
    print(result.stdout,end='')
    if negative:
        assert result.returncode in (0xc0000005,-1073741819),f'Expected freed-facet access violation, got {result.returncode}'
        print('PASS: original implementation reproduces access violation after system unload')
    else:result.check_returncode()


if __name__=='__main__':
    old=OUT/'crash_20261105/cloak_visual_before.cpp'
    if old.exists():run(old.read_text(),'before',negative=True)
    run((ROOT/'src/freelancer/Client/cloak_visual.cpp').read_text(),'fixed')
