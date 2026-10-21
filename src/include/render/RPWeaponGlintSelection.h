#pragma once
#include <cstdint>
// Fixed work/memory per visible projectile. One moving accent per shooter,
// regardless of colour, turret direction or number of concurrent salvos.
struct RPWeaponGlintSelection
{
    struct Group
    {
        unsigned Owner=0,Shots=0,Priority=9;
        float NearestSq=0,RepresentativeSq=1.e30f,Position[3]={},Colour[3]={};
        std::uintptr_t Token=0;float Remaining=0;
    };
    Group Groups[8]={};unsigned Count=0,Budget=8,Player=0;
    void Begin(unsigned Limit,unsigned PlayerId)
    {Count=0;Budget=Limit<1 ? 1 : (Limit>8 ? 8 : Limit);Player=PlayerId;}
    int Find(unsigned Owner) const
    {for(unsigned I=0;I<Count;++I) if(Groups[I].Owner==Owner) return (int)I;return -1;}
    float Score(Group const& G) const {return Player && G.Owner==Player ? -1.0f : G.NearestSq;}
    void Consider(unsigned Owner,float DistanceSq)
    {
        int Existing=Find(Owner);
        if(Existing>=0) {if(DistanceSq<Groups[Existing].NearestSq) Groups[Existing].NearestSq=DistanceSq;return;}
        Group New;New.Owner=Owner;New.NearestSq=DistanceSq;
        if(Count<Budget) {Groups[Count++]=New;return;}
        unsigned Worst=0;
        for(unsigned I=1;I<Count;++I) if(Score(Groups[I])>Score(Groups[Worst])) Worst=I;
        if(Score(New)<Score(Groups[Worst])) Groups[Worst]=New;
    }
    void Add(unsigned Owner,float DistanceSq,unsigned Priority,std::uintptr_t Token,float Remaining,
             const float* Position,const float* Colour)
    {
        int Index=Find(Owner);if(Index<0) return;
        auto& G=Groups[Index];++G.Shots;
        for(unsigned C=0;C<3;++C) G.Colour[C]+=Colour[C];
        if(!G.Token || Priority<G.Priority || (Priority==G.Priority && DistanceSq<G.RepresentativeSq))
        {
            G.Token=Token;G.Remaining=Remaining;G.Priority=Priority;G.RepresentativeSq=DistanceSq;
            for(unsigned C=0;C<3;++C) G.Position[C]=Position[C];
        }
    }
    void Finish() {for(unsigned I=0;I<Count;++I) if(Groups[I].Shots)
        for(float& C:Groups[I].Colour) C/=Groups[I].Shots;}
};
