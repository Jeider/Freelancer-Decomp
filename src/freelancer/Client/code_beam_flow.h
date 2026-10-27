#pragma once
#include "effect_vertex_batch.h"
#include <algorithm>
#include <cmath>
#include <cstdint>

// Port-only GPU copy. The retail vertex/batch/beam layouts are deliberately unchanged.
struct FCodeBeamVertex
{
    FEffectVertex Base;
    float LocalX, LocalY, Along, Phase;
};
static_assert(sizeof(FCodeBeamVertex) == 40, "XYZ|DIFFUSE|TEX2, second coordinate float4");

namespace CodeBeamFlow
{
inline void Fill(const FEffectVertex* Input, FCodeBeamVertex* Output, int Count,
                 const float* Transform12, std::uint32_t Seed)
{
    float Width = .0001f, MinZ = 0, MaxZ = 0;
    float InvLength[3];
    for (int Axis=0; Axis<3; ++Axis)
    {
        float Length=0;
        for(int Row=0;Row<3;++Row) Length+=Transform12[Row*3+Axis]*Transform12[Row*3+Axis];
        InvLength[Axis]=1.0f/(std::max)(Length,.000001f);
    }
    Seed ^= Seed >> 16; Seed *= 0x7feb352du; Seed ^= Seed >> 15;
    const float Phase=float(Seed & 65535u)/65536.0f;
    for(int I=0; I<Count; ++I)
    {
        auto& Out=Output[I];Out.Base=Input[I];
        const float Delta[3]={Input[I].X-Transform12[9],Input[I].Y-Transform12[10],Input[I].Z-Transform12[11]};
        float Local[3]={};
        // Inverse of rotation plus orthogonal scale. Beams use rigid transforms.
        for(int Axis=0;Axis<3;++Axis)for(int Row=0;Row<3;++Row)
            Local[Axis]+=Delta[Row]*Transform12[Row*3+Axis]*InvLength[Axis];
        Out.LocalX=Local[0];Out.LocalY=Local[1];Out.Along=Local[2];Out.Phase=Phase;
        if(Input[I].U < .5f) Width=(std::max)(Width,(std::max)(std::fabs(Local[0]),std::fabs(Local[1])));
        MinZ=(std::min)(MinZ,Local[2]);MaxZ=(std::max)(MaxZ,Local[2]);
    }
    const float Span=(std::max)(MaxZ-MinZ,.0001f);
    for(int I=0;I<Count;++I)
    {
        Output[I].LocalX/=Width;Output[I].LocalY/=Width;
        Output[I].Along/=Span; // local +Z is the tail; continuous across all segment seams
    }
}
}
