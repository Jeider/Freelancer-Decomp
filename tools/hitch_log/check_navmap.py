"""Run production viewport calculation before the map's first Update, at varied aspect ratios."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2]
out=root/'src/obj/hitch_log'
out.mkdir(parents=True,exist_ok=True)
source=(root/'src/freelancer/Client/nn_navmap_update.cpp').read_text()
method=source[source.index('void NeuroNetNavMap::UpdateMapViewport()'):]
stub=r'''
#include <cassert>
#include <cmath>
#include <cstring>
#include <initializer_list>
#define FREELANCER_WIDESCREEN_SUPPORT
float shift=0,width=1920,height=1080;
struct FSpaceCamera{
 float ZNear=.1f,ZFar=100.f,HalfFovXDeg=45.f;int rect[4]={};
 void Project(float*x,float*y,float*z,float*p){*x=width*.5f+shift+p[0]*height;*y=height*.5f-p[1]*height;*z=p[2];}
}scene;
FSpaceCamera*Win3DGetCamera(){return &scene;}
FSpaceCamera*AsCamera(FSpaceCamera*c){return c;}
void SpaceCameraSetHalfFovX(FSpaceCamera*c,float f){c->HalfFovXDeg=f;}
void SpaceCameraSetViewportEx(FSpaceCamera*c,int*r,int){memcpy(c->rect,r,sizeof(c->rect));}
struct FWidescreenHudShiftScope{float saved;FWidescreenHudShiftScope(float s,bool):saved(shift){shift=s;}~FWidescreenHudShiftScope(){shift=saved;}};
float G_NavMapGlobal_67203c[3]={};
struct NeuroNetNavMap{
 float MapCorner0[3]={-.3f,.3f,0},MapCorner2[3]={.3f,-.3f,0};
 float ScreenRectMin[3]={},ScreenRectSize[3]={};FSpaceCamera Camera;
 void UpdateMapViewport();
};
'''
test=r'''
int main(){for(float w:{1440.f,1920.f,3440.f}){
 width=w;NeuroNetNavMap map;
 shift=(width-height*4/3)*.5f;float before=shift;
 map.UpdateMapViewport(); // first draw, before Update ever ran
 assert(shift==before);
 float center=map.ScreenRectMin[0]+map.ScreenRectSize[0]*.5f;
 assert(fabs(center-width*.5f)<=1.f);
 int first[4];memcpy(first,map.Camera.rect,sizeof(first));
 shift=0;map.UpdateMapViewport();assert(!memcmp(first,map.Camera.rect,sizeof(first)));
 assert(map.Camera.ZNear==scene.ZNear && map.Camera.ZFar==scene.ZFar);
}}
'''
(out/'navmap.cpp').write_text(stub+method+test)
cmd=out/'navmap.cmd'
cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" >nul\n'
 'if errorlevel 1 exit /b 1\ncl /nologo /EHsc /std:c++17 /W3 /WX src/obj/hitch_log/navmap.cpp /Fosrc/obj/hitch_log/navmap.obj /Fesrc/obj/hitch_log/navmap.exe\n')
subprocess.run(['cmd','/c',str(cmd)],cwd=root,check=True)
subprocess.run([str(out/'navmap.exe')],check=True)
print('PASS: first-draw map viewport stays centred at 4:3, 16:9 and ultrawide; next Update does not shift it')
