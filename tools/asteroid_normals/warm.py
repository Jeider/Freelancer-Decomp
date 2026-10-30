"""Warm and verify the installed game's real RP9 surface/shadow cache."""
from pathlib import Path
import os
import re
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
    env.pop('FREELANCER_SHADER_CACHE_DIR', None)
    env['PATH'] = str(game / 'bin') + os.pathsep + env.get('PATH', '')
    command = [str(REPO / 'bin/warm_surface_cache.exe')]
    print('Warming installed shaders in the game cache...', flush=True)
    subprocess.run(command, cwd=game, env=env, check=True)
    result = subprocess.run(command, cwd=game, env=env, check=True, capture_output=True, text=True)
    print(result.stdout, end='', flush=True)
    lines = [line for line in result.stdout.splitlines() if ' bytes,' in line]
    # The warmer also covers client effects. Its actual job list is authoritative;
    # a second handwritten count went stale when new shader families were added.
    summary = re.search(r'^jobs (\d+)$', result.stdout, re.M)
    if not summary:
        raise RuntimeError('Cache verification failed: missing shader job count.')
    expected = int(summary[1])
    if not expected:
        raise RuntimeError('Cache verification failed: no shader jobs.')
    if len(lines) != expected or any(' HIT,' not in line for line in lines):
        raise RuntimeError(f'Cache verification failed: expected {expected}/{expected} cache hits on the second pass.')
    print(f'Verified: all {expected} shader jobs loaded from the game cache.', flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    warm(parser.parse_args().game_root.resolve(strict=True))
