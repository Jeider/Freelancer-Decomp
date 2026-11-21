"""Build/run the hidden RP9 fog probe and the production shader manifest; no game launch."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/graphics_settings/nebula_object_fog'
BUILD = OUT / 'build'
PROBE = OUT / 'probe'
EXTRA_DEFINES = []
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    compiler, env = compiler_env()
    sdk = Path('C:/Program Files (x86)/Windows Kits/10/Include')
    version = sorted(p for p in sdk.iterdir() if (p / 'um/Windows.h').exists())[-1]
    env['INCLUDE'] = ';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper()) + ';' + str(version / 'winrt') + ';C:/DXSDK_Jun10/Include'
    env['PATH'] = str(ROOT / 'bin') + ';D:/Games/FL_MOD/bin;' + env['PATH']
    env['FREELANCER_SHADER_CACHE_DIR'] = str(PROBE / 'cache')
    env['TEMP'] = env['TMP'] = str(PROBE)
    (PROBE / 'bin').mkdir(parents=True, exist_ok=True)
    shader_dir = PROBE / 'DATA_EXTRA/SHADERS'
    shader_dir.mkdir(parents=True, exist_ok=True)
    shader = ROOT / 'DATA_EXTRA/SHADERS/surface_material.hlsl'
    shutil.copy2(shader, shader_dir / shader.name)
    inputs = [shader, ROOT / 'src/RP9/RP9Ex.cpp', ROOT / 'src/RP9/RP9Ex.h',
              ROOT / 'src/freelancer/Client/nebula_fog_shape.h',
              ROOT / 'src/freelancer/Client/space_scene_obj_draw.cpp',
              ROOT / 'src/freelancer/Client/cli_asteroid_dynamic.cpp']
    before = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    for name, source, objects, libs, run_args in [
        ('route', 'tools/nebula_control/check_object_fog.cpp',
         [str(BUILD / 'obj/RP9' / (p + '.obj')) for p in ('RP9', 'RP9Ex', 'Mgsdb')],
         ['dacom.lib', 'ddraw.lib', 'version.lib', 'C:/DXSDK_Jun10/Lib/x86/DxErr.lib', 'legacy_stdio_definitions.lib'],
         [str(OUT / 'comparison.png')]),
        ('manifest', 'tools/nebula_control/check_object_fog_manifest.cpp', [], ['gdi32.lib'],
         [str(ROOT / 'DATA_EXTRA/SHADERS') + '/', str(PROBE / 'manifest_cache')])]:
        exe = PROBE / 'bin' / (name + '.exe')
        command = [str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/MD', '/O2', '/std:c++17', '/utf-8',
                   '/DRP_DIRECT3D9', '/DFREELANCER_DLSS5', '/D_ITERATOR_DEBUG_LEVEL=1',
                   '/D_CRT_SECURE_NO_WARNINGS', '/DNOMINMAX', '/Isrc/RP9', '/Isrc/include', source,
                   *EXTRA_DEFINES,
                   '/Fo' + str(PROBE / (name + '.obj')), '/Fe' + str(exe), *objects,
                   '/link', '/LTCG', '/LIBPATH:' + str(ROOT / 'bin'),
                   'd3d9.lib', 'user32.lib', 'gdi32.lib', 'C:/DXSDK_Jun10/Lib/x86/d3dx9.lib', *libs]
        for suffix, cmd in [('build', command), ('result', [str(exe), *run_args])]:
            log = OUT / (name + '_' + suffix + '.log')
            with log.open('wb') as stream:
                result = subprocess.run(cmd, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode:
                print(log.read_text(errors='replace')[-7000:])
            result.check_returncode()
        print('PASS', name, flush=True)
    assert before == {str(p.relative_to(ROOT)): digest(p) for p in inputs}, 'Sources changed during checks'
    names = set(re.findall(r'^CACHE ([0-9a-f]{64}\.bin)$', (OUT / 'manifest_result.log').read_text(), re.M))
    assert names, 'Manifest did not list the verified cache keys'
    cache_files = {name: digest(PROBE / 'manifest_cache' / name) for name in sorted(names)}
    report = {'sources': before, 'binaries': {p: digest(BUILD / 'bin' / p) for p in ('RP9.dll', 'freelancer.exe')},
              'cache_files': cache_files,
              'route': 'PASS', 'manifest': 'PASS', 'preview': 'comparison.png', 'game_launched': False}
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
