#pragma once
#include "IRPRoomMaterials.h"
#include "IRenderPipeline.h"
#include "dacom_iids.h"

struct FRPRoomMaterialScope
{
    IRPRoomMaterials* Room = nullptr;
    FRPRoomMaterialScope(IRenderPipeline* Pipeline, const char* Name, const char* Texture)
    {
        if (Pipeline && Pipeline->QueryInterface(Iids::RPRoomMaterials,
                reinterpret_cast<void**>(&Room)) >= 0 && Room)
            Room->SetRoomMaterial(Name, Texture);
    }
    ~FRPRoomMaterialScope()
    {
        if (Room) { Room->SetRoomMaterial(nullptr, nullptr); Room->Release(); }
    }
};
