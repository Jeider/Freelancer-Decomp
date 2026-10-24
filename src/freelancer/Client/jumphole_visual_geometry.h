#pragma once
#include <cstdint>
struct FJumpHoleVertex { float Position[3]; std::uint32_t Color; float UV[2]; };
static_assert(sizeof(FJumpHoleVertex) == 24, "jumphole XYZ/DIFFUSE/TEX1");
// ClassifySphere expects camera space, with forward along -Z.
inline void JumpHoleWorldToView(float const* View, float const* World, float* Out)
{
    for (unsigned R=0;R<3;++R)
        Out[R]=View[R*3]*World[0]+View[R*3+1]*World[1]+View[R*3+2]*World[2]+View[9+R];
}
// View rows look along -Z; optics rays use +Z. ObjectRotation is local-to-world.
inline void JumpHoleCameraToLocal(float const* View,float const* ObjectRotation,float* Rows)
{
    for (unsigned R=0;R<3;++R)
    {
        for (unsigned C=0;C<3;++C)
        {
            float Value=0;
            for (unsigned K=0;K<3;++K) Value+=ObjectRotation[K*3+R]*View[C*3+K];
            Rows[R*4+C]=Value*(C==2 ? -1.0f : 1.0f);
        }
        Rows[R*4+3]=0;
    }
}
constexpr unsigned JumpHoleLensVertexCount=36;
constexpr unsigned JumpHoleVertexCount=36;
inline void BuildJumpHoleVisualGeometry(FJumpHoleVertex* Vertices)
{
    float const Half[3]={560,500,500};
    int const Order[6]={0,1,2,2,1,3}; unsigned Out=0;
    for(unsigned Axis=0;Axis<3;++Axis) for(unsigned Side=0;Side<2;++Side)
    {
        FJumpHoleVertex Corners[4]={};
        unsigned Bytes[3]={128,128,128}; Bytes[Axis]=Side ? 255 : 0;
        std::uint32_t Color=0xff000000u|(Bytes[0]<<16)|(Bytes[1]<<8)|Bytes[2];
        for(unsigned K=0;K<4;++K)
        {
            Corners[K].Position[Axis]=(Side ? 1.0f : -1.0f)*Half[Axis];
            Corners[K].Position[(Axis+1)%3]=((K&1) ? 1.0f : -1.0f)*Half[(Axis+1)%3];
            Corners[K].Position[(Axis+2)%3]=((K&2) ? 1.0f : -1.0f)*Half[(Axis+2)%3];
            Corners[K].Color=Color;
        }
        for(unsigned K=0;K<6;++K) Vertices[Out++]=Corners[Order[K]];
    }
}
