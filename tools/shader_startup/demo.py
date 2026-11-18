"""Build and check the standalone shader window with the client's embedded resource."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/shader_startup/animation'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    resource_dir = ROOT / 'src/freelancer/resources'
    command = OUT / 'build_demo.cmd'
    command.write_text(
        '@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" >nul\n'
        'if errorlevel 1 exit /b 1\n'
        f'rc /nologo /i "{resource_dir}" /fo "{OUT / "animation.res"}" "{resource_dir / "shader_startup/animation.rc"}"\n'
        'if errorlevel 1 exit /b 1\n'
        'cl /nologo /EHsc /std:c++17 /utf-8 /W4 /O2 /MT /D_CRT_SECURE_NO_WARNINGS /Isrc/RP9 '
        f'tools/shader_startup/demo.cpp /Fo"{OUT / "demo.obj"}" /Fe"{OUT / "shader_window_demo.exe"}" '
        f'/link /SUBSYSTEM:WINDOWS "{OUT / "animation.res"}" user32.lib gdi32.lib shell32.lib\n', encoding='utf-8')
    subprocess.run(['cmd', '/c', str(command)], cwd=ROOT, check=True)
    result = subprocess.run([str(OUT / 'shader_window_demo.exe'), '--check'], cwd=OUT)
    report = OUT / 'animation_check.txt'
    if report.exists():
        print(report.read_text())
    result.check_returncode()


if __name__ == '__main__':
    main()
