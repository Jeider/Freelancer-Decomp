"""Exercise production pose ownership before/after the room animation update."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_courier'))
from check_transfer_docking import block
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
source=(ROOT/'src/freelancer/Client/base_walk.cpp').read_text()
code=r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <cmath>
float world[3]={1,2,3};int writes=0;
float GEmoteFloorY=2,GEmoteSavedFloorHeight=0;bool GEmoteRestoreFloorHeight=false;
struct Player {int bPoseDirty=0;void* GetEngineInstance(){return this;}void RemoveMotionHandle(int){}}player;
struct Engine {float const* GetInstancePosition(void*){return world;}
 void SetInstancePosition(void*,float* p){++writes;memcpy(world,p,sizeof(world));}
 void UpdateInstance(void*,int,void*){}}engine;
struct Deform {float height=-10;void SetPosePos(void*,float*){}void SetPoseOri(void*,float*){}void DestroyHandle(void*,int){}
 void GetOffset(void*,float* p){*p=height;}void SetHeight(void*,float h){height=h;}}deform;
struct Anim {bool named=true;float root=1.25f;unsigned GetNamedDurationOut(void*,char const*,float* out){*out=root;return named;}}anim;
struct Db {void ReleaseScript(unsigned){}}db;Db* GetCharacterInfoDb(){return &db;}
namespace DALib {Engine* Engine=&engine;Deform* Deform=&deform;Anim* Anim=&anim;}
struct Pose {float Position[3]={1,2,3};void CharacterOrientation(float*){}void CameraTransform(float*){}};
struct {int MotionKind=0,MotionHandle=-1;unsigned MotionId=0;Player* Player=&player;void* Room=nullptr;void* Deformable=&deform;struct Pose Pose;}G_BaseWalk;
bool WorldAvailable(void*,Player*){return true;}void SuspendPlayer(bool){}void BasePresenceApply(){}
struct Camera {void SetTransform(float*){}}camera;
Camera* GetRoomRuntimeRoomCamera(void*){return &camera;}
'''+block(source,'void ApplyPose()')+'\n'+block(source,'void PrepareEmoteHeight(')+'\n'+block(source,'void StopMotion()')+'\n'+block(source,'void BaseWalkAfterWorldUpdate()')+r'''
int main(){
 ApplyPose();assert(writes==1);
 PrepareEmoteHeight(nullptr,"clip");assert(deform.height==.75f&&GEmoteSavedFloorHeight==-10);
 G_BaseWalk.MotionKind=5;world[0]=4;world[1]=anim.root+deform.height;world[2]=7;
 ApplyPose();assert(writes==1&&world[0]==4);
 BaseWalkAfterWorldUpdate();assert(G_BaseWalk.Pose.Position[0]==4&&G_BaseWalk.Pose.Position[2]==7&&world[1]==2);
 world[0]=5;world[1]=anim.root+deform.height+.5f;BaseWalkAfterWorldUpdate();assert(G_BaseWalk.Pose.Position[0]==5&&world[1]==2.5f);
 world[1]=anim.root+deform.height;BaseWalkAfterWorldUpdate();assert(world[1]==2);
 StopMotion();ApplyPose();assert(world[0]==5&&world[2]==7&&world[1]==2);
 assert(deform.height==-10&&!GEmoteRestoreFloorHeight); // scene's original parameter restored
 G_BaseWalk.Pose.Position[1]+=1;ApplyPose();assert(world[1]==3); // manual lift after cancellation
 anim.named=false;PrepareEmoteHeight(nullptr,"no_root");assert(deform.height==-10&&!GEmoteRestoreFloorHeight);
 puts("PASS emote floor configured before playback, relative bobbing, cancellation restores scene parameter, missing root metadata leaves floor unchanged");
}
'''
out=ROOT/'out/base_presence/root_motion';out.mkdir(parents=True,exist_ok=True)
(out/'check.cpp').write_text(code)
compiler,env=compiler_env()
subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','check.cpp','/Fe:check.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True)
