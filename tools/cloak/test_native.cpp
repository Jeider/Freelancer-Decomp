#include "common_cequip.h"
#include "common_cobject.h"
#include "common_ini.h"
#include "dacom.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <limits>
#include <new>
#include <cstdarg>

static void __cdecl TestDump(int, char const* format, ...)
{
    va_list args; va_start(args,format); std::vfprintf(stderr,format,args); va_end(args);
    std::fputc('\n',stderr);
}
struct BeamFixture : Archetype::Munition { static void Set() { BEAM_ARCH_INDEX=0; } };

static void Parse(Archetype::Root& arch, char const* text)
{
    INI_Reader reader;
    assert(reader.open_memory(text, unsigned(std::strlen(text))) && reader.read_header());
    while (reader.read_value()) assert(arch.read(reader));
}
static bool Near(float a, float b) { return std::fabs(a-b) < .0001f; }
struct Observer : INotify
{
    int on = 0, off = 0;
    void notify(Event event, void*) override
    {
        if (event == EquipActivating) ++on;
        if (event == EquipDeactivating) ++off;
    }
};
int main(int argc, char** argv)
{
    FDUMP=TestDump;
    assert(LoadLibraryA("x86math.dll"));
    assert(argc==2);
    BeamFixture::Set();
    assert(Archetype::LoadEquipment(argv[1],false,nullptr)==2);
    auto* inherited=static_cast<Archetype::CloakingDevice*>(Archetype::GetEquipment(CreateID("cloak_test_child")));
    assert(inherited && inherited->GetSettings().enabled && !inherited->GetSettings().defaultState);
    assert(inherited->GetSettings().duration==-1 && inherited->GetSettings().cooldown==20);
    Archetype::CloakingDevice arch;
    Parse(arch, "[CloakingDevice]\nnickname=cloak_test\nhp_type=hp_hardware_special_1\nhit_pts=100\ndefault_state=false\ncloak_duration=3\n"
                "cooldown_time=4\ntoggle_cooldown=0.3\ncloakin_time=2\ncloakout_time=1\n");
    assert(arch.GetSettings().enabled && !arch.GetSettings().defaultState);
    Archetype::CloakingDevice copy(arch), assigned;
    assigned=arch; assigned=assigned;
    assert(copy.GetSettings().duration==3 && assigned.GetSettings().cooldown==4);
    Archetype::CloakingDevice legacy;
    assigned.redefine(legacy); assert(!assigned.GetSettings().enabled);
    alignas(Archetype::CloakingDevice) unsigned char storage[sizeof(Archetype::CloakingDevice)];
    auto* reused=new(storage) Archetype::CloakingDevice(arch);
    reused->~CloakingDevice(); reused=new(storage) Archetype::CloakingDevice;
    assert(!reused->GetSettings().enabled); reused->~CloakingDevice();

    CECloakingDevice device(nullptr,1,&arch,false);
    Observer observer; device.ConnectServerEquip(&observer);
    assert(!device.IsActive() && device.cloak_percent()==0 && device.CanToggle());
    assert(device.Activate(true)); assert(observer.on==1);
    assert(!device.CanToggle());
    device.Update(.5f,0);
    assert(device.Activate(false)); // Rejected off returns the actual active state.
    assert(observer.off==0 && Near(float(device.cloak_percent()),.5f));
    device.Update(.5f,0); assert(device.CanToggle() && device.cloak_percent()==1);
    assert(device.GetDurationRemaining()==3);
    device.Update(2.5f,0); assert(device.IsActive() && Near(device.GetDurationRemaining(),.5f));
    device.Update(.5f,0); assert(!device.IsActive() && observer.off==1 && !device.CanToggle());
    assert(!device.Activate(true)); assert(observer.on==1);
    device.Update(2,0); assert(device.cloak_percent()==0 && device.GetCooldownRemaining()==4);
    device.Update(3.5f,0); assert(!device.Activate(true));
    device.Update(.5f,0); assert(device.CanToggle() && device.Activate(true));
    // Manual cancellation gives the same full recharge, after appearing.
    device.Update(1,0); assert(!device.Activate(false)); device.Update(2,0);
    assert(device.GetCooldownRemaining()==4);
    device.Update(std::numeric_limits<float>::quiet_NaN(),0);
    device.Update(-4,0); assert(device.GetCooldownRemaining()==4);
    device.Update(4,0); device.Activate(true);
    // One large frame crosses all four phases without double ticking.
    device.Update(10,0); assert(!device.IsActive() && device.CanToggle());
    device.NotifyDisconnecting(&observer);

    Archetype::CloakingDevice unlimited;
    Parse(unlimited,"[CloakingDevice]\nhp_type=hp_hardware_special_1\nhit_pts=100\ndefault_state=false\ncloak_duration=-1\ncooldown_time=0\n"
                    "toggle_cooldown=0.3\ncloakin_time=0\ncloakout_time=0\n");
    CECloakingDevice infinite(nullptr,2,&unlimited,false);
    infinite.Activate(true); infinite.Update(0,0);
    assert(!infinite.CanToggle()); infinite.Update(10000,0);
    assert(infinite.IsActive() && infinite.GetDurationRemaining()==-1);
    infinite.Activate(false); infinite.Update(0,0); assert(!infinite.CanToggle());
    infinite.Update(.3f,0); assert(infinite.CanToggle());
    Parse(unlimited,"[CloakingDevice]\ncloak_duration=0\ntoggle_cooldown=0\n");
    infinite.Activate(true); infinite.Update(0,0); assert(!infinite.IsActive() && infinite.CanToggle());
    Parse(unlimited,"[CloakingDevice]\ndefault_state=true\ncloak_duration=-1\n");
    CECloakingDevice startsOn(nullptr,3,&unlimited,false);
    assert(startsOn.IsActive() && startsOn.cloak_percent()==1);

    CShip ship; ship.OwnerPlayer=1;
    CECloakingDevice::LoadCooldowns(1,{});
    {
        CECloakingDevice saved(nullptr,4,&arch,false); saved.Owner=&ship;
        saved.RegisterServerState(); saved.Activate(true); saved.Update(1,0);
        auto snapshot=CECloakingDevice::SavedCooldowns(1);
        assert(snapshot[arch.get_id()]==6);
        saved.Activate(false); saved.Update(3,0);
        snapshot=CECloakingDevice::SavedCooldowns(1); assert(snapshot[arch.get_id()]==3);
    }
    {
        CECloakingDevice loaded(nullptr,4,&arch,false); loaded.Owner=&ship;
        loaded.RegisterServerState(); assert(!loaded.IsActive() && loaded.GetCooldownRemaining()==3);
        loaded.RegisterServerState(); loaded.Update(3,0); assert(loaded.CanToggle());
        loaded.Activate(true); loaded.Update(.5f,0);
        loaded.Destroy(); loaded.Update(0,0);
        assert(!loaded.IsActive() && ship.CloakPercent==0 && !loaded.CanToggle());
    }
    CECloakingDevice::LoadCooldowns(1,{});
    assert(CECloakingDevice::SavedCooldowns(1).empty());
    // Server rejection/correction can reverse a predicted animation; duplicate
    // authoritative states must not reset its progress or duration.
    CECloakingDevice replica(nullptr,5,&arch,false);
    replica.Activate(true); replica.Update(.5f,0);
    replica.ApplyRemoteState(false); replica.Update(.5f,0);
    float percent=float(replica.cloak_percent());
    replica.ApplyRemoteState(false); assert(float(replica.cloak_percent())==percent);
    replica.Update(10,0); replica.ApplyRemoteState(true); replica.Update(2,0);
    float remaining=replica.GetDurationRemaining(); replica.ApplyRemoteState(true);
    assert(replica.GetDurationRemaining()==remaining);
    replica.Update(100,0); assert(replica.IsActive()); // Waits for server expiry.
    replica.ApplyRemoteState(false); replica.Update(2,0); assert(!replica.IsActive());
    CECloakingDevice old(nullptr,6,&legacy,false); assert(old.IsActive());
    std::puts("PASS: native cloak parsing, fades, expiry, cooldown, persistence, destruction and correction");
    return 0;
}
