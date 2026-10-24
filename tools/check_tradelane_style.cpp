#include "../src/freelancer/Client/tradelane_visual_style.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <limits>

static void Require(bool value,const char* name)
{
    std::printf("%s: %s\n",value?"PASS":"FAIL",name);
    if(!value)std::exit(1);
}
static bool Same(FTradeLaneVisualStyle const& a,FTradeLaneVisualStyle const& b)
{
    for(unsigned i=0;i<3;++i)if(a.Body[i]!=b.Body[i]||a.Accent[i]!=b.Accent[i])return false;
    for(unsigned i=0;i<4;++i)if(a.Seed[i]!=b.Seed[i])return false;
    return a.Enabled==b.Enabled&&a.Mode==b.Mode;
}
int main()
{
    FTradeLaneVisualStyle neutral,style;
    Require(neutral.Enabled==0&&neutral.Mode==0,"default style preserves neutral rendering");
    float black[3]={},green[3]={.39f,1,.39f},minimum[3]={0,.12f,0},maximum[3]={0,.39f,0};
    Require(!TradeLaneBuildPalette(style,black,black,black,black,1)&&Same(style,neutral),"black palette fails without changing fallback");
    float invalid[3]={std::numeric_limits<float>::quiet_NaN(),0,0};
    Require(!TradeLaneBuildPalette(style,invalid,green,minimum,maximum,1)&&Same(style,neutral),"non-finite palette preserves fallback");
    Require(TradeLaneBuildPalette(style,green,green,minimum,maximum,1),"nonzero palette builds");
    Require(style.Body[1]>style.Body[0]&&style.Accent[1]>style.Accent[0],"green gate retains dominant hue");
    bool finite=true;for(unsigned i=0;i<3;++i)finite&=std::isfinite(style.Body[i])&&std::isfinite(style.Accent[i])&&style.Body[i]>=0&&style.Body[i]<=1&&style.Accent[i]>=0&&style.Accent[i]<=1;
    Require(finite,"palette components remain finite and normalized");
    Require(TradeLaneSelectStyleCandidate(nullptr,0)==0,"empty gate set returns no candidate");
    FTradeLaneStyleCandidate gates[4];
    for(auto& g:gates)g.Style=style;
    gates[0].TunnelId=10;gates[0].GateId=100;gates[0].DistanceSq=500;
    gates[1].TunnelId=10;gates[1].GateId=101;gates[1].DistanceSq=400;gates[1].Style.Mode=2;
    gates[2].TunnelId=20;gates[2].GateId=200;gates[2].DistanceSq=1;
    Require(TradeLaneSelectStyleCandidate(gates,3)==1,"resolved tunnel majority wins despite nearer minority and different descriptor styles");
    gates[1].TunnelId=20;gates[1].DistanceSq=20;gates[3].TunnelId=10;gates[3].GateId=102;gates[3].DistanceSq=10;
    Require(TradeLaneSelectStyleCandidate(gates,4)==2,"equal tunnel counts choose nearest gate");
    gates[2].DistanceSq=10;
    Require(TradeLaneSelectStyleCandidate(gates,4)==3,"equal distance uses stable tunnel ID");
    gates[0].DistanceSq=10;
    Require(TradeLaneSelectStyleCandidate(gates,4)==0,"same tunnel and distance use stable gate ID");
    std::reverse(gates,gates+4);auto selected=TradeLaneSelectStyleCandidate(gates,4);
    Require(gates[selected].GateId==100,"selection is independent of candidate enumeration order");
    FTradeLaneStyleCandidate invalidGates[4];for(auto& g:invalidGates){g.Style=style;g.TunnelId=10;}
    invalidGates[0].TunnelId=0;invalidGates[1].Style.Enabled=0;invalidGates[2].DistanceSq=-1;invalidGates[3].DistanceSq=std::numeric_limits<double>::infinity();
    Require(TradeLaneSelectStyleCandidate(invalidGates,4)==4,"unresolved disabled and invalid-distance candidates are excluded");
    auto a=style,b=style,c=style;TradeLaneSeedStyle(a,123,456);TradeLaneSeedStyle(b,123,456);TradeLaneSeedStyle(c,123,457);
    Require(Same(a,b),"same system and route seed deterministically");
    Require(!Same(a,c),"different route changes variation seed");
    bool inRange=true;for(float v:a.Seed)inRange&=std::isfinite(v)&&v>=0&&v<1;
    Require(inRange,"noise and event seeds are finite in unit interval");
    std::puts("PASS tradelane style helpers; archetype/effect eligibility is the runtime caller's responsibility");
}
