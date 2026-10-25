"""Compile the production session-state functions against a recording server stub."""
import os
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/targeting_save_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/game_options.cpp').read_text()
session = source[source.index('namespace\n{'):]
fixture = r'''
#include <cassert>
#include <cstring>
#include <cstdio>
#include "../../freelancer/Client/targeting_window_state.h"
struct RecordingServer {
    unsigned word = 0;
    unsigned sends = 0;
    void SetInterfaceState(unsigned id, unsigned char* data, int size) {
        assert(id == 7 && size == 4);
        memcpy(&word, data, 4);
        ++sends;
    }
} server;
RecordingServer* G_Server = &server;
unsigned GetPlayerConnectionId() { return 7; }
'''
checks = r'''
int main() {
    assert(GetSavedTargetingProjection() == 0);
    assert(GetSavedTargetingAutoselect() && !GetSavedTargetingWindowLocked());
    for (unsigned native = 0; native < 16; ++native) {
        for (unsigned previous = 0; previous < 4; ++previous) {
            for (unsigned mode = 0; mode < 4; ++mode) {
                const unsigned untouched = 0xa5a50000u | native;
                AssignGameSessionFlags(untouched | (previous << 4));
                const auto before = server.sends;
                SetSavedTargetingProjection(mode);
                assert(server.sends == before + 1);
                assert(server.word == (untouched | (mode << 4)));
                const auto saved = server.word;
                for (unsigned bit = 1; bit <= 8; bit <<= 1) {
                    SetGameSessionFlags(bit, true);
                    assert(TestGameSessionFlags(bit));
                    assert(GetSavedTargetingProjection() == mode);
                    SetGameSessionFlags(bit, false);
                    assert(!TestGameSessionFlags(bit));
                    assert(GetSavedTargetingProjection() == mode);
                }
                // Server load overwrites the word without broadcasting it back.
                const auto sends = server.sends;
                AssignGameSessionFlags(saved);
                assert(server.sends == sends);
                assert(GetSavedTargetingProjection() == mode);
                AssignGameSessionFlags(3); // Loading a legacy save after any mode.
                assert(GetSavedTargetingProjection() == 0);
            }
        }
    }
    const auto sends = server.sends;
    SetSavedTargetingProjection(4);
    SetSavedTargetingProjection(~0u);
    assert(server.sends == sends && GetSavedTargetingProjection() == 0);
    G_Server = nullptr;
    SetSavedTargetingProjection(3);
    assert(GetSavedTargetingProjection() == 3 && server.sends == sends);
    G_Server = &server;
    for (unsigned native=0; native<16; ++native) for(unsigned mode=0; mode<4; ++mode)
    for(unsigned initial=0; initial<4; ++initial) for(unsigned chosen=0; chosen<4; ++chosen) {
        unsigned const untouched=0xa5a50000u | native | (mode<<4);
        AssignGameSessionFlags(untouched | (initial<<6));
        bool const automatic=(chosen&1)==0, locked=(chosen&2)!=0;
        auto const before=server.sends;
        SetSavedTargetingAutoselect(automatic);
        assert(server.sends==before+1);
        assert(server.word==(untouched | ((initial&2)<<6) | ((chosen&1)<<6)));
        SetSavedTargetingWindowLocked(locked);
        assert(server.sends==before+2 && server.word==(untouched | (chosen<<6)));
        auto const saved=server.word;
        assert(GetSavedTargetingProjection()==mode);
        assert(GetSavedTargetingAutoselect()==automatic && GetSavedTargetingWindowLocked()==locked);
        for(unsigned bit=1;bit<=8;bit<<=1) {
            SetGameSessionFlags(bit,true);SetGameSessionFlags(bit,false);
            assert(GetSavedTargetingAutoselect()==automatic && GetSavedTargetingWindowLocked()==locked);
        }
        SetSavedTargetingProjection((mode+1)%4);
        assert(GetSavedTargetingAutoselect()==automatic && GetSavedTargetingWindowLocked()==locked);
        auto const beforeLoad=server.sends;
        AssignGameSessionFlags(3); // Load a different legacy player, then restore this one.
        assert(GetSavedTargetingAutoselect() && !GetSavedTargetingWindowLocked());
        AssignGameSessionFlags(saved);
        assert(server.sends==beforeLoad);
        assert(GetSavedTargetingAutoselect()==automatic && GetSavedTargetingWindowLocked()==locked);
        assert(GetSavedTargetingProjection()==mode);
    }
    assert(!GetSavedHealthWindowLocked());
    for(unsigned bits=0;bits<256;++bits)for(unsigned locked=0;locked<2;++locked){
        unsigned const original=0xa5a50000u | bits;
        AssignGameSessionFlags(original);
        auto const before=server.sends;
        SetSavedHealthWindowLocked(locked!=0);
        assert(server.sends==before+1 && server.word==(original | (locked<<8)));
        auto const saved=server.word;
        SetSavedTargetingAutoselect(false);SetSavedTargetingWindowLocked(true);SetSavedTargetingProjection(3);
        SetGameSessionFlags(2,false);
        assert(GetSavedHealthWindowLocked()==(locked!=0));
        AssignGameSessionFlags(3);assert(!GetSavedHealthWindowLocked());
        AssignGameSessionFlags(saved);assert(GetSavedHealthWindowLocked()==(locked!=0));
        SetSavedHealthWindowLocked(false);assert(server.word==original);
    }
    puts("PASS: Health lock bit round trips, survives all other HUD changes, preserves other bits and defaults unlocked in legacy saves");
    for (unsigned options=0; options<128; ++options) for(unsigned group=0;group<6;++group) {
        AssignGameSessionFlags(0xa5000003u);
        bool const healthOpen=(options&1)!=0, targetOpen=(options&2)!=0;
        bool const healthLock=(options&4)!=0, targetLock=(options&8)!=0;
        bool const left=(options&16)!=0;
        unsigned const projection=(options>>5)&3;
        SetSavedHealthWindowLocked(healthLock);SetSavedTargetingWindowLocked(targetLock);
        SetSavedHealthWindowOpen(healthOpen);SetSavedTargetingWindowOpen(targetOpen);
        SetSavedHealthViewLeft(left);SetSavedTargetingProjection(projection);SetSavedWeaponGroup(group);
        assert(GetSavedHealthWindowOpen()==healthOpen&&GetSavedTargetingWindowOpen()==targetOpen);
        assert(GetSavedHealthViewLeft()==left&&GetSavedWeaponGroup()==group);
        auto const saved=server.word;
        assert((saved&0xfffe000fu)==0xa5000003u);
        auto const sent=server.sends;
        SetSavedHealthWindowOpen(healthOpen);SetSavedTargetingWindowOpen(targetOpen);
        SetSavedHealthViewLeft(left);SetSavedWeaponGroup(group);
        assert(server.sends==sent); // Reconciliation every frame never floods the server.
        ToggleAuxiliaryHudWindowsMinimized();assert(AreAuxiliaryHudWindowsMinimized());
        assert(GetSavedHealthWindowOpen()==healthOpen&&GetSavedTargetingWindowOpen()==targetOpen);
        ToggleAuxiliaryHudWindowsMinimized();assert(!AreAuxiliaryHudWindowsMinimized());
        assert(server.sends==sent&&server.word==saved);
        ToggleAuxiliaryHudWindowsMinimized();
        unsigned const revision=GetGameSessionLoadRevision();
        AssignGameSessionFlags(3);
        assert(GetGameSessionLoadRevision()==revision+1&&!AreAuxiliaryHudWindowsMinimized());
        assert(GetSavedHealthWindowOpen()&&GetSavedTargetingWindowOpen());
        assert(!GetSavedHealthViewLeft()&&GetSavedWeaponGroup()==0);
        AssignGameSessionFlags(saved);
        assert(server.sends==sent);
        assert(GetSavedHealthWindowOpen()==healthOpen&&GetSavedTargetingWindowOpen()==targetOpen);
        assert(GetSavedHealthWindowLocked()==healthLock&&GetSavedTargetingWindowLocked()==targetLock);
        assert(GetSavedHealthViewLeft()==left&&GetSavedTargetingProjection()==projection&&GetSavedWeaponGroup()==group);
        TargetingWindowState target;
        target.Restore(targetOpen,targetLock);
        target.Observe(0);target.Observe(0);assert(!target.open); // Empty/waypoint never opens.
        target.Observe(17);assert(target.open==targetOpen); // First real target uses saved preference.
        target.Observe(17);assert(target.open==targetOpen);
        target.Observe(0);assert(!target.open);
        target.Observe(18);assert(target.open==!targetLock); // Subsequent targets use auto-open.
        target.ToggleOpen();assert(target.open==targetLock); // Manual override remains possible.
        target.Restore(!targetOpen,!targetLock);target.Observe(19);assert(target.open==!targetOpen);
    }
    AssignGameSessionFlags(3|0x180u); // Old locked saves predate visibility markers.
    assert(!GetSavedHealthWindowOpen()&&!GetSavedTargetingWindowOpen());
    SetSavedHealthWindowOpen(true);SetSavedTargetingWindowOpen(true);
    assert(GetSavedHealthWindowOpen()&&GetSavedTargetingWindowOpen()); // Lock must not force manual windows closed.
    AssignGameSessionFlags(3|(7u<<12));assert(GetSavedWeaponGroup()==0);
    SetSavedWeaponGroup(0);assert((server.word&(7u<<12))==0);
    auto const invalidSends=server.sends;
    SetSavedWeaponGroup(6);SetSavedWeaponGroup(~0u);assert(server.sends==invalidSends);
    puts("PASS: 768 complete UI save/load combinations, six weapon groups, no per-frame writes, legacy saves, player reload, first-target restoration and temporary minimize/restore");
    auto const offlineSends=server.sends;
    G_Server=nullptr;
    SetSavedTargetingAutoselect(false);SetSavedTargetingWindowLocked(true);
    assert(!GetSavedTargetingAutoselect() && GetSavedTargetingWindowLocked() && server.sends==offlineSends);
    puts("PASS: projection/autoselect/lock round trips, all toggle transitions, legacy defaults, native/unrelated bits, live player reload, single broadcasts and offline updates");
}
'''
(out / 'check.cpp').write_text(fixture + session + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include'] + [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] + [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)
