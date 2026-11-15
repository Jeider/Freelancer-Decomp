#include "common_reputation.h"
#include "common_misc.h"
#include "common_ini.h"
#include "player_customization.h"
#include "dacom.h"
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>

// Compile the actual server writer and reader functions, extracted without edits.
struct ISave {
    std::string Text;
    void WriteString(char const* key,char const* value) { Text+=key; Text+=" = "; Text+=value; Text+='\n'; }
};
char const* PlayerDbSource="customization_check";
// Unrelated display controls are inert; exercise SavePerfOptions' real file writer.
namespace NativeSubtitles { bool CutsceneEnabled(){return true;} void WritePreferences(FILE*){} }
namespace ColorGrade { int ConfiguredPreset(){return 0;} void WritePreferences(FILE*){} }
namespace HudTilt { float ConfiguredAngle(){return 0;} }
struct { int width=1280,height=720,color_bpp=32,depth_bpp=24; } g_display;
struct { char const* Name; float Applied; } G_Options[]={{"test",1.f}};
unsigned const kOptionCount=1;
bool G_bSkipMachineWarnings=false;
#include "save_functions.inc"

void RoundTrip(Costume const& base,Costume const& comm) {
    ISave output; output.Text="[Player]\n";
    Server_WriteCostume(output,"",base); Server_WriteCostume(output,"com_",comm);
    FILE* file=fopen("costume_roundtrip.ini","wb"); assert(file);
    fwrite(output.Text.data(),1,output.Text.size(),file); fclose(file);
    Costume restoredBase={},restoredComm={};
    INI_Reader input; assert(input.open("costume_roundtrip.ini",false)); assert(input.read_header());
    while(input.read_value()) {
        char const* key=input.get_name_ptr(); bool com=strncmp(key,"com_",4)==0;
        FCostumeTarget target={com ? &restoredComm : &restoredBase,GetCostumeDescriptions()};
        assert(LoadCostumeKey(input,target,com ? key+4 : key,"roundtrip"));
    }
    assert(Costume_is_equal(base,restoredBase)); assert(Costume_is_equal(comm,restoredComm));
}
int main() {
    using namespace PlayerCustomization;
    assert(wcscmp(Bodies[0].Label,L"\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u0430\u044f \u043e\u0434\u0435\u0436\u0434\u0430")==0);
    LoadBodypartDescriptions("D:/Games/FL_MOD/DATA/CHARACTERS/bodyparts.ini");
    LoadBodypartDescriptions("D:/Games/FL_MOD/DATA/CHARACTERS/bodyparts_player.ini");
    LoadCostumeDescriptions("D:/Games/FL_MOD/DATA/CHARACTERS/costumes.ini");
    auto* desc=GetCostumeDescriptions(); assert(desc && desc->find_costume("trent"));
    Costume original={}; desc->get_costume("trent",original);
    unsigned head=original.PartIds[0];
    int combinations=0;
    for(int b=0;b<_countof(Bodies);++b) for(int h=0;h<_countof(Hats);++h) for(int c=0;c<_countof(Helmets);++c) {
        Selection choice; choice.Body=b; choice.Hat=h; choice.Helmet=c;
        Costume base=original,comm=original; Apply(base,comm,choice);
        assert(base.PartIds[0]==head && comm.PartIds[0]==head);
        assert(base.AccessoryCount==(h ? 1u : 0u)); assert(comm.AccessoryCount==1);
        for(int i=0;i<4;++i) assert(base.PartIds[i] && comm.PartIds[i]);
        Costume repeatBase=base,repeatComm=comm;
        Apply(repeatBase,repeatComm,choice);
        assert(Costume_is_equal(base,repeatBase) && Costume_is_equal(comm,repeatComm));
        RoundTrip(base,comm);
        Selection reset; Apply(base,comm,reset);
        assert(base.AccessoryCount==0 && comm.AccessoryCount==1);
        ++combinations;
    }
    char folder[MAX_PATH]={}; assert(GetUserDataPath(folder));
    // Never test persistence against the user's actual preferences.
    assert(strstr(folder,"customization") && strstr(folder,"SAVE"));
    std::string path=std::string(folder)+"/PerfOptions.ini";
    assert(WritePrivateProfileStringA("Costume","unrelated_key","keep",path.c_str()));
    for(int c=0;c<_countof(Helmets);++c) {
        Selection selected; selected.Body=c%_countof(Bodies); selected.Hat=c%_countof(Hats); selected.Helmet=c;
        assert(Save(selected)); Selection loaded=Load();
        assert(loaded.Body==selected.Body && loaded.Hat==selected.Hat && loaded.Helmet==selected.Helmet);
        SavePerfOptions("PerfOptions.ini"); loaded=Load();
        assert(loaded.Body==selected.Body && loaded.Hat==selected.Hat && loaded.Helmet==selected.Helmet);
    }
    char retained[32]={}; GetPrivateProfileStringA("Costume","unrelated_key","",retained,sizeof(retained),path.c_str());
    assert(strcmp(retained,"keep")==0);
    Selection chosen; chosen.Body=5; chosen.Hat=2; chosen.Helmet=14; assert(Save(chosen));
    Costume base=original,comm=original;
    SetMultiPlayer(true); PlayerCostume_ApplyOverride(base,comm);
    assert(Costume_is_equal(base,original) && Costume_is_equal(comm,original));
    SetMultiPlayer(false); PlayerCostume_ApplyOverride(base,comm);
    assert(base.AccessoryCount==1 && comm.AccessoryCount==1); RoundTrip(base,comm);
    Costume full={}; for(unsigned i=1;i<=16;++i) Costume_AddAccessory(full,i);
    assert(full.AccessoryCount==8); Costume_AddAccessory(full,0); Costume_AddAccessory(full,1); assert(full.AccessoryCount==8);
    // Replacing a hat preserves other real accessories, including after resetting the hat.
    base=original; comm=original;
    base.AccessoryIds[base.AccessoryCount++]=desc->find_accessory("prop_shades_03")->Id;
    Apply(base,comm,chosen); assert(base.AccessoryCount==2); RoundTrip(base,comm);
    chosen.Hat=0; Apply(base,comm,chosen); assert(base.AccessoryCount==1); RoundTrip(base,comm);
    printf("PASS: %d costume combinations, save/load round trips, defaults, idempotence, preference persistence, MP guard, bounds\n",combinations);
    FreeCostumeDescriptions();
}
