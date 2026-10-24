#include "../src/freelancer/Client/ship_warp_state.h"
#include <cstdio>
#include <cstdlib>
#include <limits>

static void Check(bool Value,char const* Message)
{
    if(!Value){std::fprintf(stderr,"FAIL: %s\n",Message);std::exit(1);}
}
static bool Near(float A,float B,float E=.0001f){return std::fabs(A-B)<E;}
static float Length(FShipWarpPoint A,FShipWarpPoint B)
{auto D=ShipWarpMesh::Sub(A,B);return std::sqrt(ShipWarpMesh::Dot(D,D));}
int main()
{
    for(auto N:{"HpContrail01","hPcOnTrAiL99","HpContail07","hpcontail003","HpContrail0","HpContrail1000"})
        Check(ShipWarpTrailName(N),"numeric hardpoint name, spelling and case");
    for(auto N:{"","HpContrail","HpContail","HpContrailXX","HpContail01x","HpContrail-1","HpContrail 1","HpContrail1.0","OtherHpContrail01"})
        Check(!ShipWarpTrailName(N),"invalid hardpoint suffix rejected");
    Check(!ShipWarpTrailName(nullptr),"null name rejected");
    unsigned Accepted=0;for(auto N:{"HpContail01","HpContrail07","HpContrail42","HpGun01"})Accepted+=ShipWarpTrailName(N);
    Check(Accepted==3,"gaps do not require contiguous indices");
    puts("PASS hardpoint numeric suffixes, both spellings, mixed case, gaps and invalid names");

    float const NaN=std::numeric_limits<float>::quiet_NaN();
    FShipWarpClock C;C.Tick(.125f);Check(Near(C.Intensity,.5f),"entry midpoint");
    auto Saved=C;C.Tick(0);C.Tick(-1);C.Tick(NaN);
    Check(C.Time==Saved.Time&&C.Age==Saved.Age&&C.Intensity==Saved.Intensity,"pause and invalid dt preserve clock");
    C.Tick(.125f);Check(C.Intensity==1,"entry completes");C.Stop();C.Tick(.225f);
    Check(Near(C.Intensity,.5f),"exit midpoint");float ExitAge=C.ExitAge;C.Stop();Check(C.ExitAge==ExitAge,"repeated stop does not restart fade");
    C.Resume();Check(Near(C.Intensity,.5f),"resume no brightness jump");C.Tick(.125f);Check(Near(C.Intensity,.75f),"resume blends from current intensity");
    C.Tick(.125f);C.Stop();C.Tick(.5f);Check(C.Intensity==0,"exit reaches zero");C.Resume();C.Tick(.25f);Check(C.Intensity==1,"restart after fully faded");
    C.Time=95.75f;C.Tick(.5f);Check(Near(C.Time,.25f),"96 second clock wraps");
    puts("PASS clock pause, entry, repeated stop, fade, continuous restart and time wrap");

    FShipWarpHistory H;FShipWarpPoint Out[33];
    // A right angle path: old samples must survive as a bend, not a velocity ray.
    H.Tick({0,0,0},.02f);H.Tick({10,0,0},.02f);H.Tick({10,10,0},.02f);
    unsigned N=H.Path({10,10,0},{0,0,1},0,100,Out);
    Check(N==3&&Near(Out[1].X,10)&&Near(Out[1].Y,0)&&Near(Out[2].X,0),"actual curved history preserved");
    N=H.Path({10,10,0},{0,0,1},0,15,Out);
    float Arc=0;for(unsigned I=1;I<N;++I)Arc+=Length(Out[I],Out[I-1]);
    Check(N==3&&Near(Arc,15)&&Near(Out[2].X,5),"max length clips on curved segment");
    auto Before=H;H.Tick({999,999,999},0);H.Tick({NaN,0,0},.1f);H.Tick({0,0,0},NaN);
    Check(H.Count==Before.Count&&H.SinceSample==Before.SinceSample,"paused history preserves count");
    for(unsigned I=0;I<H.Count;++I)Check(H.Samples[I].Age==Before.Samples[I].Age&&Length(H.Samples[I].Pos,Before.Samples[I].Pos)==0,"paused history preserves samples");
    H.Tick({12,12,0},1.f);Check(H.Count==1&&H.Samples[0].Age==0,"expired history pruned");
    Check(H.Path({0,0,0},{0,0,1},0,0,Out)==0&&H.Path({0,0,0},{0,0,1},NaN,10,Out)==0&&H.Path({0,0,0},{0,0,1},0,10,nullptr)==0,"invalid paths rejected");
    H.Clear();for(unsigned I=0;I<1000;++I){H.Tick({float(I),0,0},1.f/90);Check(H.Count<=64,"fixed history capacity");}
    Check(H.Count==64&&H.Samples[0].Pos.X==999,"capacity keeps newest samples");
    N=H.Path({999,0,0},{0,0,1},0,10000,Out);Check(N<=33,"output path capacity");
    H.Clear();for(unsigned I=0;I<20;++I)H.Tick({0,0,0},.02f);
    Check(H.Path({0,0,0},{0,0,1},0,1000,Out)==1,"stationary path without jump wind has no fake length");
    N=H.Path({0,0,0},{0,0,1},100,1000,Out);
    Check(N>2&&Out[N-1].Z>30,"jump wind extends stationary ship tail");
    for(unsigned I=1;I<N;++I)Check(Out[I].Z>Out[I-1].Z&&Out[I].X==0&&Out[I].Y==0,"jump wind follows explicit ship back axis");
    puts("PASS curved path, exact arc clipping, pause, expiration, capacities and jump wind");
}
