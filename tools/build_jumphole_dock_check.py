"""Generate a standalone C++ route regression from current DockBehavior production code.
Run from repository root; compile/run src/obj/jumphole_dock_check.cpp with MSVC.
Math/data validation and affected route/state branches are extracted, not reimplemented.
Move/Face/clearance/physics services are deterministic mocks. The unchanged legacy
state-2 lateral-jitter body is instrumented by a counter, preserving its production
branch condition. This validates routing decisions, not a live AI flight or ABI.
"""
from pathlib import Path
import re
s=Path('src/Common/common_dockbehavior.cpp').read_text(encoding='utf-8-sig')
s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
def block(t,mark):
 a=t.index(mark);b=t.index('{',a);d=1;e=b+1
 while d:d+=(t[e]=='{')-(t[e]=='}');e+=1
 return t[a:e]
def body(mark):
 f=block(s,mark);return f[f.index('{')+1:-1]
def branch(t,mark,with_else=False):
 a=t.index(mark);part=block(t[a:],mark)
 if with_else:
  rest=t[a+len(part):];m=re.match(r'\s*else\s*{',rest)
  assert m
  part+=block(rest,'else')
 return part
predicate=block(s,'static bool FrontJumpHoleApproach(')
refresh=block(s,'void DockBehavior::RefreshApproachState(')
can=block(s,'bool DockBehavior::CheckCanProceed(')
enter=body('void DockBehavior::EnterState(')
update=body('int DockBehavior::UpdateApproachTail(')
recompute=body('void DockBehavior::RecomputeApproach(')
init=branch(recompute,'else if ((StateFlags32c & 0x40)').removeprefix('else ')
route=branch(enter,'if ((StateFlags32c & 0xc0) != 0 || FrontHole)',True)
submit=branch(body('void DockBehavior::SubmitGotoDirective('),'if ((StateFlags32c & 0xc0) != 0 || FrontHole)',True)
case2=enter[enter.index('case 2:'):enter.index('case 4:')]
jitter_if=case2[case2.index('if ('):case2.index('\n        {',case2.index('if ('))]
case2tail=case2[case2.index('SubObjectA.SetMode(0);'):]
case6=enter[enter.index('case 6:'):enter.index('case 7:')]
case8=enter[enter.index('case 8:'):enter.index('case 9:')]
case9=enter[enter.index('case 9:'):enter.index('static_cast<IBehaviorManager*>(Field20)->lock_maneuvers(true);')]+ 'break; }'
u2=update[update.index('case 2:'):update.index('case 3:')]
u6=update[update.index('case 6:'):update.index('case 7:')]
u8=update[update.index('case 8:'):update.index('case 9:')]
u1=block(update,'if (ModeState320 == 1)')
clear=body('bool DockBehavior::OnResult(')
a=clear.index('if (StateFlags32c & 0x840)');clear=clear[a:clear.index('return false;',a)]
prefix=r'''
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <initializer_list>
#include <cstdio>
#include <cstring>
#include <limits>
#include <cassert>
struct Vector{float x=0,y=0,z=0;Vector operator-(Vector b)const{return{x-b.x,y-b.y,z-b.z};}};
struct Matrix{float E[3][3]={{-1,0,0},{0,1,0},{0,0,-1}};};struct Transform{Matrix Rotation;Vector Translation;};
struct Watchable{char dummy;};using TERMINAL_TYPE=int;
static unsigned CreateID(const char*n){return strcmp(n,"rh_biz_jh_to_sig8")==0?12345:54321;}
struct IObjRW{char pad[8]={};Watchable watch;unsigned id=12345;int result=0;Transform mount,near,far;
 unsigned get_id()const{return id;}bool is_player()const{return false;}
 int get_dock_hardpoints(int i,TERMINAL_TYPE*t,Transform*a,Transform*b,Transform*c,float*r)const{assert(i==0);if(result)return result;*a=mount;*b=near;*c=far;if(t)*t=1;if(r)*r=150;return 0;}
};using IObjInspect=IObjRW;
static IObjRW* ObjRwFromWatchable(Watchable*w){return w?reinterpret_cast<IObjRW*>(reinterpret_cast<char*>(w)-8):nullptr;}
static IObjInspect const* ObjInspectOf(void const*p){return static_cast<IObjInspect const*>(p);}
struct Watcher{Watchable*p=nullptr;Watchable const* target()const{return p;}};
struct Self{Vector CachedPos;};struct SystemManager{Self SelfTarget;};static bool InRange=true;
static bool IsWithinInterceptRangeOfIface(Self*,IObjRW*,float){return InRange;}
static void VecNormalize3(Vector const*v,Vector*out){float n=sqrtf(v->x*v->x+v->y*v->y+v->z*v->z);*out={v->x/n,v->y/n,v->z/n};}
static double ClampedDot3(Vector a,Vector b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static float BitsToFloat(unsigned x){float f;memcpy(&f,&x,4);return f;}
struct Idea{Vector position,direction,Offset4c;int mode=-1,field44=-1,updates=0,result=0,commits=0;float range=0,angle=0;
 void SetPosition(Vector v){position=v;}void SetDirection(Vector v){direction=v;}void SetMode(int m){mode=m;}void SetRange3c(float r){range=r;}void SetField44(int f){field44=f;}void SetAngleWeight8c(float f){angle=f;}void SetBasis(Matrix const&){}void SetField59(int){}void SetAngle38(float){}void SetField158(int){}int Update(float){updates++;return result;}void Commit(){commits++;}float GetFaceAngle(){return 0;}};
struct Behavior{char pad[28]={};float dt=0;int result=2;int Slot7(){return result;}};
struct Goto{void*NavPilotPtr=nullptr;};struct Op{int Field_0C=0,Field_1C=0;Vector Destination;};
struct DockBehavior{unsigned StateFlags32c=0x800;Watcher Watcher324;int Field43c=-1,SubStateValue440=0,CombatFlag344=0,ModeState320=0,UpdateResult10=1,Flag39a=0,ApproachClearedFlag334=0,splines=0,jitters=0;float Field408=0,MaxApproachSpeed46c=1000;static constexpr double kEnterState9RadiusScale=.6;Vector SavedPosition3fc,DestPoint3cc,InterceptPoint39c,Facing38c;Matrix Orient40c,OrientMatrix3d8,Orient3a8;void*Field24=nullptr;void*ThreatSourcePtr14=nullptr;void*TargetShipPtr388=nullptr;Idea SubObjectA,SubObjectB,SubObjectC;Goto GotoDirective;
 void NavHelperRefreshLeadPoint(){}void SetCruiseLock(int,int){}void BuildFinalApproachSpline(){splines++;}void*RawAt(int){return &SubObjectA.Offset4c;}void EnterState(int s){ModeState320=s;}float GetTickDelta(){return .02f;}
 void RefreshApproachState();bool CheckCanProceed();void Init();Op Route();Op Submit();void EnterActual(int);int UpdateActual();int Start();void Clearance();};
'''
out=[prefix,predicate,refresh,can,'void DockBehavior::Init(){Field43c=-1;'+init+'}',
 'Op DockBehavior::Route(){Op Op;bool const FrontHole=FrontJumpHoleApproach(*this);'+route+'return Op;}',
 'Op DockBehavior::Submit(){Op Op;bool const FrontHole=FrontJumpHoleApproach(*this);'+submit+'return Op;}',
 'void DockBehavior::EnterActual(int NewState){ModeState320=NewState;switch(NewState){case 2:{'+jitter_if+' {jitters++;InterceptPoint39c={999,999,999};}\n'+case2tail+case6+case8+case9+'}}',
 'int DockBehavior::UpdateActual(){float DeltaTime=.02f;switch(ModeState320){'+u2+u6+u8+'}return UpdateResult10;}',
 'int DockBehavior::Start(){float DeltaTime=.02f;'+u1+'return UpdateResult10;}',
 'void DockBehavior::Clearance(){RefreshApproachState();'+clear+'}']
out.append(r'''
static bool equal(Vector a,Vector b){return fabs(a.x-b.x)<.0001f&&fabs(a.y-b.y)<.0001f&&fabs(a.z-b.z)<.0001f;}
static void require(bool b,const char*n){printf("%s %s\n",b?"PASS":"FAIL",n);if(!b)std::abort();}
int main(){
 IObjRW obj;obj.mount.Translation={.146f,-.438f,-28.1581f};obj.near.Translation={.146f,-.438f,-168.776f};obj.far.Translation={.146f,-.438f,-330.6447f};
 SystemManager sys;Behavior pilot;DockBehavior d;d.Watcher324.p=&obj.watch;d.Field24=&sys;d.ThreatSourcePtr14=&obj;d.GotoDirective.NavPilotPtr=&pilot;
 require(FrontJumpHoleApproach(d),"selected valid jumphole opts in");
 unsigned original=d.StateFlags32c;obj.id=54321;require(!FrontJumpHoleApproach(d),"reverse and other hole IDs retain retail routing");obj.id=12345;
 for(int error:{-4,-2,-5}){obj.result=error;require(!FrontJumpHoleApproach(d),"missing/incomplete hardpoints fall back");}obj.result=0;
 auto far=obj.far;obj.far=obj.near;require(!FrontJumpHoleApproach(d),"collapsed hardpoint fallback");obj.far.Translation={0,0,100};require(!FrontJumpHoleApproach(d),"reversed approach fallback");obj.far=far;obj.far.Translation.x=std::numeric_limits<float>::quiet_NaN();require(!FrontJumpHoleApproach(d),"nonfinite hardpoint fallback");obj.far=far;
 d.Watcher324.p=nullptr;require(!FrontJumpHoleApproach(d),"missing target fallback");d.Watcher324.p=&obj.watch;
 d.Init();require(d.Field43c==0&&equal(d.InterceptPoint39c,obj.far.Translation)&&equal(d.DestPoint3cc,obj.near.Translation),"initialization loads authored Point02 and Point01");require(fabs(d.Facing38c.z-1)<.0001f,"facing follows authored front toward mount");
 require(d.Route().Field_0C==1&&equal(d.Route().Destination,obj.far.Translation)&&equal(d.Submit().Destination,obj.far.Translation),"both far-route builders target authored Point02");
 d.ModeState320=1;d.Start();require(d.ModeState320==2,"far route completion enters state2");d.EnterActual(2);require(d.jitters==0&&equal(d.SubObjectA.position,obj.far.Translation),"state2 retains authored Point02 without gate lateral jitter");
 sys.SelfTarget.CachedPos={0,0,-330};d.SubObjectA.result=0;d.ModeState320=2;d.UpdateActual();require(d.ModeState320==2,"selected hole must reach Point02 before advancing even in front halfspace");d.SubObjectA.result=1;d.UpdateActual();require(d.ModeState320==3,"Point02 arrival enables clearance request state3");d.SubObjectA.updates=d.SubObjectB.updates=0;
 d.ModeState320=3;require(d.CheckCanProceed(),"front halfspace permits clearance");sys.SelfTarget.CachedPos={0,0,20};require(!d.CheckCanProceed(),"backside cannot obtain front clearance");InRange=false;sys.SelfTarget.CachedPos={0,0,-330};require(!d.CheckCanProceed(),"range check is retained");InRange=true;
 d.Clearance();require(d.ModeState320==6,"clearance uses original gate/hole transition to6");d.EnterActual(6);require(equal(d.SubObjectA.position,obj.near.Translation)&&d.SubObjectA.field44==2&&d.SubObjectA.range==10&&d.MaxApproachSpeed46c==10,"state6 initializes actual move and face ideas");
 d.SubObjectA.result=0;d.SubObjectB.result=0;d.UpdateActual();require(d.ModeState320==6&&d.SubObjectA.updates==1&&d.SubObjectB.updates==1,"selected hole does not shortcut to9 while unaligned");d.SubObjectB.result=1;d.UpdateActual();require(d.ModeState320==8,"aligned selected hole enters spline state8");d.EnterActual(8);require(d.splines==1,"state8 builds final approach spline");d.SubObjectC.result=1;d.UpdateActual();require(d.ModeState320==9,"completed spline enters9");d.EnterActual(9);require(equal(d.SubObjectB.direction,d.Facing38c),"final movement maintains authored gate facing");require(d.StateFlags32c==original,"physical jump-hole type is never mutated");
 obj.id=54321;d.ModeState320=6;d.SubObjectA.updates=0;d.UpdateActual();require(d.ModeState320==9&&d.SubObjectA.updates==0,"other/reverse jumpholes preserve immediate retail6-to9");
 for(unsigned type:{0x40u,0x80u}){d.StateFlags32c=type;require(!FrontJumpHoleApproach(d),"gate and lane do not opt in");d.EnterActual(6);d.SubObjectB.result=1;d.UpdateActual();require(d.ModeState320==8,"ordinary gate/lane alignment path unchanged");require(equal(d.Route().Destination,d.DestPoint3cc),"ordinary gate/lane far destination stays Point01");}
 d.StateFlags32c=0x800;obj.id=12345;obj.result=-2;d.ModeState320=6;d.UpdateActual();require(d.ModeState320==9,"invalid hardpoint selected hole uses retail shortcut");
 puts("PASS extracted production branches with mocked Move/Face; no live AI/physics simulation claimed");
}
''')
Path('src/obj/jumphole_dock_check.cpp').write_text('\n'.join(out))
print('Generated src/obj/jumphole_dock_check.cpp from current production functions/branches')
