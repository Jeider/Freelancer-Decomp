#pragma once
namespace TrainYard {
constexpr float CaptureDistance=15.f;
constexpr float SpawnPinGap=12.f;
struct Packet {
    unsigned size=sizeof(Packet),version=2,player=0,revision=0;
    unsigned operation=0; // 0 status, 1 initial spawn, 2 approach, 3 uncouple, 4 cancel
    unsigned trailer=0;
    int result=0,coupled=0;
    int approaching=0;
    float distance=0;
};
using BridgeFn=int (__cdecl*)(Packet*);
constexpr char Export[]="TrainYardBridge";
}
