"""Exercise the production DFM load loop with a small in-memory filesystem.

Checks bar/cutscene flags, native assets, optional-marker versions, fractions,
skinning limits, physical mesh cache keys and the eight-slot boundary.
"""
from pathlib import Path
import os
import subprocess

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/lods/check_loader';OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'src/Deformable2/Deformable2.cpp').read_text()
a=source.index('                float Fractions[8];');b=source.index('                    if (!Instance->PartArray[PartIndex].BindMeshes',a)
loop=source[a:b]+'\n}\n'
prefix=r'''
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#include "character_geometry_lod.h"
#define FDUMP(...) ((void)0)
struct FFileSystemDesc { const char* Name; unsigned long Field30; };
using AGGDESC=FFileSystemDesc;
void FillFileDesc(FFileSystemDesc* d,const char* s){d->Name=s;}
struct IFileSystem {
 int Count=6,Version=0,Quality=0,Cursor=0,Mesh=-1;std::vector<float> Values{1,.8f,.6f,.4f,.2f,.1f};
 int OpenNode(const char*){return 1;}
 int OpenByDesc(FFileSystemDesc* d){return !strcmp(d->Name,"Fractions")?1:!strcmp(d->Name,"Enhanced geometry")?(Version?2:-1):!strcmp(d->Name,"Geometry quality")?(Quality?3:-1):-1;}
 unsigned GetSize(unsigned long,int){return unsigned(Values.size()*4);}
 int Read(unsigned long h,void* out,unsigned len,unsigned long* got,int){
  if(h==1){memcpy(out,Values.data(),len);*got=len;}else{memcpy(out,h==2?&Version:&Quality,4);*got=4;}return 1;}
 void CloseFile(unsigned long){}
 int CreateInstance(AGGDESC* d,void** out){auto* fs=new IFileSystem;fs->Mesh=atoi(d->Name+4);*out=fs;return 0;}
 void Release(){delete this;}
};
int FsFindFirst(IFileSystem* fs,const char*,WIN32_FIND_DATAA* d){fs->Cursor=0;strcpy_s(d->cFileName,"Mesh0");return 1;}
int FsFindNext(IFileSystem* fs,int,WIN32_FIND_DATAA* d){if(++fs->Cursor>=fs->Count)return 0;sprintf_s(d->cFileName,"Mesh%d",fs->Cursor);return 1;}
void FsFindClose(IFileSystem*,int){}
struct FDeformMesh {};
struct Slot { float Fraction=0; };
struct Desc {int LodCount=16;Slot Lods[16];int Field08=0;unsigned Flags=0,LodLimit=2;};
std::vector<int> loaded,full;bool enabled=true;FDeformMesh dummy;
float CharacterRenderValue(const char*,float){return enabled?1.f:0.f;}
void RecordCharacterLod(void*,int,int,bool,unsigned){}
FDeformMesh* LoadDeformMesh(void*,IFileSystem* fs,char* name,unsigned char flag){loaded.push_back(fs->Mesh);full.push_back(flag);assert(name[strlen(name)-1]=='0'+fs->Mesh);return &dummy;}
void Run(Desc* Entry,IFileSystem* RootFs){
 char BaseName[40]="hand",*Dot=BaseName+4;void* Holder=nullptr;void* Instance=nullptr;int PartIndex=0;
'''
tests=r'''
}
void Check(int version,bool on,unsigned flags,int cap,std::vector<int> expected,int quality=0){
 IFileSystem fs;if(version){fs.Version=version;fs.Count=7;fs.Values.insert(fs.Values.begin(),1.f);}
 fs.Quality=quality;Desc entry;entry.Flags=flags;entry.LodCount=cap;enabled=on;loaded.clear();full.clear();Run(&entry,&fs);
 assert(loaded==expected);assert(entry.LodCount==int(expected.size()));
 assert(entry.Field08==int(version==1 && !expected.empty() && expected.front()==0));
 for(size_t i=0;i<loaded.size();++i){assert(entry.Lods[i].Fraction==fs.Values[loaded[i]]);
  int native=version==1 && loaded[i]?loaded[i]-1:loaded[i];assert(full[i]==int(native<2));}
}
int main(){
 for(bool on:{false,true}){
  Check(0,on,0,16,{0,1,2,3,4,5});Check(0,on,2,16,{1,2,3,4,5});Check(0,on,1,1,{0});Check(0,on,3,1,{});
  Check(1,on,2,16,{2,3,4,5,6});Check(1,on,3,1,{2});
  Check(2,on,0,16,{0,1,2,3,4,5,6}); // unknown extension is ignored
  Check(0,on,2,16,{1,2,3,4,5},1);Check(0,on,3,1,{1},1);
  Check(0,on,0,16,{0,1,2,3,4,5},2); // unknown native-pair version
  Check(1,on,2,16,{2,3,4,5,6},1); // inserted level wins if both markers exist
 }
 Check(0,true,0,16,{0,1,2,3,4,5},1);Check(0,false,0,16,{0,1,2,3,4,5},1);
 Check(0,true,1,1,{0},1);Check(0,false,1,1,{0},1);Check(0,false,0,2,{0,1},1);
 Check(1,true,0,16,{0,1,2,3,4,5,6});Check(1,false,0,16,{1,2,3,4,5,6});
 Check(1,true,1,1,{0});Check(1,false,1,1,{1});
 IFileSystem fs;fs.Version=1;fs.Count=1;fs.Values={1};Desc e;enabled=false;loaded.clear();full.clear();Run(&e,&fs);assert(loaded==std::vector<int>{0});
 fs.Count=12;fs.Values.assign(12,1);fs.Version=0;e=Desc{};loaded.clear();full.clear();Run(&e,&fs);assert(loaded.size()==8);
 fs.Count=1;fs.Values={1};fs.Quality=1;e=Desc{};loaded.clear();full.clear();Run(&e,&fs);assert(loaded==std::vector<int>{0});
 assert(CharacterGeometryLod::NearDistance(10.f)==5.f);
 puts("PASS production loader: bar/cutscene, native opt-out, low-character option, fractions, cache keys, skinning limits, eight LODs");
}
'''
(OUT/'check.cpp').write_text(prefix+loop+tests)
cmd=OUT/'build.cmd';cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\nif errorlevel 1 exit /b 1\ncl /nologo /EHsc /std:c++17 /O2 /D_CRT_SECURE_NO_WARNINGS /I"'+str(ROOT/'src/include')+'" "'+str(OUT/'check.cpp')+'" /Fo"'+str(OUT/'check.obj')+'" /Fe"'+str(OUT/'check.exe')+'"\n')
subprocess.run(['cmd','/c',str(cmd)],cwd=OUT,check=True)
result=subprocess.run([str(OUT/'check.exe')],cwd=OUT,capture_output=True,text=True)
(OUT/'result.txt').write_text(result.stdout+result.stderr);print(result.stdout+result.stderr);result.check_returncode()
