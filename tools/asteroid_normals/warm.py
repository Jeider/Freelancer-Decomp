"""Warm and verify the installed game's real RP9 surface/shadow cache."""
from pathlib import Path
import os
import subprocess

REPO = Path(__file__).resolve().parents[2]


def warm(game):
    out = REPO / 'src/obj/asteroid_normals'
    out.mkdir(parents=True, exist_ok=True)
    build = out / 'warm_build.cmd'
    build.write_text('@echo off\n'
        'call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
        'if errorlevel 1 exit /b 1\n'
        'set "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
        'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX '
        '/Isrc/RP9 tools/warm_surface_cache.cpp /Fosrc/obj/asteroid_normals/warm.obj '
        '/Febin/warm_surface_cache.exe /link "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib"\n')
    subprocess.run(['cmd', '/c', str(build)], cwd=REPO, check=True)
    # No isolated test-cache override: use the same default directory as the game.
    env = dict(os.environ)
    env['PATH'] = str(game / 'bin') + os.pathsep + env.get('PATH', '')
    command = [str(REPO / 'bin/warm_surface_cache.exe')]
    print('Warming installed shaders in the game cache...', flush=True)
    subprocess.run(command, cwd=game, env=env, check=True)
    result = subprocess.run(command, cwd=game, env=env, check=True, capture_output=True, text=True)
    print(result.stdout, end='', flush=True)
    lines = [line for line in result.stdout.splitlines() if ' bytes,' in line]
    expected = 13 if (game / 'DATA_EXTRA/SHADERS/room_material.hlsl').is_file() else 10
    if (game / 'DATA_EXTRA/SHADERS/room_contact.hlsl').is_file(): expected += 1
    if (game / 'DATA_EXTRA/SHADERS/room_shadow.hlsl').is_file(): expected += 4
    if 'SURFACE_GREENHOUSE' in (game / 'DATA_EXTRA/SHADERS/surface_material.hlsl').read_text(): expected += 4
    if 'SURFACE_SHIP_NORMALS' in (game / 'DATA_EXTRA/SHADERS/surface_material.hlsl').read_text(): expected += 4
    if 'SURFACE_NOMAD' in (game / 'DATA_EXTRA/SHADERS/surface_material.hlsl').read_text(): expected += 6
    if (game / 'DATA_EXTRA/SHADERS/code_beam.hlsl').is_file(): expected += 2
    if len(lines) != expected or any(' HIT,' not in line for line in lines):
        raise RuntimeError(f'Cache verification failed: expected {expected}/{expected} cache hits on the second pass.')
    print(f'Verified: all {expected} surface/shadow/room variants loaded from the game cache.', flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    warm(parser.parse_args().game_root.resolve(strict=True))
