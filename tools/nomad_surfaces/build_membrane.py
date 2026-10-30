"""Build DDS conversion/native alpha-preview utility and run it on the GPU."""
import os
import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=root/'src/obj/nomad_membrane';out.mkdir(parents=True,exist_ok=True)
build=out/'build.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\nif errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\ncl /nologo /O2 /EHsc /std:c++17 /D_CRT_SECURE_NO_WARNINGS tools/nomad_surfaces/membrane_dds.cpp /Fosrc/obj/nomad_membrane/convert.obj /Febin/nomad_membrane_dds.exe /link user32.lib d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib"\n')
subprocess.run(['cmd','/c',str(build)],cwd=root,check=True)
subprocess.run([str(root/'bin/nomad_membrane_dds.exe'),*sys.argv[1:]],cwd=root,check=True)
