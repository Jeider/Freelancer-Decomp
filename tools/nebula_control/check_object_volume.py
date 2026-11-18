"""Validate object-only fog routing and unchanged cloud rendering on a hidden D3D9 device."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
OUT = ROOT / 'out/graphics_settings/nebula_object_fog/object_volume'
PROBE = OUT / 'probe'
BUILD = OUT / 'build'
CASES = 'tools/nebula_control/object_volume_cases.inl'
ALLOW_SHADER_CHANGES = ()
REPAIR_OBJECT_DEPTH = False
COMPARE_INSTALLED_COMPOSITE = False
EXTRA_SOURCES = []
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tools/nebula_control')]
import exclusion_volume_all as reference
from build_asf_hq import compiler_env


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(source, signature):
    start = source.index(signature)
    begin = source.index('{', start)
    depth = 1
    end = begin + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def run(name, command, env):
    log = OUT / (name + '.log')
    with log.open('wb') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        print(log.read_text(errors='replace')[-6000:])
    result.check_returncode()


def main():
    for folder in ('inputs', 'textures', 'cache'):
        (PROBE / folder).mkdir(parents=True, exist_ok=True)
    protected = [GAME / 'DATA_EXTRA/VOLUMETRIC/volumetric.ini',
                 ROOT / 'DATA_EXTRA/VOLUMETRIC/volumetric.ini',
                 GAME / 'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini',
                 GAME / 'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini',
                 GAME / 'Assets/Pythonlancer/universe/content/asteroid_definition.py']
    protected += sorted((GAME / 'DATA/SOLAR/NEBULA_MOD/GENERATED').glob('gen_om15_*_nebula.ini'))
    shader_names = ('nebula_volume.hlsl', 'nebula_volume.hlsli', 'nebula_composite.hlsl',
                    'surface_material.hlsl', 'far_rocks.hlsl')
    for name in shader_names:
        installed, source = GAME / 'DATA_EXTRA/SHADERS' / name, ROOT / 'DATA_EXTRA/SHADERS' / name
        if name not in ALLOW_SHADER_CHANGES:
            assert digest(installed) == digest(source), name
        protected += [installed, source]
    guards = {str(p): digest(p) for p in protected}
    source_paths = ['src/freelancer/Client/nebula_volume.cpp', 'src/freelancer/Client/nebula_volume.h',
                    'src/freelancer/Client/space_scene_obj_draw.cpp', 'src/freelancer/Client/far_rocks.cpp',
                    'tools/nebula_control/check_object_volume.py', CASES,
                    'tools/nebula_control/check_omega15_volume.cpp', 'tools/exclusion_volume_all.py', *EXTRA_SOURCES]
    sources = {p: digest(ROOT / p) for p in source_paths}
    source = (ROOT / source_paths[0]).read_text(encoding='utf-8-sig')
    routes = ['FVolumeEntry* FindEntry(', 'bool NebulaVolume::ReplacesObjectFog(',
              'bool NebulaVolume::UsesVolumeForObjectSurfaces(', 'bool NebulaVolume::ReplacesFogOverlay(']
    route = '''#include <cstdio>
#include <cstdlib>
int quality=3, enabled=1;unsigned activeSystem=15;
namespace GraphicsSettings {enum {Nebulae};int Get(int){return quality;}}
int PortConfigInt(char const*,char const*,int){return enabled;}
unsigned CreateID(char const*){return 15;}
unsigned StarSysGetActiveSystemId(){return activeSystem;}
struct FNebulaEffect {};
struct FVolumeEntry {FNebulaEffect* Nebula;struct {float ReplaceObjectFog,ReplaceFogOverlay;} Settings;bool bBackground;};
FVolumeEntry GEntries[1];int GEntryCount=0;
namespace NebulaVolume {bool ReplacesObjectFog(FNebulaEffect const*);bool UsesVolumeForObjectSurfaces(FNebulaEffect const*);bool ReplacesFogOverlay(FNebulaEffect const*);}
'''
    route += '\n'.join(function(source, signature) for signature in routes)
    route += '''
int main(int argc,char**argv){enabled=argc>1?atoi(argv[1]):1;FNebulaEffect nebula,other;
GEntries[0].Nebula=&nebula;
for(int available=0;available<2;++available)for(int q=0;q<4;++q)for(int system:{15,16})
for(int legacy=0;legacy<2;++legacy)for(int background=0;background<2;++background){
 GEntryCount=available;quality=q;activeSystem=system;GEntries[0].bBackground=background;
 GEntries[0].Settings.ReplaceObjectFog=float(legacy);GEntries[0].Settings.ReplaceFogOverlay=0;
 bool expected=available&&(legacy||(enabled&&q>=2&&system==15&&!background));
 if(NebulaVolume::UsesVolumeForObjectSurfaces(&nebula)!=expected)return 2;
 if(NebulaVolume::UsesVolumeForObjectSurfaces(nullptr)||NebulaVolume::UsesVolumeForObjectSurfaces(&other))return 3;
 if(NebulaVolume::ReplacesObjectFog(&nebula)!=(available&&legacy))return 4;
 if(NebulaVolume::ReplacesFogOverlay(&nebula))return 5;
}puts("PASS real production routing: quality, system, opt-out, unavailable GPU/resources, background volume, legacy policies");}
'''
    route = '#include <initializer_list>\n' + route
    (PROBE / 'route.cpp').write_text(route)
    draw = (ROOT / source_paths[2]).read_text()
    rocks = (ROOT / source_paths[3]).read_text()
    assert draw.count('NebulaVolume::UsesVolumeForObjectSurfaces(Nebula)') == 1
    assert rocks.count('NebulaVolume::UsesVolumeForObjectSurfaces(Nebula)') == 1
    assert draw.count('NebulaVolume::ReplacesObjectFog(G_FieldController)') == 2
    failure = source[source.index('        if (Failure)'):source.index('        if (Failure)') + 130]
    assert 'GEntryCount = 0;' in failure and 'return;' in failure

    config = reference.sections(reference.read(protected[0]))
    common = {**reference.defaults(), **next(v for n, v in config if n == 'nebula')}
    styles = {v['name']: v for n, v in config if n == 'nebulastyle'}
    overrides = {v['file'].lower(): v for n, v in config if n == 'nebulaoverride'}
    assert 'om15_full_volume' not in styles
    reference.OUT = PROBE
    system = reference.sections(reference.read(protected[2]))
    star = next(d['star'] for n, d in system if n == 'object' and 'star' in d)
    stars = {d['nickname'].lower(): d for n, d in reference.sections(reference.read(GAME / 'DATA/SOLAR/stararch.ini')) if 'nickname' in d}
    case = {'id': 'omega15', 'basename': 'gen_om15_neb1_nebula',
            'text': reference.read(GAME / 'DATA/SOLAR/NEBULA_MOD/GENERATED/gen_om15_neb1_nebula.ini'),
            'context': {'volumetric': True, 'star': star}}
    reference.constants(case, common, styles, overrides, stars)
    assert case['status'] == 'ready' and case['style'] == 'walker', case
    assert case['settings']['replace_object_fog'] == '0'
    assert case['notes'] == ['Hybrid/retail cloud sprites are active in game and omitted here',
                             'Retail fog overlay omitted'], case['notes']
    settings = case['settings']
    fog = next(d for n, d in reference.sections(case['text']) if n == 'fog')
    exclusion = next(d for n, d in reference.sections(case['text']) if n == 'exclusion zones')
    near, span = float(fog['near']), float(fog['distance'])
    scale = span / (float(exclusion['fog_far']) - near) * float(settings['exclusion_density_scale'])
    (PROBE / 'object_volume_fixture.h').write_text(
        f'const float FixtureFogStart={near:.8f}f, FixtureFogEnd={near+span:.8f}f;\n'
        + 'const float FixtureFogRgb[3]={' + ','.join(f'{float(v)/255:.8f}f' for v in fog['color'].split(',')) + '};\n'
        + f'const float FixtureExclusionScale={scale:.8f}f;\n')
    noise = source[source.index('    unsigned int Hash(unsigned int X)'):source.index('    // Coverage (the fraction')]
    (PROBE / 'nebula_noise_fixture.h').write_text('const unsigned long kNoiseSize=64;\nfloat Clamp(float x,float a,float b){return std::max(a,std::min(b,x));}\n' + noise)
    gpu = (ROOT / 'tools/nebula_control/check_omega15_volume.cpp').read_text()
    gpu = gpu[:gpu.index(' double previous=1;')] + '#include "' + str(ROOT / CASES).replace('\\', '/') + '"\n}\n'
    if REPAIR_OBJECT_DEPTH:
        gpu = gpu.replace(' auto pass=', ' bool repairDepth=true;\n auto pass=')
        gpu = gpu.replace('float p[26][4]={};', 'float p[27][4]={};p[26][0]=repairDepth?1.f:0.f;p[26][1]=c[89][3];')
        gpu = gpu.replace('SetPixelShaderConstantF(0,&p[0][0],26)', 'SetPixelShaderConstantF(0,&p[0][0],27)')
    if COMPARE_INSTALLED_COMPOSITE:
        assert REPAIR_OBJECT_DEPTH
        original = '''
 IDirect3DPixelShader9*originalComposite=nullptr;
 std::vector<Rp9Startup::FJob>originalJobs;
 Require(Rp9Startup::Build("D:/Games/FL_MOD/DATA_EXTRA/SHADERS/",originalJobs,err),err.c_str());
 for(auto const&job:originalJobs)if(job.Name=="nebula_composite.hlsl"&&job.Profile[0]=='p'){
  std::vector<unsigned char>code;std::string msg;bool hit=false;
  Check(Rp9Startup::Compile(job,"D:/Games/FL_MOD/DATA_EXTRA/SHADERS/",code,msg,hit));
  Check(d->CreatePixelShader((DWORD*)code.data(),&originalComposite));
 }Require(originalComposite!=nullptr,"installed composite baseline");
'''
        gpu = gpu.replace(' std::vector<unsigned long>noise;', original + ' std::vector<unsigned long>noise;')
        gpu = gpu.replace('march?ps:composite', 'march?ps:(repairDepth?composite:originalComposite)')
    for before, after in [
        ('#include "nebula_noise_fixture.h"', '#include "nebula_noise_fixture.h"\n#include "object_volume_fixture.h"'),
        ('Require(argc==6,', 'Require(argc==8,'),
        ('LW=W/2,LH=H/2;', 'LW=unsigned(W*atof(argv[6])),LH=unsigned(H*atof(argv[6]));'),
        (' Require(vs&&ps&&composite,"production volume shader pair");', ''' Require(vs&&ps&&composite,"production volume shader pair");
 IDirect3DTexture9*puff=nullptr;Check(D3DXCreateTextureFromFileA(d,argv[7],&puff));Check(d->SetTexture(2,puff));
 for(auto state:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})Check(d->SetSamplerState(2,state,D3DTEXF_LINEAR));
 for(auto state:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV})Check(d->SetSamplerState(2,state,D3DTADDRESS_CLAMP));''')]:
        assert gpu.count(before) == 1, before
        gpu = gpu.replace(before, after)
    (PROBE / 'gpu.cpp').write_text(gpu)
    compiler, env = compiler_env()
    env['INCLUDE'] = ';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper()) + ';C:/DXSDK_Jun10/Include'
    env['PATH'] = str(ROOT / 'bin') + ';' + str(GAME / 'bin') + ';' + env['PATH']
    env['TEMP'] = env['TMP'] = str(PROBE)
    for name, libs in [('route', []), ('gpu', ['d3d9.lib', 'user32.lib', 'C:/DXSDK_Jun10/Lib/x86/d3dx9.lib'])]:
        command = [str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/MD', '/O2', '/std:c++17', '/utf-8',
                   '/DNOMINMAX', '/D_CRT_SECURE_NO_WARNINGS', '/Isrc/RP9', '/Isrc/include',
                   '/Itools/nebula_control', '/I' + str(PROBE), str(PROBE / (name + '.cpp')),
                   '/Fo' + str(PROBE / (name + '.obj')), '/Fe' + str(PROBE / (name + '.exe')), '/link', *libs]
        run(name + '_build', command, env)
    for enabled in (0, 1):
        run('route_' + str(enabled), [str(PROBE / 'route.exe'), str(enabled)], env)
    for q in (2, 3):
        run('gpu_' + str(q), [str(PROBE / 'gpu.exe'), str(PROBE / 'inputs/omega15.bin'),
            str(ROOT / 'DATA_EXTRA/SHADERS') + '/', str(PROBE / 'cache'), str(OUT / ('objects_' + str(q))),
            str(q), settings['resolution_scale'], case['texture']], env)
        print((OUT / ('gpu_' + str(q) + '.log')).read_text())
    assert guards == {str(p): digest(p) for p in protected}, 'Protected cloud/content inputs changed'
    assert sources == {p: digest(ROOT / p) for p in source_paths}, 'Sources changed during validation'
    report = {'passed': True, 'sources': sources, 'guards': guards, 'case': case,
              'binary': digest(BUILD / 'bin/freelancer.exe'), 'game_launched': False,
              'scope': 'om15, medium/high; prepared depth volume; surface fog only',
              'limitations': 'Synthetic sphere/depth fixture. Existing hybrid sprites, retail overlay, shells and game scene omitted identically in both renders.',
              'shader_changes': list(ALLOW_SHADER_CHANGES), 'profile_changes': False,
              'compared_installed_composite': COMPARE_INSTALLED_COMPOSITE}
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS production route and GPU cases; protected cloud/content hashes unchanged')


if __name__ == '__main__':
    main()
