"""Check Health damage edges, manual/locked visibility and the production warning filter."""
import os
import subprocess
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/health_damage_check'
out.mkdir(parents=True, exist_ok=True)

def function(file, signature):
    source = (repo / 'src/freelancer/Client' / file).read_text()
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


code = r'''
#include <cassert>
#include <cstdio>
#include <limits>
#include "health_window_state.h"
constexpr unsigned EquipTypeShield=0x100, EquipTypeShieldGen=0x200;
unsigned CreateID(char const* name){unsigned value=2166136261u;while(*name)value=(value^static_cast<unsigned char>(*name++))*16777619u;return value;}
'''
code += function('hud_health.cpp', 'bool HealthIsDamageMessage(')
code += function('hud_health.cpp', 'bool HealthTracksEquipment(')
code += r'''
int main(){
    HealthDamageState tracker;
    auto sample=[&](double hp,bool vulnerable=false,bool destroyed=false){
        tracker.Begin();tracker.Sample(1,hp,vulnerable,destroyed);return tracker.Finish();
    };
    assert(!sample(1));assert(!sample(.99));assert(!sample(.751));
    assert(sample(.75));assert(!sample(.6));assert(sample(.5));
    assert(!sample(.25));assert(sample(.249));
    for(int frame=0;frame<20;++frame)assert(!sample(.249)); // Critical pulse is not new damage.
    assert(!sample(.8));assert(sample(.75)); // Repairs re-arm the band transition.
    assert(sample(0));assert(!sample(0));
    tracker.Begin();assert(!tracker.Finish()); // Already destroyed, then removed.
    tracker.Reset();assert(!sample(.1)); // Loading a damaged ship is only a baseline.
    tracker.Begin();assert(tracker.Finish()); // An attached part disappears.
    tracker.Begin();assert(!tracker.Finish());
    tracker.Reset();assert(!sample(1,true));assert(!sample(.74,true));
    assert(sample(.5,true)); // Vulnerable orange baseline doesn't falsely trigger at 75%.
    assert(!sample(std::numeric_limits<double>::quiet_NaN(),true));
    assert(sample(.49,true,true));
    tracker.Reset();tracker.Begin();tracker.Sample(0x10001,1);tracker.Sample(0x20001,1);assert(!tracker.Finish());
    tracker.Begin();tracker.Sample(0x10001,1);tracker.Sample(0x20001,.5);assert(tracker.Finish()); // Distinct group/equipment IDs.
    tracker.Begin();tracker.Sample(0x10001,1);tracker.Sample(0x20001,.5);tracker.Sample(0x20002,.1);assert(!tracker.Finish());
    puts("PASS: colour thresholds, repair re-arm, critical pulse stability, destruction/removal, ship reset and independent part IDs");
    HealthWindowState window;window.ToggleOpen();assert(!window.open);
    window.Damage();assert(window.open);window.ToggleOpen();assert(!window.open);
    window.SetLocked(true);window.Damage();assert(!window.open);
    window.ToggleOpen();assert(window.open); // Manual open still works when locked.
    window.ToggleOpen();window.SetLocked(false);assert(!window.open); // No replay.
    window.Damage();assert(window.open);
    window.Opened();window.SetLocked(true);assert(window.open); // Lock does not close a visible window.
    window.ToggleOpen();assert(!window.open);
    window.SetLocked(false);window.Damage();assert(window.open); // Desired state can change during a close animation.
    window.SetLocked(true);assert(!window.open); // Cancel an auto-open queued during closing.
    window.ToggleOpen();window.SetLocked(true);assert(window.open); // A pending manual open is preserved.
    puts("PASS: fresh damage reopens, lock suppresses, manual controls always work, unlock doesn't replay warnings");
    for(auto name:{"hull_breach_imminent","engine_critical","weapon_expired","cargo_expired","thruster_destroyed","engine_destroyed","mine_dropper_destroyed","countermeasure_dropper_destroyed","gun_destroyed","launcher_destroyed","turret_destroyed","radiation_damage_detected"})
        assert(HealthIsDamageMessage(CreateID(name)));
    for(auto name:{"shield_destroyed","nnv_shield_failed","dock_granted","nnv_shield_restored","nnv_shield_activated","nnv_shield_deactivated","incoming_missile","nnv_tractor_failure","repair_complete",""})
        assert(!HealthIsDamageMessage(CreateID(name)));
    puts("PASS: damage warning filter rejects every shield message, including failure and destruction");
    HealthDamageState shields;
    auto observeEquipment=[&](double hp,bool shieldPresent=true){
        shields.Begin();
        for(unsigned type:{0x20u,0x40u,0x80u,0x100u,0x200u,0x400u,0x800u,0x1000u}){
            bool const shield=type==EquipTypeShield || type==EquipTypeShieldGen;
            if(shield && !shieldPresent)continue;
            if(HealthTracksEquipment(type))shields.Sample(type,shield?hp:1.0);
        }
        return shields.Finish();
    };
    assert(!HealthTracksEquipment(EquipTypeShield));assert(!HealthTracksEquipment(EquipTypeShieldGen));
    for(unsigned type:{0x20u,0x40u,0x80u,0x400u,0x800u,0x1000u})assert(HealthTracksEquipment(type));
    assert(!observeEquipment(1));assert(!observeEquipment(.75));assert(!observeEquipment(.5));
    assert(!observeEquipment(.1));assert(!observeEquipment(0));assert(!observeEquipment(0,false));
    assert(!observeEquipment(1));
    puts("PASS: shield depletion, exhaustion, destruction/removal and recharge cannot trigger Health; physical equipment still monitored");
}
'''
(out / 'check.cpp').write_text(code)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include'] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                '/EHsc', '/MT', '/I'+str(repo / 'src/freelancer/Client'), 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)
