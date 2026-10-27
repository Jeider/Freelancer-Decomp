"""Compile/render the production beam shader on D3D9, including depth and fog checks."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/code_beam'
OUT.mkdir(parents=True, exist_ok=True)
build = OUT / 'check.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
    'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
    'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 '
    'tools/code_beam/check.cpp /Fosrc/obj/code_beam/check.obj /Febin/code_beam_check.exe '
    '/link d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" user32.lib\n')
subprocess.run(['cmd', '/c', str(build)], cwd=ROOT, check=True)
env = dict(os.environ, FREELANCER_SHADER_CACHE_DIR=str(OUT / 'shader_cache'))
# Extract the actual game atlas read-only for the optional GPU comparison image.
atlas_source = Path('D:/games/FL_MOD/DATA/FX/beam.txm')
if atlas_source.is_file():
    sys.path.insert(0, str(ROOT / 'tools'))
    from generate_station_lods import read_tree
    def extract(node):
        if node.name == 'code_beam':
            for child in node.children:
                if child.name == 'MIP0':
                    (OUT / 'atlas.tga').write_bytes(child.blob)
        for child in node.children:
            extract(child)
    for node in read_tree(atlas_source.read_bytes())[1]:
        extract(node)
subprocess.run([str(ROOT / 'bin/code_beam_check.exe')], cwd=ROOT, env=env, check=True)
