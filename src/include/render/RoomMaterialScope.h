#pragma once
#include "IRPRoomMaterials.h"
#include "IRenderPipeline.h"
#include "dacom_iids.h"

struct FRPRoomMaterialScope
{
    IRPRoomMaterials* Room = nullptr;
    FRPRoomMaterialScope(IRenderPipeline* Pipeline, const char* Name, const char* Texture,
                         const char* Detail = nullptr)
    {
        if (Pipeline && Pipeline->QueryInterface(Iids::RPRoomMaterials,
                reinterpret_cast<void**>(&Room)) >= 0 && Room)
        {
            Room->SetRoomMaterial(Name, Texture);
            Room->SetRoomDetail(Detail);
        }
    }
    ~FRPRoomMaterialScope()
    {
        if (Room)
        {
            Room->SetRoomMaterial(nullptr, nullptr);
            Room->SetRoomDetail(nullptr);
            Room->Release();
        }
    }
};
