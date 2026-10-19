// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only (FREELANCER_DBG_OPTIONS): the server half of the console commands taken from
// adoxa's console.dll v1.24 (cmdSave, cmdBase, cmdSystem, cmdJump). See port_console_api.h.

#ifdef FREELANCER_DBG_OPTIONS

#include "../include/port_console_api.h"
#include "../include/common_server.h"
#include "../include/common_server_playerdb.h"
#include "../include/common_id.h"
#include "../include/server_cobject.h"
#include "../include/server_playerdb.h"
#include "../include/server_savegame.h"

#include <cctype>
#include <cmath>
#include <cstring>

namespace pub
{
    namespace SpaceObj
    {
        // server_pub.cpp (?GetBurnRadius@SpaceObj@pub@@YAHABIAAMAAVVector@@@Z).
        SERVER_API int __cdecl GetBurnRadius(const unsigned int& obj_id_ref, float& out_radius, Vector& out_center);
    }
}

namespace
{
    unsigned const kPlayer = 1; // single player

    FPortConsoleSystem G_PendingSystem;
    bool G_bPendingSystem = false;

    void AddAxis(Vector& Pos, float Distance, Matrix const& Orient, int Axis)
    {
        Pos.x += Distance * Orient.E[0][Axis];
        Pos.y += Distance * Orient.E[1][Axis];
        Pos.z += Distance * Orient.E[2][Axis];
    }

    void TurnAround(Matrix& Orient)
    {
        // console.dll's Matrix::turn_around: half a turn about the up axis.
        for (int Row = 0; Row < 3; ++Row)
        {
            Orient.E[Row][0] = -Orient.E[Row][0];
            Orient.E[Row][2] = -Orient.E[Row][2];
        }
    }

    float ObjectRadius(unsigned Object)
    {
        float Radius = 0.0f, Burn = 0.0f;
        Vector Centre;
        pub::SpaceObj::GetRadius(Object, Radius, Centre);
        pub::SpaceObj::GetBurnRadius(Object, Burn, Centre);
        return Radius < Burn ? Burn : Radius;
    }

    bool PartialMatch(char const* Name, char const* Part)
    {
        size_t const Length = std::strlen(Part);
        for (char const* At = Name; *At != '\0'; ++At)
            if (_strnicmp(At, Part, Length) == 0)
                return true;
        return false;
    }

    // console.dll find_object: a nickname, or "~part" of one (the first match).
    unsigned FindObject(unsigned System, char const* Name)
    {
        if (Name[0] != '~')
        {
            unsigned const Id = CreateID(Name);
            unsigned InSystem = 0;
            if (pub::SpaceObj::GetSystem(Id, InSystem) >= 0 && InSystem == System)
                return Id;
        }
        struct FFind : pub::System::SysObjEnumerator
        {
            char const* Part;
            bool bPartial;
            unsigned Found = 0;
            bool Slot00(pub::System::FSysObj const* Object) override
            {
                bool const bHit = bPartial ? PartialMatch(Object->Nickname, Part) : _stricmp(Object->Nickname, Part) == 0;
                if (bHit)
                {
                    Found = CreateID(Object->Nickname);
                    return false;
                }
                return true;
            }
        } Find;
        Find.bPartial = Name[0] == '~';
        Find.Part = Find.bPartial ? Name + 1 : Name;
        pub::System::EnumerateObjects(System, Find);
        return Find.Found;
    }

    // console.dll enter_system / cmdJump: where to put a ship that arrives at Object.
    void PlaceAt(unsigned Object, Vector& Pos, Matrix& Orient, Vector const* From)
    {
        unsigned Type = 0;
        pub::SpaceObj::GetType(Object, Type);
        Vector TargetPos;
        Matrix TargetOrient;
        pub::SpaceObj::GetLocation(Object, TargetPos, TargetOrient);
        float Radius = ObjectRadius(Object);
        if (Type == 0x20) // docking ring: in front of the opening
        {
            Pos = TargetPos;
            Orient = TargetOrient;
            AddAxis(Pos, -Radius, Orient, 2);
            AddAxis(Pos, 98.0f, Orient, 0);
            return;
        }
        if (Type == 0x40) // jump gate: out in front, facing away
        {
            Pos = TargetPos;
            Orient = TargetOrient;
            AddAxis(Pos, 1.5f * Radius, Orient, 2);
            TurnAround(Orient);
            return;
        }
        if (From == nullptr)
        {
            // Arriving in a system: on the object's -Z side, the whole of a planet in view.
            if (Type & 7)
                Radius *= 2.0f;
            Pos = TargetPos;
            Orient = TargetOrient;
            AddAxis(Pos, -Radius, Orient, 2);
            return;
        }
        // Jumping in-system: on the line from the ship to the object, facing it.
        double const Dx = TargetPos.x - From->x, Dy = TargetPos.y - From->y, Dz = TargetPos.z - From->z;
        double const Distance = std::sqrt(Dx * Dx + Dy * Dy + Dz * Dz);
        if ((Type & 7) != 0 && (Distance < Radius + 2.0 || Distance > Radius * 2.0 + 2.0))
            Radius *= 2.0f;
        if (Distance > 0.0)
        {
            Pos.x = static_cast<float>(TargetPos.x - Radius * Dx / Distance);
            Pos.y = static_cast<float>(TargetPos.y - Radius * Dy / Distance);
            Pos.z = static_cast<float>(TargetPos.z - Radius * Dz / Distance);
        }
        Vector Delta;
        Delta.x = TargetPos.x - Pos.x;
        Delta.y = TargetPos.y - Pos.y;
        Delta.z = TargetPos.z - Pos.z;
        Orient = LookMatrixYup(Delta);
    }

    int Jump(FPortConsoleJump const& In)
    {
        unsigned Ship = 0;
        pub::Player::GetShip(kPlayer, Ship);
        if (Ship == 0)
            return kPortConsoleNotInSpace;
        unsigned System = 0;
        pub::SpaceObj::GetSystem(Ship, System);
        Vector Pos;
        Matrix Orient;
        pub::SpaceObj::GetLocation(Ship, Pos, Orient);
        if (In.Mode == 1)
        {
            // console.dll: x forward (-Z), y right, z up.
            AddAxis(Pos, -In.Offset.x, Orient, 2);
            AddAxis(Pos, In.Offset.y, Orient, 0);
            AddAxis(Pos, In.Offset.z, Orient, 1);
        }
        else
        {
            unsigned Target = 0;
            if (In.Mode == 0)
                pub::SpaceObj::GetTarget(Ship, Target);
            else
                Target = FindObject(System, In.Object);
            if (Target == 0)
                return In.Mode == 0 ? kPortConsoleNoTarget : kPortConsoleObjectNotFound;
            Vector const From = Pos;
            PlaceAt(Target, Pos, Orient, &From);
        }
        pub::SpaceObj::Relocate(Ship, System, Pos, Orient);
        return kPortConsoleOk;
    }
}

// Read by IServerImpl::SystemSwitchOutComplete: the console's destination instead of a gate's.
bool PortConsoleTakeSystemSwitch(unsigned ShipId, unsigned& OutSystem, Vector& InOutPos, Matrix& InOutOrient)
{
    if (!G_bPendingSystem)
        return false;
    G_bPendingSystem = false;
    OutSystem = G_PendingSystem.System;
    if (G_PendingSystem.Mode == 1)
    {
        InOutPos = G_PendingSystem.Pos;
        InOutOrient = G_PendingSystem.Orient;
    }
    else if (G_PendingSystem.Mode == 2)
    {
        unsigned const Object = FindObject(G_PendingSystem.System, G_PendingSystem.Object);
        if (Object != 0)
            PlaceAt(Object, InOutPos, InOutOrient, nullptr);
    }
    else
    {
        Vector Pos;
        Matrix Orient;
        if (pub::SpaceObj::GetLocation(ShipId, Pos, Orient) >= 0)
        {
            InOutPos = Pos;
            InOutOrient = Orient;
        }
    }
    return true;
}

extern "C" __declspec(dllexport) int __cdecl PortConsoleServer(int Op, void const* In)
{
    switch (Op)
    {
    case kPortConsoleSave:
    {
        // console.dll cmdSave: PlayerData::save straight away, in space too.
        FPortConsoleSave const* const Save = static_cast<FPortConsoleSave const*>(In);
        return PlayerData_SaveGame(Players[kPlayer], Save->File, Save->Description, 0) ? 1 : 0;
    }
    case kPortConsoleForceLand:
        return pub::Player::ForceLand(kPlayer, *static_cast<unsigned const*>(In)) >= 0 ? kPortConsoleOk
                                                                                         : kPortConsoleFailed;
    case kPortConsoleSystem:
        G_PendingSystem = *static_cast<FPortConsoleSystem const*>(In);
        G_bPendingSystem = true;
        return kPortConsoleOk;
    case kPortConsoleJump:
        return Jump(*static_cast<FPortConsoleJump const*>(In));
    default:
        return kPortConsoleFailed;
    }
}

#endif
