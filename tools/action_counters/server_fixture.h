#include "player_action_stats.h"
#include "server_action_stats.h"
#include <algorithm>
#include <cassert>
#include <iomanip>
#include <locale>
#include <map>
#include <mutex>
#include <set>
#include <sstream>
#include <vector>
#include <string>
namespace Archetype {
enum {AClassRepairKit=1,AClassShieldBattery=2,AClassGun=3};
struct Equipment {int kind=0;int get_class_type()const{return kind;}};
inline Equipment kit{1},battery{2},gun{3};
inline Equipment* GetEquipment(unsigned id){return id==10?&kit:id==11?&battery:&gun;}
}
struct CEquip {
    Archetype::Equipment const* EquipArch() const{return &Archetype::gun;}
};
struct EquipDesc {unsigned ArchId=0;unsigned short Id=0;int Count=0;};
struct EquipmentList {
    std::vector<EquipDesc> Items;
    EquipDesc const* find_equipment_item(unsigned short id)const{
        for(auto const& e:Items)if(e.Id==id)return &e;return nullptr;
    }
};
struct PlayerData {unsigned client_id=1,current_base=10,ship_object_id=101;int cash=1000;EquipmentList equipment;};
struct PlayerDatabase {
    PlayerData players[3];
    bool is_valid(unsigned id)const{return id==1 || id==2;}
    bool is_valid_ship_owner(unsigned id,unsigned obj)const{return is_valid(id)&&obj==id+100;}
    PlayerData& operator[](unsigned id){assert(id<3);return players[id];}
} inline Players;
struct GoodInfo {unsigned ArchId=10;};
namespace GoodList {inline GoodInfo good;inline GoodInfo const* find_by_id(unsigned id){return id==50?&good:nullptr;}}
struct CObject {enum {ClassSimple=3,ClassEqObj=0x103};unsigned ObjectClass=ClassEqObj;};
struct CSimple:CObject {unsigned OwnerPlayer=0;};
struct CEqObj:CSimple {
    struct {CEquip equip;CEquip const* FindByID(unsigned)const{return &equip;}} EquipManager;
};
struct IObjRW {
    CEqObj object;unsigned id=0;
    float attitude=-1;IObjRW* target=nullptr;
    CObject const* cobject()const{return &object;}
    unsigned get_id()const{return id;}
    int get_attitude_towards(float& a,IObjRW const*)const{a=attitude;return 0;}
    int get_target(IObjRW*& t)const{t=target;return 0;}
    bool is_dying()const{return false;}
};
struct GameObject:IObjRW {CSimple* csimple(){return &object;}};
inline GameObject fixturePilot;
inline GameObject* Server_LookupGameObject(unsigned id){return id==101 ? &fixturePilot : nullptr;}
namespace SubObjectID {inline bool IsEquipID(unsigned id){return id>1;}}
struct DamageEntry {enum class SubObjFate{None,Destroyed,Separated,HealthProxy};unsigned short SubObjId=1;SubObjFate Fate=SubObjFate::None;};
struct DamageList {
    std::vector<DamageEntry> Entries;
    unsigned attacker=0;bool destroyed=false;
    unsigned get_inflictor_owner_player()const{return attacker;}
    unsigned get_inflictor_id()const{return 0;}
    bool is_destroyed()const{return destroyed;}
};
namespace Universe {inline bool get_system(unsigned id){return id==10;}inline bool get_base(unsigned id){return id==20;}}
inline bool SinglePlayer(){return true;}
