#include "player_train.h"
#include "hud_maneuvers.h"
#include "hud_target.h"
#include "player_behavior.h"
#include "player_spawn.h"
#include "game_options.h"
#include "globals.h"
#include "client_gameobj.h"
#include "client_objdb.h"
#include "cli_projectile_fx.h"
#include "nn_arrival_text.h"
#include "nn_button_control.h"
#include "menu_ui_init.h"
#include "tooltip_hover.h"
#include "port_config.h"
#include "common_text.h"
#include "common_misc.h"
#include "common_cobject.h"
#include "common_cequip.h"
#include "common_fuses.h" // Common.dll owns the vector<unsigned short> instantiation.
#include "../../Common/common_train.h"
#include "train_yard_bridge.h"
#include <windows.h>
#include <cwchar>
#include <vector>
#include <cstdlib>

namespace PlayerTrain {
namespace {
HUD_Maneuvers* panel=nullptr;
WinControl* button=nullptr;
TrainYard::Packet status;
ULONGLONG nextQuery=0;
int behavior=0;
TrainYard::BridgeFn bridge() {
    if(!SinglePlayer())return nullptr;
    auto module=GetModuleHandleW(L"Server.dll");
    return module ? reinterpret_cast<TrainYard::BridgeFn>(GetProcAddress(module,TrainYard::Export)):nullptr;
}
bool request(unsigned operation) {
    auto fn=bridge();if(!fn)return false;
    TrainYard::Packet packet;
    packet.player=GetPlayerConnectionId();packet.revision=GetGameSessionLoadRevision();packet.operation=operation;
    if(!fn(&packet))return false;
    status=packet;return true;
}
}
void Create(HUD_Maneuvers* hud) {
    panel=hud;nextQuery=0;
    float position[3]={0,.297f,0},half[3]={.0156f,.0157f,0};
    button=hud->CreateButtonControl("TrainCoupling","INTERFACE\\HUD\\EXTRA\\hud_train_couple.3db",
        nullptr,"ui_select_item",nullptr,position,nullptr,half,0,1,0,0,0x7f5200,0,0);
    button->SetProperty(1,1,0);
}
void Release(HUD_Maneuvers* hud) {
    if(panel!=hud)return;
    panel=nullptr;button=nullptr;nextQuery=0;status={};
}
bool HasButton(int current) {
    auto* player=static_cast<IObjRW*>(GetPlayerObjRW());
    return button && (current==0x13 || current==2) && bridge() && CmnTrain::IsLocomotive(player?HudShipOfObjRw(player):nullptr);
}
bool IsApproaching() {
    auto* player=static_cast<IObjRW*>(GetPlayerObjRW());
    return player && CmnTrain::IsCoupling(HudShipOfObjRw(player));
}
void CancelApproach() {
    if(IsApproaching()){request(4);nextQuery=0;}
}
void Update(HUD_Maneuvers* hud,int current) {
    if(hud!=panel || !button)return;
    behavior=current;
    bool show=HasButton(current);
    button->SetProperty(1,show?0:1,0);
    if(!show)return;
    ULONGLONG now=GetTickCount64();
    if(now>=nextQuery) {
        nextQuery=now+200;
        bool wasApproaching=status.approaching!=0;
        if(request(1) && wasApproaching && status.coupled) {
            PlayOrRewindUiSoundSlot(FindUiSoundSlot("ui_equip_mount04"));
            NnArrivalTextShowCaption(L"\u0421\u0446\u0435\u043f\u043a\u0430 \u0437\u0430\u043c\u043a\u043d\u0443\u0442\u0430");
        }
    }
    button->SetProperty(0xc,status.coupled || status.approaching ? 1:0,0);
}
void Layout(HUD_Maneuvers* hud,int current) {
    if(hud!=panel || !HasButton(current))return;
    float position[3]{};hud->CruiseButton->SetProperty(7,reinterpret_cast<uintptr_t>(position),0);
    position[0]-=.016f;hud->CruiseButton->SetProperty(6,reinterpret_cast<uintptr_t>(position),0);
    position[0]+=.032f;button->SetProperty(6,reinterpret_cast<uintptr_t>(position),0);
}
void Tooltip(NnButtonControl* control,FToolTipHoverInfo* info) {
    if(control!=button)return;
    bool ru=std::strcmp(PortLanguage(),"ru")==0;
    const wchar_t* caption=status.approaching ? (ru?L"\u041e\u0442\u043c\u0435\u043d\u0438\u0442\u044c \u0441\u0446\u0435\u043f\u043a\u0443":L"Cancel coupling") :
        status.coupled ? (ru?L"\u041e\u0442\u0446\u0435\u043f\u0438\u0442\u044c \u0432\u0430\u0433\u043e\u043d\u044b":L"Uncouple wagons") :
        (ru?L"\u0421\u0446\u0435\u043f\u0438\u0442\u044c \u0432\u0430\u0433\u043e\u043d\u044b (15 \u043c, 2 \u043c/\u0441)":L"Couple wagons (15 m, 2 m/s)");
    info->CaptionW=_wcsdup(caption);info->CaptionCapacity=static_cast<unsigned>(wcslen(caption)+1);info->AuxField=0;
}
bool Click(unsigned long clicked) {
    if(!button || clicked!=reinterpret_cast<unsigned long>(button))return false;
    if(!HasButton(behavior))return true;
    if(!request(0))return true;
    bool detach=status.coupled!=0;
    bool cancel=status.approaching!=0;
    if(!detach && !cancel) {
        if(behavior==2 && !panel->RequestManeuver(0x13,false))return true;
        SetPlayerThrottle(0);ClearMouseFlightSteering();
    }
    if(!request(cancel?4:detach?3:2))return true;
    if(status.result==1 && detach && !cancel)
        PlayOrRewindUiSoundSlot(FindUiSoundSlot("ui_equip_mount02"));
    wchar_t message[180];
    if(status.result==1)wcscpy_s(message,cancel ? L"\u0421\u0446\u0435\u043f\u043a\u0430 \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430" : detach ? L"\u0412\u0430\u0433\u043e\u043d\u044b \u043e\u0442\u0446\u0435\u043f\u043b\u0435\u043d\u044b" : L"\u041f\u043e\u0434\u0445\u043e\u0434 \u043a \u0441\u0446\u0435\u043f\u043a\u0435");
    else if(status.result==-4)swprintf_s(message,L"\u041f\u043e\u0434\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0446\u0435\u043f\u043a\u0443 \u043b\u043e\u043a\u043e\u043c\u043e\u0442\u0438\u0432\u0430 \u043a \u043f\u0435\u0440\u0432\u043e\u043c\u0443 \u0432\u0430\u0433\u043e\u043d\u0443: \u043d\u0435 \u0434\u0430\u043b\u044c\u0448\u0435 %.0f \u043c",TrainYard::CaptureDistance);
    else if(status.result==-5)wcscpy_s(message,L"\u0421\u043d\u0438\u0437\u044c\u0442\u0435 \u0441\u043a\u043e\u0440\u043e\u0441\u0442\u044c \u0441\u0431\u043b\u0438\u0436\u0435\u043d\u0438\u044f \u0434\u043e 2 \u043c/\u0441");
    else if(status.result==-6)wcscpy_s(message,L"\u0412\u044b\u0440\u043e\u0432\u043d\u044f\u0439\u0442\u0435 \u043b\u043e\u043a\u043e\u043c\u043e\u0442\u0438\u0432 \u043f\u043e \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044e \u0432\u0430\u0433\u043e\u043d\u043e\u0432");
    else if(status.result==-7)wcscpy_s(message,L"\u0414\u043b\u044f \u0441\u0446\u0435\u043f\u043a\u0438 \u0438 \u0440\u0430\u0441\u0446\u0435\u043f\u043a\u0438 \u043e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u0435 \u043a\u0440\u0443\u0438\u0437 \u0438 \u0430\u0432\u0442\u043e\u043f\u0438\u043b\u043e\u0442");
    else wcscpy_s(message,L"\u0412\u0430\u0433\u043e\u043d\u044b \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b");
    NnArrivalTextShowCaption(message);nextQuery=0;return true;
}
void FireCoupled(IObjAffect* host,unsigned short const* ids,unsigned count,Vector const* aim,int player) {
    if(!SinglePlayer() || !host || !aim ||
       (player!=-1 && player!=static_cast<int>(GetPlayerConnectionId())))return;
    auto* client=static_cast<FClientEquippedObj*>(host);
    auto* object=client->Object;
    if(!CmnTrain::IsLocomotive(object))return;
    auto* loco=static_cast<CShip*>(object);
    auto* own=static_cast<IObjRW*>(GetPlayerObjRW());
    if(!own || own->cobject()!=loco || loco->is_cruise_active() ||
       loco->is_using_tradelane() || loco->is_launching())return;
    // Missile-only groups do not trigger the train's gun battery.
    bool guns=count==0;
    for(unsigned i=0;i<count;++i)guns|=CEGun::cast(loco->EquipManager.FindByID(ids[i]))!=nullptr;
    if(!guns)return;
    auto* tail=static_cast<CShip*>(CmnTrain::Trailer(loco));
    auto* tailClient=tail?ClientObjDb_FindByCObject(tail):nullptr;
    if(!tailClient || tailClient->is_dying())return;
    std::vector<unsigned short> battery;
    CEquipTraverser walk(EquipTypeGun);
    while(auto* item=tail->EquipManager.Traverse(walk)) {
        auto* gun=CEGun::cast(item);
        if(!gun || !gun->IsActive() || !gun->IsFunctioning())continue;
        gun->SetTargetPoint(*aim);battery.push_back(gun->GetID());
    }
    if(!battery.empty())CliShipFireWeapons(static_cast<IObjAffect*>(tailClient),battery.data(),
        static_cast<unsigned>(battery.size()),aim,player);
}
}
