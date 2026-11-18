// Included inside CourierMission. A parked solar exposes the existing docking
// berth; Server's private ship cache retains the exact locomotive equipment.
TrainEvacuation::State evac;
unsigned employer=0,evacSystem=0;
Vector evacPosition{};
Matrix evacOrientation{1,0,0,0,1,0,0,0,1};
float evacHealth=1.f;
bool evacConfirm=false,evacQueued=false,evacRestore=false,evacCriticalSpoken=false;
bool evacDestroyPending=false;
bool evacWaitingSpoken=false;

bool canReboard(unsigned target) {
    using E=TrainEvacuation::Phase;
    if(!ready || bPendingDestroy || swapped || !target || target!=boarding ||
       (evac.phase!=E::Away && evac.phase!=E::Returning) || evac.remaining<=0 ||
       evac.locomotiveLost || evacSystem!=system())return false;
    float health=0;
    return pub::SpaceObj::GetRelativeHealth(boarding,health)==0 && health>.05f;
}

FmtStr reputationValue(float value) const {
    FmtStr text;text.begin_mad_lib(TrainEvacuation::RateText);
    text.append_string(value<0?TrainEvacuation::Minus:TrainEvacuation::Plus);
    unsigned n=unsigned(std::round((std::min)(std::fabs(value),10000.f)*10000.f));
    text.append_int(n/10000);text.append_int(n/1000%10);text.append_int(n/100%10);
    text.append_int(n/10%10);text.append_int(n%10);text.end_mad_lib();return text;
}
bool applyCourierReputation(TrainEvacuation::RepEvent event) {
    int playerRep=-1;
    if(!employer || pub::Player::GetRep(PlayerId,playerRep)!=0 || !evac.once(event))return false;
    float rate=GetFactionEventRate(employer,FactionEventTrainDeliveryLate+int(event));
    if(!std::isfinite(rate))return false;
    if(rate==0)return true;
    float before=0,after=0;pub::Reputation::GetReputation(playerRep,employer,before);
    ApplyFactionReputationChange(playerRep,rate,employer,true);
    pub::Reputation::GetReputation(playerRep,employer,after);
    FmtStr text;text.begin_mad_lib(TrainEvacuation::Reputation);
    text.append_rep_group(employer);text.append_fmt_str(reputationValue(after-before));
    text.append_string(TrainEvacuation::LateText+unsigned(event));text.end_mad_lib();
    pub::Player::DisplayMissionMessage(PlayerId,text,static_cast<MissionMessageType>(2),false);
    FDUMP(0x100001,"TrainCourier: reputation player=%u employer=%u event=%s rate=%.6g delta=%.6g",
        PlayerId,employer,TrainEvacuation::eventName(event),rate,after-before);
    return true;
}
void evacuationNotice(unsigned textId,char const* family) {
    FmtStr text;text.begin_mad_lib(textId);text.end_mad_lib();
    pub::Player::DisplayMissionMessage(PlayerId,text,static_cast<MissionMessageType>(2),false);
    if(family)say(family);
}
int evacuationCommand(TrainEvacuation::Command command,TrainEvacuation::Status* out) {
    using namespace TrainEvacuation;
    out->phase=unsigned(evac.phase);
    if(!ready || bPendingDestroy || !swapped || !ship() ||
       state.stage==Stage::Complete || state.stage==Stage::Failed)return 0;
    if(command==Command::Critical) {
        if(out->ship!=ship())return 0;
        evac.phase=Phase::Emergency;return 1;
    }
    bool allowed=evac.phase==Phase::Onboard && state.stage!=Stage::TransferIn && state.stage!=Stage::TransferOut;
    out->available=allowed && !evacConfirm && !state.popup;out->ship=ship();
    if(command==Command::Query)return 1;
    if(command!=Command::Confirm || !out->available)return 0;
    FmtStr title,text;title.begin_mad_lib(Title);title.end_mad_lib();
    text.begin_mad_lib(activeOrder()?ConfirmLoaded:ConfirmEmpty);
    text.append_rep_group(employer);
    float loco=GetFactionEventRate(employer,FactionEventTrainLocomotiveLoss);
    float cargo=activeOrder()?GetFactionEventRate(employer,FactionEventTrainCargoLoss):0;
    text.append_fmt_str(reputationValue(loco));text.append_fmt_str(reputationValue(cargo));
    text.append_fmt_str(reputationValue(loco+cargo));
    text.append_fmt_str(reputationValue(GetFactionEventRate(employer,FactionEventTrainDeliveryLate)));
    text.end_mad_lib();
    evacConfirm=pub::Player::PopUpDialog(PlayerId,title,text,3)==0;
    return evacConfirm?1:0;
}
void answerEvacuation(unsigned answer) {
    evacConfirm=false;
    if(evac.phase!=TrainEvacuation::Phase::Onboard)return;
    if(answer!=1){evacuationNotice(TrainEvacuation::Cancelled,nullptr);return;}
    evac.phase=TrainEvacuation::Phase::Leaving;evacQueued=false;evacWaitingSpoken=false;
}
bool makeEvacuatedSolar() {
    if(evacSystem!=system())return false;
    auto* s=solar();if(!s)return false;
    if(s->bSpawned && s->SpaceObjId)pub::SpaceObj::Destroy(s->SpaceObjId,DESTROY_NORMAL);
    s->ArchetypeId=CreateID("tc_evacuated_locomotive");
    s->Position=evacPosition;s->SystemId=evacSystem;s->BaseId=transferBase;
    s->Faction=employer?employer:source.faction;s->Radius=0;
    std::memcpy(&s->Orientation,&evacOrientation,sizeof(Matrix));
    s->bSpawned=0;
    if(!SpawnMissionSolarRecord(s))return false;
    boarding=s->SpaceObjId;
    pub::SpaceObj::SetRelativeHealth(boarding,evacHealth);
    Packet p;p.player=PlayerId;p.operation=Operation::RecoverableSolar;p.launchSolar=boarding;
    if(!bridge || !bridge(&p) || p.result!=1) {
        unsigned old=boarding;boarding=0;s->bSpawned=0;pub::SpaceObj::Destroy(old,DESTROY_NORMAL);return false;
    }
    evacRestore=false;
    return true;
}
void clearLocomotiveCache() {
    auto module=GetModuleHandleA("Server.dll");
    auto transfer=module?reinterpret_cast<PlayerShipTransfer::Bridge>(GetProcAddress(module,"PlayerShipTransferBridge")):nullptr;
    PlayerShipTransfer::Packet p;p.player=PlayerId;p.operation=PlayerShipTransfer::Operation::ClearLocomotive;
    if(transfer)transfer(&p);
}
void detachEvacuatedSolar() {
    auto* systems=GetSystemInfos();
    auto found=systems->find(evacSystem);
    if(found!=systems->end()) {
        auto* info=&found->second;
        auto* objects=info->GetMissionObjects();
        objects->erase(std::remove(objects->begin(),objects->end(),boarding),objects->end());
    }
    MissionSolars.clear();RespawnSolars.clear();boarding=0;
}
void loseLocomotive(bool battle) {
    using namespace TrainEvacuation;
    if(evac.phase==Phase::Closed)return;
    bool cargo=activeOrder();
    evac.phase=Phase::Closed;evacConfirm=false;evac.remaining=0;failed=true;
    if(cargo)applyCourierReputation(CargoLost);
    applyCourierReputation(LocomotiveLost);
    // Retire uses the normal delayed cleanup queue and disables coupling.
    if(trailer) {
        request(Operation::Retire,trailer);
        trailer=0;
    }
    cargoPending=restoreCargo=false;
    if(boarding) {
        Packet parked;parked.player=PlayerId;parked.operation=Operation::ParkedSolar;parked.launchSolar=boarding;
        if(bridge)bridge(&parked);
        if(battle)pub::SpaceObj::Destroy(boarding,DESTROY_TYPE1);
    }
    detachEvacuatedSolar();clearLocomotiveCache();request(Operation::Release);
    NnPath.Reset();state.stage=Stage::Failed;
    evacuationNotice(battle?(cargo?BattleLoaded:BattleEmpty):(cargo?TimeoutLoaded:TimeoutEmpty),
        battle?(cargo?"te_battle_loaded":"te_battle_empty"):(cargo?"te_timeout_loaded":"te_timeout_empty"));
    OnMissionFail();
}
bool tickEvacuation(float dt) {
    using namespace TrainEvacuation;
    if(evac.phase==Phase::Onboard)return false;
    if(evac.phase==Phase::Closed)return true;
    if(evacDestroyPending) {
        if(boarding || makeEvacuatedSolar()){evacDestroyPending=false;loseLocomotive(true);}
        return true;
    }
    if(evac.phase==Phase::Away || evac.phase==Phase::Returning) {
        if(evac.tick(dt)){loseLocomotive(false);return true;}
        if(trailer) {
            Packet snapshot;snapshot.player=PlayerId;snapshot.operation=Operation::Snapshot;
            if(bridge && bridge(&snapshot) && snapshot.result==1) {
                savedCargo=snapshot.cargo;savedCargo.coupled=0;observeLoss(savedCargo);
            }
        }
        if(boarding && evacSystem==system()) {
            float health=evacHealth;
            if(pub::SpaceObj::GetRelativeHealth(boarding,health)==0) {
                evacHealth=health;
                if(health<=.05f){loseLocomotive(true);return true;}
                pub::SpaceObj::GetLocation(boarding,evacPosition,evacOrientation);
            } else {boarding=0;evacRestore=true;}
        }
        if(evacRestore && ship() && evacSystem==system())makeEvacuatedSolar();
        if(!evac.warned10 && evac.remaining<=10) {
            evac.warned10=evac.warned30=true;evacuationNotice(Warning10,"te_return_10");
        } else if(!evac.warned30 && evac.remaining<=30) {
            evac.warned30=true;evacuationNotice(Warning30,"te_return_30");
        }
        if(boarding) {
            Point target=source;target.systemId=evacSystem;target.position=evacPosition;
            if(objectiveObject!=boarding)objectObjective(ReturnObjective,target,boarding,"tc_boarding");
        }
        // Restore detached cargo without delivering it from the personal ship.
        if(restoreCargo && savedCargo.system==system()) {
            Packet p;p.player=PlayerId;p.operation=Operation::Restore;p.cargo=savedCargo;p.cargo.coupled=0;
            if(bridge && bridge(&p) && p.result==1){trailer=p.trailer;restoreCargo=false;}
        }
        return true;
    }
    bool emergency=evac.phase==Phase::Emergency;
    if(emergency && !evacCriticalSpoken) {
        evacCriticalSpoken=true;evacuationNotice(CriticalText,nullptr);
    }
    if(evacQueued)return true;
    if(!emergency && !evacWaitingSpoken) {
        evacWaitingSpoken=true;evacuationNotice(Waiting,nullptr);
    }
    // Finish a jump before touching its cargo or switching the player's ship.
    if(jumping && !resumeJump())return true;
    Packet prepare;prepare.player=PlayerId;prepare.operation=Operation::PrepareEvacuation;
    if(!bridge || !bridge(&prepare) || prepare.result!=1)return true;
    if(trailer) {
        Packet snapshot;snapshot.player=PlayerId;snapshot.operation=Operation::Snapshot;
        if(bridge && bridge(&snapshot) && snapshot.result==1)savedCargo=snapshot.cargo;
        savedCargo.coupled=0;
    }
    if(pub::SpaceObj::GetLocation(ship(),evacPosition,evacOrientation)!=0)return true;
    evacSystem=system();
    if(auto* sys=Universe::get_system(evacSystem)) {
        std::string name="tc_"+std::string(sys->GetNickname())+"_base";
        unsigned base=CreateID(name.c_str());
        if(Universe::get_base(base))transferBase=base;
    }
    auto module=GetModuleHandleA("Server.dll");
    auto transfer=module?reinterpret_cast<PlayerShipTransfer::Bridge>(GetProcAddress(module,"PlayerShipTransferBridge")):nullptr;
    PlayerShipTransfer::Packet p;p.player=PlayerId;p.operation=PlayerShipTransfer::Operation::QueueReturn;
    p.purpose=emergency?PlayerShipTransfer::Purpose::Emergency:PlayerShipTransfer::Purpose::Evacuate;
    if(transfer && transfer(&p) && p.result==1)evacQueued=true;
    return true;
}
int evacuationTransfer(PlayerShipTransfer::Packet* p,int phase) {
    using P=PlayerShipTransfer::Purpose;
    using E=TrainEvacuation::Phase;
    if(phase==0 && p->returning && evac.phase==E::Emergency)p->purpose=P::Emergency;
    bool departing=p->purpose==P::Evacuate || p->purpose==P::Emergency;
    bool reboarding=p->purpose==P::Reboard || (!p->returning && evac.canReturn());
    if(!departing && !reboarding)return -1;
    if(phase==0) {
        if(departing) {
            if(!swapped || (evac.phase!=E::Leaving && evac.phase!=E::Emergency))return 0;
            if(pub::SpaceObj::GetLocation(ship(),evacPosition,evacOrientation)!=0)return 0;
            evacSystem=system();
        } else {
            if(!canReboard(boarding))return 0;
            if(p->anchor?p->anchor!=boarding:(!transferBase || p->base!=transferBase))return 0;
            float health=0;
            if(pub::SpaceObj::GetRelativeHealth(boarding,health)!=0 || health<=.05f)return 0;
            p->purpose=P::Reboard;p->anchor=boarding;p->base=transferBase;p->locomotiveHealth=health;
        }
        p->position=evacPosition;p->orientation=evacOrientation;return 1;
    }
    if(phase==2) {
        evacQueued=false;
        if(departing && evac.phase!=E::Emergency) {
            evac.phase=E::Onboard;evacuationNotice(TrainEvacuation::TransferFailed,nullptr);
        } else if(reboarding && evac.phase!=E::Closed) {
            evac.phase=E::Away;evacuationNotice(TrainEvacuation::ReturnFailed,nullptr);
        }
        return 1;
    }
    if(phase!=1)return 0;
    if(PlayerState && PlayerState->ShipObject)PlayerState->ShipObject->RebindShip(p->target,p->ship.ShipArchetype);
    evacQueued=false;
    if(departing) {
        bool emergency=evac.phase==E::Emergency || p->purpose==P::Emergency;
        swapped=false;evacHealth=p->locomotiveHealth;
        evac.left();evacRestore=true;
        makeEvacuatedSolar();
        if(emergency) {
            evacDestroyPending=true;
            if(boarding){evacDestroyPending=false;loseLocomotive(true);}
        }
        else evacuationNotice(TrainEvacuation::EvacuatedText,"te_departed");
    } else {
        unsigned old=boarding;boarding=0;
        if(auto* s=solar())s->bSpawned=0;
        if(old)pub::SpaceObj::Destroy(old,DESTROY_NORMAL);
        Packet clear;clear.player=PlayerId;clear.operation=Operation::RecoverableSolar;
        if(bridge)bridge(&clear);
        swapped=true;evac.phase=E::Onboard;evac.remaining=0;evacCriticalSpoken=false;evacRestore=false;
        restoreObjective=true;objectiveObject=0;
        if(activeOrder()) {
            state.stage=Stage::Pickup;
            if(trailer) {
                Point target=source;target.systemId=evacSystem;target.position=evacPosition;
                Matrix orientation;pub::SpaceObj::GetLocation(trailer,target.position,orientation);
                objectObjective(config.recover,target,trailer);
            }
        }
        evacuationNotice(TrainEvacuation::ReturnedText,activeOrder()?"te_return_loaded":"te_return_empty");
    }
    return 1;
}
