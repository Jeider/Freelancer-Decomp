"""Compile the real draw scope with tiny camera/pipeline fixtures; never starts the game."""
from pathlib import Path
import os
import subprocess

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/dynamic_quality/check'
OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'src/Deformable2/Deformable2.cpp').read_text()
state=source[source.index('struct FCharacterPartQuality'):source.index('\nnamespace',source.index('struct FCharacterPartQuality'))]
prefix=r'''
#define NOMINMAX
#include <cassert>
#include <cstdio>
#include <limits>
#include <vector>
#include <map>
#include "character_quality.h"
struct ICamera {
 float Depth=10,Scale=540,Near=.1f; int Viewport[4]={0,0,1919,1079};bool ProjectOK=true;
 int Project(float*x,float*y,float*z,float*){*x=*y=0;*z=Depth;return ProjectOK;}
 int* GetViewport(){return Viewport;} float GetZNear(){return Near;}
 double GetYScaleOverNear(){return Scale/Near;}
};
struct FDeformPart { int MeshCount=4,LodIndex=0,Changes=0;float Radius=1; };
struct FDeformInstance { int PartCount=1;FDeformPart* PartArray; };
struct IRPCharacterQuality {
 unsigned Pass=1;float Strength=1;unsigned CharacterQualityPass(){return Pass;}
 float SetCharacterQuality(float value){float old=Strength;Strength=value;return old;}
};
int Level=2;float CharacterRenderValue(const char*,float){return float(Level);}
bool SelectPartLod(FDeformPart* p,int i){bool changed=p->LodIndex!=i;p->LodIndex=i;p->Changes+=changed;return changed;}
void MarkPartSkinDirty(FDeformPart*){}
unsigned char PartBoundSphere(FDeformPart*p,float*r,float*c){*r=p->Radius;c[0]=c[1]=c[2]=0;return 1;}
'''
tests=r'''
int main(){
 using namespace CharacterQuality;
 float p=ScreenSize(1,10,.1f,540,1080);
 assert(p>108 && p<110);assert(ScreenSize(1,10,.1f,1080,2160)==p);
 assert(ScreenSize(1,10,.1f,1080,1080)==2*p); // zoom, not world metres
 assert(ScreenSize(1,1,.1f,540,1080)<0);
 assert(ScreenSize(1,std::numeric_limits<float>::quiet_NaN(),.1f,540,1080)<0);
 assert(Tier(180,2)==1 && Tier(180,3)==0);
 assert(Tier(50,2)==2 && Tier(50,3)==1);
 assert(Strength(150,2)==.5f && Strength(150,3)==1);
 assert(Strength(44,3)==0 && Strength(400,0)==0);
 State s;assert(Update(s,250,2,true)==0);
 for(float v:{239.f,241.f,220.f,230.f,205.f})assert(Update(s,v,2,false)==0);
 assert(Update(s,200,2,false)==1);assert(Update(s,250,2,false)==1);
 assert(Update(s,280,2,false)==0);assert(Update(s,10,2,false)==3);
 assert(Update(s,400,2,false)==0);assert(Update(s,-1,2,false)==0 && !s.Valid);
 int extra[]={-1,0,1,2,3},native[]={0,1,2,3},skipped[]={1,2,3},missing[]={-1,1,2};
 assert(Pick(0,5,extra,1)==1 && Pick(0,5,extra,2)==2);
 assert(Pick(0,4,native,1)==0 && Pick(0,3,skipped,2)==0);
 assert(Pick(0,3,missing,1)==1);assert(Pick(0,1,native,3)==0);
 assert(Pick(-1,5,extra,3)==-1 && Pick(5,5,extra,3)==5);
 assert(Pick(4,5,extra,1)==4);
 IRPCharacterQuality pipeline;G_QualityPipeline=&pipeline;
 FDeformPart part;FDeformInstance instance{1,&part};ICamera a,b;
 G_CharacterQuality[&instance].Parts.resize(1);
 for(int i=0;i<4;++i)RecordCharacterLod(&instance,0,i,true,i);
 auto& q=G_CharacterQuality.find(&instance)->second;
 assert(QualityRequested(&instance,0,0)==0);
 {FCharacterQualityScope scope(&instance,&a);assert(part.LodIndex==1 && pipeline.Strength==0);}
 assert(pipeline.Strength==1);int changes=part.Changes;
 for(int i=0;i<50;++i){
  pipeline.Pass=2;SelectPartLod(&part,QualityRequested(&instance,0,0));
  {FCharacterQualityScope shadow(&instance,&b);assert(pipeline.Strength==1 && part.LodIndex==1);}
  pipeline.Pass=1;SelectPartLod(&part,QualityRequested(&instance,0,0));
  {FCharacterQualityScope color(&instance,&a);assert(part.LodIndex==1);}
 }
 assert(part.Changes==changes); // no colour/shadow/highest LOD rebuild loop
 b.Depth=2;{FCharacterQualityScope scope(&instance,&b);assert(part.LodIndex==0 && pipeline.Strength==1);}
 {FCharacterQualityScope scope(&instance,&a);assert(part.LodIndex==1);}
 a.ProjectOK=false;{FCharacterQualityScope scope(&instance,&a);assert(part.LodIndex==0 && pipeline.Strength==1);}
 a.ProjectOK=true;pipeline.Pass=0;
 {FCharacterQualityScope ui(&instance,&a);assert(part.LodIndex==0 && pipeline.Strength==1);}
 pipeline.Pass=1;Level=0;{FCharacterQualityScope off(&instance,&a);assert(pipeline.Strength==0);}
 Level=3;a.Depth=5;{FCharacterQualityScope high(&instance,&a);assert(pipeline.Strength==1);}
 pipeline.Strength=.6f;{FCharacterQualityScope nested(&instance,&b);assert(pipeline.Strength==1);}assert(pipeline.Strength==.6f);
 puts("PASS dynamic quality: projection/zoom/resolution, hysteresis, physical-loaded mappings, missing LOD, production draw scope, camera/UI/shadow isolation, stable buffers");
}
'''
(OUT/'check.cpp').write_text(prefix+state+'\n#include "CharacterQuality.inl"\n'+tests)
cmd=OUT/'build.cmd'
cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\nif errorlevel 1 exit /b 1\ncl /nologo /EHsc /std:c++17 /O2 /I"'+str(ROOT/'src/include')+'" /I"'+str(ROOT/'src/Deformable2')+'" check.cpp /Fecheck.exe\n')
env=dict(os.environ,TEMP=str(OUT),TMP=str(OUT))
subprocess.run(['cmd','/c',str(cmd)],cwd=OUT,env=env,check=True)
r=subprocess.run([str(OUT/'check.exe')],cwd=OUT,capture_output=True,text=True)
(OUT/'result.txt').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr);r.check_returncode()
