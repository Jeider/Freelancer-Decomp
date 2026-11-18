#pragma once
// Local single-player presentation only; durable state belongs to Content.
struct TrainCourierHud {
    unsigned size=sizeof(TrainCourierHud);
    float remaining=0;
    unsigned caption=0;
    float x=.275f,y=-.16f;
    float returnRemaining=-1;
    unsigned returnCaption=0;
};
using TrainCourierHudFn=int (__cdecl*)(unsigned,TrainCourierHud*);
