#pragma once
#include <cstdint>

// Small frame-to-frame selection history. Tokens are compared, never dereferenced.
// The remaining lifetime rejects pool-address reuse by a freshly spawned bullet.
struct RPWeaponGlintTracking
{
    struct Seed {std::uintptr_t Token=0;unsigned Owner=0;float Remaining=0;};
    Seed Previous[8]={},Next[8]={};
    std::uintptr_t Camera=0;
    void Clear() {for(auto& S:Previous) S={};for(auto& S:Next) S={};}
    void Begin(std::uintptr_t CameraToken)
    {
        if(Camera!=CameraToken) {Clear();Camera=CameraToken;}
        for(auto& S:Next) S={};
    }
    unsigned Priority(std::uintptr_t Token,unsigned Owner,float Remaining) const
    {
        for(unsigned I=0;I<8;++I)
            if(Previous[I].Token==Token && Previous[I].Owner==Owner &&
               Remaining<=Previous[I].Remaining+0.0001f) return I;
        return 8;
    }
    void Admit(unsigned Group,std::uintptr_t Token,unsigned Owner,float Remaining)
    {
        if(Group<8 && !Next[Group].Token) Next[Group]={Token,Owner,Remaining};
    }
    void Finish() {for(unsigned I=0;I<8;++I) Previous[I]=Next[I];}
};
