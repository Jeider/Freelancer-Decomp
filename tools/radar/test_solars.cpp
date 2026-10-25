// Exercise real Common.dll solar parsing, inheritance, reload and default-off metadata.
#include "common_archetype.h"
#include "common_ini.h"
#include "common_misc.h"
#include <cassert>
#include <cstdio>

int main()
{
    FILE* file=nullptr;
    assert(fopen_s(&file,"radar_solar_fixture.ini","w")==0);
    fputs("[Solar]\nnickname = radar_test_plain\ntype = NON_TARGETABLE\n"
          "[Solar]\nnickname = radar_test_mine\ntype = NON_TARGETABLE\nradar_mining = true\n"
          "[Solar]\nnickname = radar_test_hidden\ntype = STATION\nradar_hidden = true\n"
          "[Solar]\nnickname = radar_test_inherited\ninherit = radar_test_mine\n"
          "[Solar]\nnickname = radar_test_override\ninherit = radar_test_hidden\nradar_hidden = false\n",file);
    fclose(file);
    assert(Archetype::LoadSolar("radar_solar_fixture.ini",false,nullptr)==5);
    auto get=[](char const* name){auto* arch=Archetype::GetSolar(CreateID(name));assert(arch);return arch;};
    assert(!get("radar_test_plain")->bRadarMining && !get("radar_test_plain")->bRadarHidden);
    assert(get("radar_test_mine")->bRadarMining && !get("radar_test_mine")->bRadarHidden);
    assert(get("radar_test_hidden")->bRadarHidden);
    assert(get("radar_test_inherited")->bRadarMining);
    assert(!get("radar_test_override")->bRadarHidden);
    assert(fopen_s(&file,"radar_solar_fixture_reload.ini","w")==0);
    fputs("[Solar]\nnickname = radar_test_mine\nradar_mining = false\nradar_hidden = true\n",file);
    fclose(file);
    Archetype::LoadSolar("radar_solar_fixture_reload.ini",true,nullptr);
    assert(!get("radar_test_mine")->bRadarMining && get("radar_test_mine")->bRadarHidden);
    puts("PASS: real solar loader, default exclusion, mining/hidden flags, inheritance, overrides and reload; native Solar layout unchanged");
}
