// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Content.dll TU16 (06ea6d50-06ea7750): the "StoryLauncher" controller.
// Retail object is 8 bytes: vptr 06fb43c0 (slot 0 LAB_06ea6f50) + ControllerId at +4.

#include "ContentInternal.h"  // OpenContentDataIni (FUN_06f24280), G_ContentModule
#include "ContentStaticIds.h" // TU16 static IDs 06ea6d50..06ea6f30
#include "NpcShips.h"         // FNpcCharacterDesc, LoadNpcCharacterDesc, GSpecificNpcs (DAT_06fd081c)
#include "common_id.h"
#include "common_ini.h"
#include "common_server_controller.h"
#include "common_server.h"
#include "campaign_server.h"
#include "ContentPlayerState.h"

#include <new>
#include <utility>

namespace
{
    class FStoryLauncher : public IDLL
    {
    public:
        explicit FStoryLauncher(unsigned int const* InControllerId);
        // Slot 1, FUN_06ea7330 -> FUN_06ea7350.
        ~FStoryLauncher() override;

        void HandleMessage(pub::Controller::EMessage MessageId, void const* MessageParms) override;

    private:
        unsigned int ControllerId;
    };

    // FUN_06ea6ff0 (06ea6ff0-06ea7325, RET 8): (&ControllerId, Parms); Parms is not read. The
    // heartbeat is switched off, then missions\specific_npc.ini (FUN_06f24280, result not
    // tested) is read into the process-wide table DAT_06fd081c: every [NPC] block becomes a
    // description (FUN_06f32920) filled by FUN_06f32b70 - whose result is not tested either -
    // and inserted under its nickname id (the map's unique insert inlined, 06ea70f0-06ea71d3;
    // a repeated nickname keeps the first). EH states: 0 the IDLL base, 1-4 the local
    // INI_Reader and its members (destroyed inline at 06ea71f1-06ea7305).
    void LoadStoryNpcs()
    {
        INI_Reader Reader;
        OpenContentDataIni("missions\\specific_npc.ini", &Reader);
        while (Reader.read_header())
        {
            if (!Reader.is_header("NPC"))
                continue;
            FNpcCharacterDesc Desc;
            ID_String Nickname;
            Nickname.clear();
            LoadNpcCharacterDesc(&Nickname, &Desc, &Reader);
            GSpecificNpcs.insert(std::make_pair(Nickname.Id, Desc));
        }
    }

    FStoryLauncher::FStoryLauncher(unsigned int const* InControllerId)
        : ControllerId(*InControllerId)
    {
        pub::Controller::SetHeartbeatInterval(ControllerId, -1.0f);
        LoadStoryNpcs();
    }

    // FUN_06ea7350 (06ea7350-06ea744a): the specific NPC table DAT_06fd081c is emptied (the
    // tree's erase(begin, end) inlined: the whole-tree path FUN_06ea76a0 when it holds every
    // node, else node by node FUN_06ea76e0 / FUN_06f44330), then the IDLL base.
    FStoryLauncher::~FStoryLauncher()
    {
        GSpecificNpcs.clear();
    }

    // LAB_06ea6f50 (RET 8): message 7 carries the player id; create "Story" through
    // this module's own path (GetModuleFileNameA on DAT_06fcf3a4), priority NORMAL. The
    // parameter object has a vtable (06fb439c, EH state 0).
    void FStoryLauncher::HandleMessage(pub::Controller::EMessage MessageId, void const* MessageParms)
    {
        if (MessageId != pub::Controller::EMessage::PlayerLogin)
            return;

        pub::Controller::FStoryCreateParms StoryParms;
        StoryParms.PlayerId = *static_cast<unsigned int const*>(MessageParms);
        char ModulePath[0x104];
        GetModuleFileNameA(G_ContentModule, ModulePath, 0x104);
        pub::Controller::Create(ModulePath, "Story", &StoryParms, pub::Controller::NORMAL);
    }
}

IDLL* CreateStoryLauncher(char const* /*Name*/, unsigned int ControllerId, void const* /*Parms*/)
{
    // The SP launcher creates one Story per login and must never run in MP.
    if (!pub::SinglePlayer()) return nullptr;
    // FUN_06eeec50: operator new(8), then FUN_06ea6ff0(&ControllerId, Parms).
    return new (std::nothrow) FStoryLauncher(&ControllerId);
}

namespace {
class FCampaignLauncher final : public IDLL {
    bool started = false;
public:
    explicit FCampaignLauncher(unsigned id) {
        LoadStoryNpcs();
        pub::Controller::SetHeartbeatInterval(id, 0.25f);
    }
    ~FCampaignLauncher() override { GSpecificNpcs.clear(); }
    void HandleMessage(pub::Controller::EMessage event, void const* data) override {
        if (started || !CampaignServer::Enabled() || pub::SinglePlayer() ||
            (event != pub::Controller::EMessage::Heartbeat && event != pub::Controller::EMessage::BaseEnter)) return;
        // GameSupport (HIGHEST) has loaded the base before this NORMAL controller.
        // Register autoplay RTC before LocationEnter, not after the room is displayed.
        for (auto const& item : GetContentPlayerStates()) {
            if (event == pub::Controller::EMessage::BaseEnter &&
                (!data || static_cast<unsigned const*>(data)[1] != item.first)) continue;
            auto* player = item.second.get();
            if (!player || (!player->GetBaseRecord() && !player->ShipObject)) continue;
            pub::Controller::FStoryCreateParms parms;parms.PlayerId = item.first;
            started = true; // protect against nested/duplicate login events
            unsigned id = pub::Controller::Create("Content.dll", "CampaignStory", &parms,
                                                  pub::Controller::NORMAL);
            if (!id) {
                FDUMP(0x100002, "CampaignServer: failed to create the shared Story controller");
                // No automatic retry: partially initialized story actions must not repeat.
            } else {
                float elapsed = 0;
                pub::Controller::_SendMessage(id, pub::Controller::EMessage::Heartbeat, &elapsed);
            }
            return;
        }
    }
};
}

IDLL* CreateCampaignLauncher(char const*, unsigned id, void const*) {
    if (!CampaignServer::Enabled() || pub::SinglePlayer()) return nullptr;
    return new (std::nothrow) FCampaignLauncher(id);
}
