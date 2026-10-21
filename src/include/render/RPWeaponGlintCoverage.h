#pragma once
#include <cmath>
#include <cstring>
// Camera-relative 64m cells covering the entire 1000m effect range. Conservative
// hull bounds reject clearly empty space in O(1) per projectile, without rays.
struct RPWeaponGlintCoverage
{
    unsigned char Cells[32*32*32]={};bool Any=false;
    static int Cell(float V) {return (int)std::floor((V+1024.0f)/64.0f);}
    void Mark(const float* Center,float Radius)
    {
        int Lo[3],Hi[3];
        for(unsigned I=0;I<3;++I)
        {
            if(Center[I]+Radius< -1024 || Center[I]-Radius>=1024) return;
            Lo[I]=Cell(Center[I]-Radius);Hi[I]=Cell(Center[I]+Radius);
            if(Lo[I]<0) Lo[I]=0;if(Hi[I]>31) Hi[I]=31;
        }
        Any=true;
        for(int Z=Lo[2];Z<=Hi[2];++Z) for(int Y=Lo[1];Y<=Hi[1];++Y)
            std::memset(Cells+(Z*32+Y)*32+Lo[0],1,Hi[0]-Lo[0]+1);
    }
    bool Contains(const float* Position) const
    {
        int X=Cell(Position[0]),Y=Cell(Position[1]),Z=Cell(Position[2]);
        return (unsigned)X<32 && (unsigned)Y<32 && (unsigned)Z<32 && Cells[(Z*32+Y)*32+X]!=0;
    }
};
