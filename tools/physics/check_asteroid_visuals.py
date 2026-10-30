"""Exercise production draw submission and object fade; validate all five Sig8 presets."""
import os
from pathlib import Path
import re
import subprocess
from check_gravity import function
from prepare_sig8_asteroids import GAME, FIELDS, convert_field

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'src/obj/asteroid_visual_check'
STUB = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <limits>
#include "server_asteroid_fade.h"
namespace Archetype { struct EqObj {bool bNomad=false;}; }
struct CEqObj {
    float CloakPercent=0;
    Archetype::EqObj arch;
    Archetype::EqObj* eqobjarch(){return &arch;}
};
struct FClientEquippedObj {
    CEqObj object;
    int Field_0xe0=0, index=7;
    long get_index(){return index;}
};
CEqObj* EquippedObjEqObj(FClientEquippedObj* go){return &go->object;}
float lastOpacity=1;int removes=0, sets=0, overrides=0, draws=0;void* lastExtra=nullptr;
void SetAppearanceInstanceValue(void*,void* bits){memcpy(&lastOpacity,&bits,4);++sets;}
void RemoveAppearanceInstanceValue(int){++removes;}
void GetAppearanceOverrideMaterial(unsigned kind,void** out){assert(kind==3);*out=(void*)3;++overrides;}
void GameobjSubmitDrawRetail(FClientEquippedObj*,unsigned* out,void*,unsigned,void*,void* extra){++draws;lastExtra=extra;*out=9;}
'''
CHECK = r'''
int main(){
    FClientEquippedObj rock, ordinary;
    auto draw=[](FClientEquippedObj& go){unsigned lod=0;assert(EquippedObjSubmitDrawRetail(&go,&lod,nullptr,0,nullptr,nullptr)==&lod);assert(lod==9);};
    draw(ordinary);assert(sets==0&&overrides==0&&lastExtra==nullptr);
    ServerAsteroidFade::Begin(&rock);draw(rock);
    assert(lastOpacity==0&&lastExtra==(void*)3&&rock.Field_0xe0==1&&rock.object.CloakPercent==0);
    // A camera/redraw or repeated initialization does not advance/reset age.
    draw(rock);ServerAsteroidFade::Tick(&rock,.375f);draw(rock);assert(lastOpacity==.5f);
    ServerAsteroidFade::Begin(&rock);draw(rock);assert(lastOpacity==.5f);
    ServerAsteroidFade::Tick(&rock,-1);ServerAsteroidFade::Tick(&rock,std::numeric_limits<float>::quiet_NaN());
    draw(rock);assert(lastOpacity==.5f);
    rock.object.CloakPercent=.5f;draw(rock);assert(lastOpacity==.25f&&rock.object.CloakPercent==.5f);
    rock.object.CloakPercent=0;ServerAsteroidFade::Tick(&rock,10);draw(rock);
    assert(rock.Field_0xe0==0&&removes==1&&lastExtra==nullptr);
    draw(rock);assert(removes==1);
    ServerAsteroidFade::Forget(&rock);assert(ServerAsteroidFade::Ages().empty());
    ServerAsteroidFade::Begin(&rock);draw(rock);assert(lastOpacity==0); // reused object address
    ServerAsteroidFade::Forget(&rock);
    ordinary.object.CloakPercent=.25f;draw(ordinary);assert(lastOpacity==.75f);
    puts("PASS: production material override, opacity/cloak composition, no gameplay mutation, camera independence, lifetime cleanup and reused address");
}
'''


def settings(data, skip_dynamic=False):
    result = []
    for section in re.split(rb'(?=^\[)', data, flags=re.M):
        lines = [s.strip() for s in section.splitlines() if s.strip() and not s.lstrip().startswith(b';')]
        if skip_dynamic and lines and lines[0] in (b'[DynamicAsteroids]', b'[ServerDynamicAsteroids]'):
            continue
        result.append(lines)
    return result


def main():
    for rel in FIELDS:
        original = (GAME/rel).read_bytes()
        converted = convert_field(original)
        assert settings(original, True) == settings(converted, True), rel
        assert converted.count(b'[ServerDynamicAsteroids]') == 3
        assert converted.count(b'count = 60') == 3
        assert converted.count(b'count = 0') == 3
        assert settings(convert_field(converted)) == settings(converted), rel
    print('PASS: all five Sig8 fields converted; FarRocks, billboards, exclusions, dust and bands preserved; migration idempotent')
    assert 'ServerAsteroidFade::Begin(this)' in function('src/freelancer/Client/client_gameobj.cpp', 'void FClientSolarGameobj::Slot170(')
    assert 'ServerAsteroidFade::Forget(this)' in function('src/freelancer/Client/client_gameobj.cpp', 'FClientSolarGameobj::~FClientSolarGameobj(')
    assert 'ServerAsteroidFade::Tick(this, Dt)' in function('src/freelancer/Client/client_gameobj.cpp', 'void FClientSolarGameobj::update(')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'check.cpp').write_text(STUB+function('src/freelancer/Client/space_scene_obj_draw.cpp', 'unsigned* EquippedObjSubmitDrawRetail(')+CHECK)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include', ROOT/'src/freelancer/Client'] +
                              [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')])
    env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                    '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'check.exe')], cwd=OUT, check=True)


if __name__ == '__main__':
    main()
