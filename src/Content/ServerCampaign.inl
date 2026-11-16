// Dedicated-host campaign. SP keeps FStory and its original money thresholds.
namespace {
class FServerCampaign final : public IDLL, public IStoryMissionEvents {
    CampaignControl::Snapshot status;
    CampaignControl::ProgressFile file{CampaignControl::ProgressFile::ServerPath()};
    unsigned id;
    std::wstring ownerName;
    bool starting = false;
    bool shipBought = false;

    void Publish(unsigned notice = CampaignControl::Ready) {
        status.notice=notice;
        status.initialized=1;
        CampaignControl::Publish(status);
    }
    bool Commit(CampaignControl::State const& next) {
        if (!file.Save(next)) { status.state.phase=CampaignControl::Error;Publish(CampaignControl::DiskError);return false; }
        status.state=next;Publish();return true;
    }
    void SyncRanks() {
        for (auto const& item : GetContentPlayerStates()) {
            if (!item.second) continue;
            int rank=0;
            if (pub::Player::GetRank(item.first,rank)==0 && rank!=int(status.state.rank))
                pub::Player::SetRank(item.first,int(status.state.rank));
            pub::Player::SetMoneyNeededToNextRank(item.first,0);
            item.second->MissionNumber=status.state.chapter;
            RecalculateContentPlayerRank(item.second.get());
        }
    }
    bool OwnerPresent() const {
        std::wstring name;
        return status.owner && reinterpret_cast<std::uintptr_t>(FindContentPlayerState(status.owner))==status.ownerState &&
            pub::Player::GetName(status.owner,name)==0 && name==ownerName;
    }
    bool SelectOwner() {
        // Never cancel a player's random mission to start the story.
        auto* previousOwner=OwnerPresent()?FindContentPlayerState(status.owner):nullptr;
        unsigned candidate=previousOwner && (previousOwner->GetBaseRecord() || previousOwner->ShipObject) ? status.owner : 0;
        for (auto const& item : GetContentPlayerStates()) {
            auto* player=item.second.get();
            if (!player) continue;
            if (player->GetLiveMission()!=0) { Publish(CampaignControl::PlayerBusy);return false; }
            if (!candidate && (player->GetBaseRecord() || player->ShipObject)) candidate=item.first;
        }
        if (!candidate || pub::Player::GetName(candidate,ownerName)!=0) { Publish(CampaignControl::NoPlayers);return false; }
        status.owner=candidate;
        status.ownerState=reinterpret_cast<std::uintptr_t>(FindContentPlayerState(candidate));
        wcsncpy_s(status.ownerName,ownerName.c_str(),_TRUNCATE);
        return true;
    }
    void ShipReputation() {
        shipBought=true;
        int rep=-1;unsigned group=0;
        if (pub::Player::GetRep(status.owner,rep)==0) {
            pub::Reputation::GetReputationGroup(group,"gd_bh_grp");
            pub::Reputation::SetReputation(rep,group,-.2f);
        }
    }
    void EndPlayers(unsigned controller,int outcome) {
        // Joined campaign participants need not be members of the retail group.
        for (auto const& item : GetContentPlayerStates()) {
            auto* player=item.second.get();
            if (player && player->GetLiveMission()==controller) {
                player->EndLiveMission(controller,outcome,false);
                player->SetDockAccess(1,nullptr);
                player->SetTradelaneAccess(1,nullptr);
            }
        }
    }
    void Start() {
        using namespace CampaignControl;
        if (starting || status.controller || status.state.completed>=MissionCount || !SelectOwner()) return;
        starting=true;
        auto previous=status.state;
        auto next=previous;
        auto const& mission=Missions()[next.completed];
        next.phase=Running;next.chapter=mission.start;next.rank=RankForChapter(next.chapter);++next.revision;
        FILETIME now;GetSystemTimeAsFileTime(&now);
        next.attempt=(std::uint64_t(now.dwHighDateTime)<<32)|now.dwLowDateTime;
        if (next.attempt<=previous.attempt) next.attempt=previous.attempt+1;
        // Publish the attempt before constructing the script: local trigger saves
        // from another attempt must not suppress this mission's initial triggers.
        if (!Commit(next)) { starting=false;return; }
        FStoryMissionCreateParms parms;parms.PlayerId=status.owner;parms.StoryEvents=this;
        unsigned controller=pub::Controller::Create("Content.dll",mission.name,&parms,pub::Controller::ABOVE_NORMAL);
        if (!controller) {
            if (Commit(previous)) Publish(CreateFailed);
            starting=false;return;
        }
        status.controller=controller;SyncRanks();Publish();
        pub::Controller::_SendMessage(controller,pub::Controller::EMessage::MissionStart,nullptr);
        starting=false;
    }
public:
    explicit FServerCampaign(unsigned controller) : id(controller) {
        int loaded=file.Load(status.state);
        if (loaded<0) { status.state.phase=CampaignControl::Error;Publish(CampaignControl::CorruptSave); }
        else {
            if (status.state.phase==CampaignControl::Running) status.state.phase=CampaignControl::Interrupted;
            Publish();
        }
        pub::Controller::SetHeartbeatInterval(id,.25f);
    }
    void OnMissionEvent(unsigned event, unsigned chapter, unsigned controller) override {
        using namespace CampaignControl;
        if (status.state.phase!=Running || controller!=status.controller || status.state.completed>=MissionCount) return;
        auto const& mission=Missions()[status.state.completed];
        if (event==1) {
            if (chapter<mission.start || chapter>mission.finish) return;
            auto next=status.state;next.chapter=chapter;next.rank=RankForChapter(chapter);
            if (chapter!=status.state.chapter) { ++next.revision;if (!Commit(next)) return;SyncRanks(); }
            if (chapter==23) ShipReputation();
            return;
        }
        if (event==4) {
            status.controller=0;
            EndPlayers(controller,3);
            auto next=status.state;next.phase=Interrupted;++next.revision;
            Commit(next);return;
        }
        if (event!=3 || chapter!=mission.finish) return;
        // Succeed already ran EndMission. Clear the id before any reentrant messages.
        status.controller=0;
        EndPlayers(controller,2);
        auto next=status.state;++next.completed;next.chapter=mission.after;next.rank=RankForChapter(next.chapter);++next.revision;
        next.phase=next.completed==MissionCount ? Complete : mission.automaticNext ? Automatic : Freeflight;
        if (Commit(next)) SyncRanks();
        pub::Controller::Destroy(controller);
        // Automatic continuations are started on the next heartbeat, after the
        // old controller has unwound and released its mission state.
    }
    void HandleMessage(pub::Controller::EMessage event, void const* data) override {
        using namespace CampaignControl;
        using pub::Controller::EMessage;
        if (!CampaignServer::Enabled() || pub::SinglePlayer()) return;
        if (event==EMessage::PlayerShipArchSet && data && status.state.phase!=Error &&
            status.state.chapter>=15 && status.state.chapter<23 && !shipBought && OwnerPresent() &&
            *static_cast<unsigned const*>(data)==status.owner) ShipReputation();
        if (event!=EMessage::Heartbeat && event!=EMessage::BaseEnter) return;
        if (status.state.phase==Error) return;
        SyncRanks();
        Request request;
        bool requested=Take(request);
        if (((status.state.phase==First || status.state.phase==Automatic) && status.notice!=CreateFailed) ||
            (requested && CanRequest(status.state,request))) Start();
        if (!status.controller || status.state.phase!=Running) return;
        if (!OwnerPresent()) { Publish(OwnerAbsent);return; }
        Publish();
        for (auto const& item : GetContentPlayerStates()) {
            auto* player=item.second.get();
            if (player && !player->GetLiveMission() && (player->GetBaseRecord() || player->ShipObject)) {
                player->JoinMission(&status.controller,status.owner,true,0);
                if (event==EMessage::BaseEnter && data && static_cast<unsigned const*>(data)[1]==item.first)
                    pub::Controller::_SendMessage(status.controller,event,data);
            }
        }
    }
};
}
