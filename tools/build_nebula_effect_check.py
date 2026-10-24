"""Extract the production CPU transmission body and exercise it with geometric zones."""
from pathlib import Path

s = Path('src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
body = s[s.index('float NebulaVolume::EffectVisibility('):s.index('float NebulaVolume::SegmentNebulaLength(')]
prefix = r'''
#include <cmath>
#include <vector>
#include <cassert>
#include <cstdio>
#include <limits>
struct Vector { float x=0,y=0,z=0; };
struct Zone {
 Vector Centre; float Radius=1000;
 Vector const& GetPos() const {return Centre;}
 float GetRadius() const {return Radius;}
 double GetImmersion(Vector p) const {
  double x=p.x-Centre.x,y=p.y-Centre.y,z=p.z-Centre.z;
  return x*x+y*y+z*z<Radius*Radius?1:0;
 }
};
float Clamp(float x,float a,float b){return x<a?a:x>b?b:x;}
struct Exclusion { Zone* ZonePtr=nullptr;float FogFar=10000;};
struct Manager {std::vector<Exclusion*> Items;};
struct FNebulaVolumeSettings {float Enabled=1,ExclusionDensityScale=1;};
struct FMediumParams {float FogNear,FogDistance,HazeSigma,CloudSigma;};
struct FNebulaEffect { ::Zone* Zone=nullptr;int FlagLoaded=1;Manager* ExclusionMgr=nullptr;
 float Near=0,Distance=1000,Sigma=.001f,Cloud=0;FNebulaVolumeSettings Settings;};
struct Entry {FNebulaEffect* Nebula;void* RingOwner=nullptr;};
std::vector<Entry> GNebulae;bool GbProgramFailed=false;
namespace RenderEx {bool IsAvailable(){return true;}}
FNebulaVolumeSettings SettingsFor(FNebulaEffect const* n){return n->Settings;}
void ComputeMedium(FNebulaEffect const*n,FNebulaVolumeSettings const&,FMediumParams*m){*m={n->Near,n->Distance,n->Sigma,n->Cloud};}
float ExclusionInsideScale(Exclusion const* e,FMediumParams const&m,FNebulaVolumeSettings const&s){
 return Clamp((e->FogFar>m.FogNear?Clamp(m.FogDistance/(e->FogFar-m.FogNear),0,1):1)*s.ExclusionDensityScale,0,1);
}
struct FNebulaVolumeExclusionAccess{
 static int Count(Manager const*m){return (int)m->Items.size();}
 static Exclusion const* At(Manager const*m,int i){return m->Items[i];}
};
namespace NebulaVolume {float EffectVisibility(float const*,float const*);}
'''
tests = r'''
int main(){
 Zone z;FNebulaEffect n;n.Zone=&z;GNebulae={{&n}};
 float a[3]={-2000,0,0},b[3]={0,0,0},c[3]={2000,0,0},front[3]={-1500,0,0};
 auto V=NebulaVolume::EffectVisibility;
 assert(V(a,front)==1);assert(fabs(V(a,b)-exp(-1.))<.0001);
 assert(fabs(V(a,c)-exp(-2.))<.0001);assert(fabs(V(b,a)-exp(-1.))<.0001);
 assert(V(a,a)==1);assert(V(nullptr,b)==0);
 float bad[3]={std::numeric_limits<float>::quiet_NaN(),0,0};assert(V(a,bad)==0);
 puts("PASS segment clipping: outside-inside, through-zone, reverse, foreground, zero length, invalid");
 n.Near=1000;assert(fabs(V(b,c)-exp(-.5))<.0001);n.Near=0;
 Zone e;e.Radius=2000;Exclusion ex{&e,10000};Manager mgr;mgr.Items={&ex};n.ExclusionMgr=&mgr;
 assert(fabs(V(a,c)-exp(-.2))<.0001);n.ExclusionMgr=nullptr;
 puts("PASS fog near ramp and exclusion fog distance thinning");
 FNebulaEffect other=n;GNebulae.push_back({&other});assert(fabs(V(a,b)-exp(-2.))<.0001);
 GNebulae[1].RingOwner=&other;assert(fabs(V(a,b)-exp(-1.))<.0001);
 GNebulae[1].RingOwner=nullptr;other.FlagLoaded=0;assert(fabs(V(a,b)-exp(-1.))<.0001);
 puts("PASS overlapping optical depths; unloaded and ring companions excluded");
 GNebulae.resize(1);n.Sigma=0;n.Cloud=.001f;assert(V(a,b)==0);
 n.Cloud=0;assert(V(a,b)==1);n.Settings.Enabled=0;assert(V(a,b)==0);
 n.Settings.Enabled=1;n.Sigma=.004f;float faded=V(a,b);assert(faded>0&&faded<exp(-4.));
 n.Sigma=.005f;assert(V(a,b)==0);
 puts("PASS cloud-only/legacy fallback, deliberately zero density, soft visibility cutoff");
}
'''
Path('src/obj/nebula_effect_check.cpp').write_text(prefix+body+tests, encoding='utf-8')
print('Generated src/obj/nebula_effect_check.cpp from production EffectVisibility body')
