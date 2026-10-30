#include "server_action_stats.h"
#include "common_server.h"
#include "common_server_playerdb.h"
#include "common_goods.h"
#include "common_cobject.h"
#include "common_cequip.h"
#include "common_iface.h"
#include "common_misc.h"
#include "common_universe.h"
#include "server_cobject.h"
#include "server_gameobject.h"
#include "server_sysdb.h"
#include <algorithm>
#include <iomanip>
#include <locale>
#include <map>
#include <mutex>
#include <set>
#include <sstream>

namespace ServerActionStats {
namespace {
struct Trade {unsigned arch=0,count=0;bool buy=false;int beforeCount=0;double cash=0;};
struct Session {
    State state;
    unsigned long long epoch=0;
    Trade trade;
    double previousCredit=0;
    bool inFlight=false;
    std::set<unsigned> destroyed;
    std::set<unsigned long long> destroyedEquipment;
};
std::mutex mutex;
std::map<unsigned,Session> sessions;
unsigned long long generation=0;
bool registryAlive=true;
struct ShutdownGuard {~ShutdownGuard(){registryAlive=false;}} shutdownGuard;
int CountItems(PlayerData const& player,unsigned arch) {
    int count=0;
    for(auto const& equip:player.equipment.Items) if(equip.ArchId==arch && equip.Count>0)
        count+=(std::min)(equip.Count,1000000-count);
    return count;
}
void FinishTrade(Session& session,PlayerData const& player) {
    auto& t=session.trade;
    if(!t.arch || t.cash<=0) return;
    int delta=CountItems(player,t.arch)-t.beforeCount;
    int quantity=t.buy ? delta : -delta;
    if(quantity<=0 || static_cast<unsigned>(quantity)!=t.count) return;
    session.state.Add(t.buy ? Counter::BuyTransactions : Counter::SellTransactions);
    session.state.Add(t.buy ? Counter::UnitsBought : Counter::UnitsSold,quantity);
    session.state.Add(t.buy ? Counter::CreditsSpent : Counter::CreditsReceived,t.cash);
    t={};session.previousCredit=0;
}
}
void Load(unsigned player,State const& state) {
    std::lock_guard<std::mutex> lock(mutex);
    auto& s=sessions[player];s=Session();s.state=state;s.epoch=++generation;
}
void Clear(unsigned player) {if(!registryAlive)return;std::lock_guard<std::mutex> lock(mutex);sessions.erase(player);}
State Snapshot(unsigned player) {
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(player);return i==sessions.end() ? State() : i->second.state;
}
void Add(unsigned player,Counter counter,double amount) {
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(player);if(i!=sessions.end())i->second.state.Add(counter,amount);
}
void Save(FILE* file,State const& state) {
    std::ostringstream text;text.imbue(std::locale::classic());text<<std::setprecision(17);
    for(size_t i=0;i<PlayerActionStats::Count;++i)
        if(state.values[i]>0)text<<"action_counter = "<<PlayerActionStats::Name(static_cast<Counter>(i))
            <<", "<<state.values[i]<<'\n';
    auto data=text.str();fwrite(data.data(),1,data.size(),file); // Existing save writer checks ferror.
}
void BeginTrade(unsigned player,unsigned good,unsigned count,bool buy) {
    if(!Players.is_valid(player) || !count || count>1000000) return;
    auto const* info=GoodList::find_by_id(good);
    if(!info || !info->ArchId) return;
    auto const& p=Players[player];
    if(!p.current_base) return;
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(player);if(i==sessions.end())return;
    auto& s=i->second;
    s.trade={info->ArchId,count,buy,CountItems(p,info->ArchId),buy ? 0 : s.previousCredit};
    s.previousCredit=0;
}
void CashChanged(PlayerData const& p,int before) {
    double delta=double(p.cash)-before;
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(p.client_id);if(i==sessions.end())return;
    auto& s=i->second;
    s.previousCredit=delta>0 ? delta : 0;
    if(s.trade.arch && ((s.trade.buy && delta<0) || (!s.trade.buy && delta>0))) {
        s.trade.cash=std::abs(delta);FinishTrade(s,p);
    }
}
void InventoryChanged(PlayerData const& p) {
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(p.client_id);if(i!=sessions.end())FinishTrade(i->second,p);
}
void UsedItem(PlayerData const& p,unsigned short equipment,int count) {
    if(count<=0)return;
    auto const* item=p.equipment.find_equipment_item(equipment);
    if(!item)return;
    auto const* arch=Archetype::GetEquipment(item->ArchId);if(!arch)return;
    auto kind=arch->get_class_type();
    // The native repair-kit / shield-battery classes, not item nickname guesses.
    if(kind==Archetype::AClassRepairKit) Add(p.client_id,Counter::Nanobots,(std::min)(count,item->Count));
    if(kind==Archetype::AClassShieldBattery) Add(p.client_id,Counter::Batteries,(std::min)(count,item->Count));
}
void Damaged(IObjRW* object,DamageList const& damage) {
    if(!object || damage.Entries.empty())return;
    auto* simple=object->cobject();
    if(!simple || (simple->ObjectClass & CObject::ClassSimple)!=CObject::ClassSimple)return;
    unsigned victim=static_cast<CSimple const*>(simple)->OwnerPlayer;
    unsigned attacker=damage.get_inflictor_owner_player();
    if(!attacker) {
        auto* source=Server_LookupGameObject(damage.get_inflictor_id());
        if(source && source->csimple())attacker=source->csimple()->OwnerPlayer;
    }
    bool playerVictim=victim && Players.is_valid_ship_owner(victim,object->get_id());
    bool credited=attacker && Players.is_valid(attacker) && attacker!=victim;
    auto* pilot=credited ? Server_LookupGameObject(Players[attacker].ship_object_id) : nullptr;
    float attitude=0;
    bool enemy=pilot && object->get_attitude_towards(attitude,pilot)==0 && attitude<-.55f;
    IObjRW* ally=nullptr;
    if(enemy && damage.is_destroyed())object->get_target(ally);
    float allyAttitude=0;
    bool protectingAlly=ally && ally!=pilot && !ally->is_dying() &&
        ally->get_attitude_towards(allyAttitude,pilot)==0 && allyAttitude>.55f;
    if(playerVictim)Add(victim,Counter::DamageReceivedEvents);
    if(credited)Add(attacker,Counter::DamageDealtEvents);
    std::lock_guard<std::mutex> lock(mutex);
    if(playerVictim && damage.is_destroyed()) {
        auto i=sessions.find(victim);
        if(i!=sessions.end() && i->second.destroyed.insert(object->get_id()).second)i->second.state.Add(Counter::Deaths);
    }
    if(!credited)return;
    auto i=sessions.find(attacker);if(i==sessions.end())return;
    if(protectingAlly && i->second.destroyed.insert(object->get_id()).second)
        i->second.state.Add(Counter::AllyAttackersDestroyed);
    if(!enemy)return;
    auto const* equipped=(simple->ObjectClass & CObject::ClassEqObj)==CObject::ClassEqObj ? static_cast<CEqObj const*>(simple) : nullptr;
    if(!equipped)return;
    for(auto const& e:damage.Entries) if((e.Fate==DamageEntry::SubObjFate::Destroyed ||
        e.Fate==DamageEntry::SubObjFate::Separated) && SubObjectID::IsEquipID(e.SubObjId)) {
        auto* equip=equipped->EquipManager.FindByID(e.SubObjId);
        auto key=(static_cast<unsigned long long>(object->get_id())<<16)|e.SubObjId;
        if(equip && equip->EquipArch() && equip->EquipArch()->get_class_type()==Archetype::AClassGun &&
            i->second.destroyedEquipment.insert(key).second)
            i->second.state.Add(Counter::EnemyWeaponsDisabled);
    }
}
void Visited(unsigned player,unsigned object) {
    Add(player,Counter::Discoveries);
    if(Universe::get_system(object))Add(player,Counter::SystemsDiscovered);
    if(Universe::get_base(object))Add(player,Counter::BasesDiscovered);
}
void EnteredSpace(unsigned player,bool launched) {
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(player);if(i==sessions.end())return;
    auto& s=i->second;
    if(launched && !s.inFlight)s.state.Add(Counter::Launches);
    s.inFlight=true;s.trade={};s.previousCredit=0;s.destroyed.clear();s.destroyedEquipment.clear();
}
void Landed(unsigned player) {
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(player);if(i==sessions.end())return;
    auto& s=i->second;
    if(s.inFlight)s.state.Add(Counter::Landings);
    s.inFlight=false;s.trade={};s.previousCredit=0;
}
}

extern "C" __declspec(dllexport) int __cdecl PlayerActionStatsBridge(PlayerActionStats::Bridge* packet) {
    using namespace ServerActionStats;
    using namespace PlayerActionStats;
    if(!packet || packet->size!=sizeof(Bridge) || packet->version!=BridgeVersion || !SinglePlayer())return 0;
    std::lock_guard<std::mutex> lock(mutex);
    auto i=sessions.find(packet->player);if(i==sessions.end())return 0;
    auto& s=i->second;
    if(packet->operation==1) {
        if(packet->epoch!=s.epoch)return 0;
        for(size_t n=0;n<Count;++n)if(ClientOwned(static_cast<Counter>(n))) {
            double value=packet->state.values[n];
            if(!std::isfinite(value) || value<s.state.values[n] || value>Limit)return 0;
        }
        for(size_t n=0;n<Count;++n)if(ClientOwned(static_cast<Counter>(n)))s.state.values[n]=packet->state.values[n];
    } else if(packet->operation!=0)return 0;
    packet->epoch=s.epoch;packet->state=s.state;return 1;
}
