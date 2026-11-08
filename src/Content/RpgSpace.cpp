#include "RpgSpace.h"
#ifdef FREELANCER_RPG_WORLD
#include "ContentInternal.h"
#include "PilotPersonalities.h"
#include "common_server.h"
#include "common_pub.h"
#include "common_goods.h"
#include "common_newchar.h"
#include "server_cobject.h"
#include <map>
#include <set>
#include <vector>
#include <string>
#include <cmath>

namespace
{
    struct Contact
    {
        std::string Name, Ship, Loadout, Pilot, Faction, Head, Body, Accessory;
        unsigned System=0, Anchor=0, NameIds=0;
        float RespawnSeconds=60, Cooldown=0;
        Vector Offset = {};
        unsigned Object=0;
        int Reputation=-1;
    };
    std::vector<Contact> Contacts;
    std::set<unsigned> TrackedPlayers;
    float CheckElapsed=0;
    bool Loaded=false;

    void Load()
    {
        if (Loaded) return;
        Loaded=true;
        INI_Reader Reader;
        if (!OpenContentDataIni("RPG\\space.ini", &Reader)) return;
        while (Reader.read_header())
        {
            if (!Reader.is_header("RpgShip")) continue;
            Contact C;
            bool Enabled=false, Valid=true;
            while (Reader.read_value())
            {
                if (Reader.is_value("nickname")) C.Name=Reader.get_value_string();
                else if (Reader.is_value("enabled")) Enabled=Reader.get_value_bool(0);
                else if (Reader.is_value("respawn_seconds")) C.RespawnSeconds=static_cast<float>(Reader.get_value_float(0));
                else if (Reader.is_value("system")) pub::GetSystemID(C.System,Reader.get_value_string());
                else if (Reader.is_value("anchor")) C.Anchor=CreateID(Reader.get_value_string());
                else if (Reader.is_value("offset"))
                {
                    C.Offset.x=static_cast<float>(Reader.get_value_float(0));
                    C.Offset.y=static_cast<float>(Reader.get_value_float(1));
                    C.Offset.z=static_cast<float>(Reader.get_value_float(2));
                }
                else if (Reader.is_value("ship_archetype")) C.Ship=Reader.get_value_string();
                else if (Reader.is_value("loadout")) C.Loadout=Reader.get_value_string();
                else if (Reader.is_value("pilot")) C.Pilot=Reader.get_value_string();
                else if (Reader.is_value("affiliation")) C.Faction=Reader.get_value_string();
                else if (Reader.is_value("individual_name")) C.NameIds=Reader.get_value_int(0);
                else if (Reader.is_value("head")) C.Head=Reader.get_value_string();
                else if (Reader.is_value("body")) C.Body=Reader.get_value_string();
                else if (Reader.is_value("accessory")) C.Accessory=Reader.get_value_string();
                else Valid=false;
            }
            for (auto const& Existing:Contacts) if (Existing.Name==C.Name) Valid=false;
            if (Enabled && Valid && !C.Name.empty() && C.System && C.Anchor &&
                std::isfinite(C.RespawnSeconds) && C.RespawnSeconds>=0 &&
                !C.Ship.empty() && !C.Loadout.empty() && !C.Pilot.empty() && !C.Faction.empty() &&
                std::isfinite(C.Offset.x) && std::isfinite(C.Offset.y) && std::isfinite(C.Offset.z))
                Contacts.push_back(C);
        }
    }

    void Friendly(Contact const& C, unsigned Player)
    {
        int Rep=-1;
        if (C.Object && pub::Player::GetRep(Player,Rep)==0)
        {
            pub::Reputation::SetAttitude(C.Reputation,Rep,1.0f);
            pub::Reputation::SetAttitude(Rep,C.Reputation,1.0f);
        }
    }

    bool Spawn(Contact& C,unsigned Controller)
    {
        pub::SpaceObj::ShipInfo Info = {};
        unsigned AnchorSystem=0, Faction=0;
        unsigned Pilot=CreateID(C.Pilot.c_str());
        pub::AI::SetPersonalityParams AI;
        if (pub::SpaceObj::GetSystem(C.Anchor,AnchorSystem)!=0 || AnchorSystem!=C.System ||
            pub::SpaceObj::GetLocation(C.Anchor,Info.Position,Info.Orientation)!=0 ||
            pub::GetShipID(Info.ShipArchID,C.Ship.c_str())!=0 ||
            pub::GetLoadoutID(Info.LoadoutID,C.Loadout.c_str())!=0 || !Loadout::Get(Info.LoadoutID) ||
            pub::Reputation::GetReputationGroup(Faction,C.Faction.c_str())!=0 ||
            !GetPilotPersonality(&Pilot,&AI.Value)) return false;
        FmtStr Name, Empty;
        Name.begin_mad_lib(C.NameIds); Name.end_mad_lib();
        if (pub::Reputation::Alloc(C.Reputation,Empty,Name)!=0) return false;
        pub::Reputation::SetAffiliation(C.Reputation,Faction);
        Info.ControllerId=Controller;
        Info.SystemID=C.System;
        Info.Position.x+=C.Offset.x; Info.Position.y+=C.Offset.y; Info.Position.z+=C.Offset.z;
        Info.VibeGroupId=C.Reputation;
        Info.HitPts=-1;
        Info.ReputationRank=2;
        Info.CostumeHead=CreateID(C.Head.c_str());
        Info.CostumeBody=CreateID(C.Body.c_str());
        Info.CostumeLeftHand=CreateID("benchmark_male_hand_left");
        Info.CostumeRightHand=CreateID("benchmark_male_hand_right");
        if (!C.Accessory.empty()) { Info.CostumeAccessory[0]=CreateID(C.Accessory.c_str());Info.CostumeAccessoryCount=1; }
        if (pub::SpaceObj::Create(C.Object,Info)!=0 || !C.Object)
        {
            pub::Reputation::Free(C.Reputation); C.Reputation=-1; C.Object=0; return false;
        }
        AI.bSetPersonality=1;
        AI.StateGraphId=pub::StateGraph::get_state_graph("FIGHTER",pub::StateGraph::LEADER);
        AI.ContentCallbackObject=nullptr; AI.DirectiveCallbackObject=nullptr;
        pub::AI::SubmitState(C.Object,&AI);
        pub::AI::DirectiveIdleOp Idle;
        pub::AI::SubmitDirective(C.Object,&Idle);
        FDUMP(0x100001,"RPG ship %s: created %u near %u\n",C.Name.c_str(),C.Object,C.Anchor);
        return true;
    }
}

void RpgSpaceTrackPlayer(unsigned PlayerId)
{
    TrackedPlayers.insert(PlayerId);
}
void RpgSpaceLogout(unsigned PlayerId) { TrackedPlayers.erase(PlayerId); }
void RpgSpaceTick(unsigned ControllerId,float Seconds)
{
    if (!std::isfinite(Seconds) || Seconds<=0) return;
    CheckElapsed+=Seconds;
    if (CheckElapsed<1.0f) return;
    const float Elapsed=CheckElapsed;
    CheckElapsed=0;
    Load();
    for (auto& C:Contacts)
    {
        if (C.Cooldown>0) C.Cooldown=Elapsed>=C.Cooldown ? 0 : C.Cooldown-Elapsed;
        unsigned Type=0;
        if (C.Object && pub::SpaceObj::GetType(C.Object,Type)!=0)
        {
            if (C.Reputation!=-1) pub::Reputation::Free(C.Reputation);
            C.Object=0; C.Reputation=-1;
            // Zero disables respawning for the current world session.
            C.Cooldown=C.RespawnSeconds>0 ? C.RespawnSeconds : -1;
        }
    }
    for (unsigned Player:TrackedPlayers)
    {
        unsigned Ship=0,System=0;
        if (pub::Player::GetShip(Player,Ship)==0 && Ship &&
            pub::SpaceObj::ExistsAndAlive(Ship)==0 && pub::SpaceObj::GetSystem(Ship,System)==0)
        {
            for (auto& C:Contacts) if(C.System==System)
            {
                if (C.Object) { Friendly(C,Player); continue; }
                if (C.Cooldown==-1 || C.Cooldown>0) continue;
                if (Spawn(C,ControllerId)) Friendly(C,Player);
                else
                {
                    C.Cooldown=5; // Retry transient setup failures without flooding each heartbeat.
                    FDUMP(0x100001,"RPG ship %s: spawn failed; retry in 5 seconds\n",C.Name.c_str());
                }
            }
        }
    }
}
void RpgSpaceClear()
{
    TrackedPlayers.clear(); CheckElapsed=0;
    std::vector<Contact> Old; Old.swap(Contacts); Loaded=false;
    for(auto const& C:Old)
    {
        if(C.Object) pub::SpaceObj::Destroy(C.Object,DestroyType::DESTROY_NORMAL);
        if(C.Reputation!=-1) pub::Reputation::Free(C.Reputation);
    }
}
#endif
