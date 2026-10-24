#pragma once
#include "ship_warp_mesh.h"

// A closed, soft exhaust volume remains visible from axial and side views.
// RGB encodes its world normal; alpha carries the nozzle's stable animation seed.
inline void BuildEngineHeatVolume(std::vector<FShipWarpVertex>& Out,FShipWarpPoint Origin,
    FShipWarpPoint Right,FShipWarpPoint Up,FShipWarpPoint Back,float Width,float Length,float Seed)
{
    using namespace ShipWarpMesh;
    if(!Finite(Origin)||!Finite(Right)||!Finite(Up)||!Finite(Back)||
        !std::isfinite(Width)||!std::isfinite(Length)||Width<=0||Length<=0)return;
    Right=Unit(Right);Up=Unit(Up,{0,1,0});Back=Unit(Back,{0,0,1});
    constexpr unsigned Rings=12,Sectors=16;
    auto V=[&](unsigned Ring,unsigned Sector) {
        float Theta=float(Ring)*3.141592654f/Rings,A=float(Sector%Sectors)*6.283185307f/Sectors;
        float S=std::sin(Theta),C=std::cos(Theta),U=(1-C)*.5f;
        auto Radial=Add(Mul(Right,std::cos(A)),Mul(Up,std::sin(A)));
        auto P=Add(Origin,Add(Mul(Back,Width*.15f+Length*U),Mul(Radial,Width*S)));
        auto N=Unit(Add(Mul(Radial,S/Width),Mul(Back,-C*2/Length)));
        auto Byte=[](float F){return unsigned((std::max)(0.f,(std::min)(1.f,F))*255+.5f);};
        unsigned Color=(Byte(Seed)<<24)|(Byte(N.X*.5f+.5f)<<16)|(Byte(N.Y*.5f+.5f)<<8)|Byte(N.Z*.5f+.5f);
        return FShipWarpVertex{{P.X,P.Y,P.Z},Color,{U,A}};
    };
    for(unsigned R=0;R<Rings;++R)for(unsigned S=0;S<Sectors;++S)
        Quad(Out,V(R,S),V(R,S+1),V(R+1,S),V(R+1,S+1));
}
