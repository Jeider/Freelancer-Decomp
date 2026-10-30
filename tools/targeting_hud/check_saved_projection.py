"""Exercise production global HUD preferences against a profile store and recording server."""
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
#include <cstdlib>
#include <string>
constexpr int MAX_PATH=260;
std::string profile;
unsigned profileWrites=0;
bool writeOk=true;
bool GetUserDataPath(char* out){strcpy_s(out,MAX_PATH,"mock-user");return true;}
unsigned GetLastError(){return 5;}
#define FDUMP(...) ((void)0)
unsigned GetPrivateProfileStringA(char const*,char const*,char const*,char* out,unsigned size,char const*){
    strcpy_s(out,size,profile.c_str());return unsigned(profile.size());
}
bool WritePrivateProfileStringA(char const*,char const*,char const* text,char const* path){
    assert(strcmp(path,"mock-user\\hud_preferences.ini")==0);
    if(!writeOk)return false; profile=text;++profileWrites;return true;
}
struct RecordingServer {
    unsigned word=0,sends=0;
    void SetInterfaceState(unsigned,unsigned char* data,int size){assert(size==4);memcpy(&word,data,4);++sends;}
} server;
RecordingServer* G_Server=&server;
unsigned GetPlayerConnectionId(){return 7;}
'''
checks = r'''
void RestartProfile(){GHudLoaded=GHudStored=false;GHudPreferences=0;GHudPath[0]=0;}
int main(){
    assert(GetShowWeaponGroups() && GetSavedRadarAutoMode()==0);
    assert(profileWrites==0); // Reading main-menu defaults must not suppress migration.
    AssignGameSessionFlags(3|(2u<<20)|(1u<<8)|(2u<<4));
    assert(GetSavedRadarAutoMode()==2 && GetSavedHealthWindowLocked() && GetSavedTargetingProjection()==2);
    assert(profileWrites==1 && server.sends==0);
    AssignGameSessionFlags(0); // Another character cannot overwrite global choices.
    assert(GetSavedRadarAutoMode()==2 && GetSavedHealthWindowLocked());
    for(unsigned mode=0;mode<3;++mode) for(unsigned projection=0;projection<4;++projection)
    for(unsigned group=0;group<6;++group) for(unsigned open=0;open<2;++open){
        SetSavedRadarAutoMode(mode);SetSavedTargetingProjection(projection);SetSavedWeaponGroup(group);
        SetSavedHealthWindowLocked(open!=0);SetSavedHealthWindowOpen(open!=0);SetSavedHealthViewLeft(open!=0);
        SetSavedTargetingWindowLocked(open!=0);SetSavedTargetingWindowOpen(open!=0);SetSavedTargetingAutoselect(open!=0);
        SetSavedRadarEnabled(open!=0);SetSavedRadarRange(mode);SetSavedAutoTurretsEnabled(open!=0);
        SetSavedAutoTurretReserve(group*15);SetShowWeaponGroups(open!=0);
        unsigned const writes=profileWrites;
        SetSavedHealthWindowOpen(open!=0);SetSavedRadarEnabled(open!=0);SetShowWeaponGroups(open!=0);
        assert(profileWrites==writes && server.sends==0); // No per-frame disk/network traffic.
        RestartProfile();AssignGameSessionFlags(~0u);
        assert(GetSavedRadarAutoMode()==mode && GetSavedRadarRange(2)==mode && GetSavedRadarEnabled()==(open!=0));
        assert(GetSavedTargetingProjection()==projection && GetSavedWeaponGroup()==group);
        assert(GetSavedHealthWindowLocked()==(open!=0) && GetSavedHealthWindowOpen()==(open!=0));
        assert(GetSavedTargetingWindowLocked()==(open!=0) && GetSavedTargetingWindowOpen()==(open!=0));
        assert(GetSavedTargetingAutoselect()==(open!=0) && GetSavedHealthViewLeft()==(open!=0));
        assert(GetSavedAutoTurretsEnabled(false)==(open!=0) && GetSavedAutoTurretReserve(0)==group*15);
        assert(GetShowWeaponGroups()==(open!=0) && profileWrites==writes && server.sends==0);
    }
    auto before=profile;
    SetSavedRadarAutoMode(3);SetSavedRadarRange(3);SetSavedWeaponGroup(6);SetSavedTargetingProjection(4);SetSavedAutoTurretReserve(91);
    assert(profile==before);
    writeOk=false;SetShowWeaponGroups(!GetShowWeaponGroups());assert(!HudPreferencesSaved() && profile==before);
    writeOk=true;SetShowWeaponGroups(!GetShowWeaponGroups());assert(HudPreferencesSaved() && profile!=before);
    SetGameSessionFlags(8,false);assert(server.word==7 && (server.word&~15u)==0);
    SetGameSessionFlags(8,true);assert(server.word==15);
    before=profile;G_Server=nullptr;SetSavedRadarAutoMode(0);assert(GetSavedRadarAutoMode()==0);
    puts("PASS: global HUD profile, one-time legacy import, cross-character/restart persistence, no save broadcasts, write failure, native flags");
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
