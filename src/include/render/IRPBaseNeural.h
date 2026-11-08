#pragma once
#include "dacom.h"
#include "base_neural_bridge.h"

// Optional interface, compiled out of RP9 when FreelancerDlss5=0.
struct IRPBaseNeural : IDAComponent
{
    virtual GENRESULT DACOM_API ProcessBaseNeural(BaseNeuralBridge::Frame const* Frame) = 0;
    virtual void DACOM_API StopBaseNeural() = 0;
    virtual GENRESULT DACOM_API BeginBaseSupersample(float Scale) = 0;
    virtual GENRESULT DACOM_API EndBaseSupersample() = 0;
};
namespace Iids { static const char RPBaseNeural[] = "IRPBaseNeural_v2"; }
