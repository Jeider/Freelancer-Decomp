"""D3D9 check of NeuroNet geometry AND actual staged atlas UV/orientation."""
import subprocess
from check import ROOT,VC,compiler_env
out=ROOT/'src/obj/nn_icons'
env=compiler_env();env['INCLUDE']+=';C:/DXSDK_Jun10/Include'
subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT',
    '/DNOMINMAX','/DNN_ICON_CHECK',f'/I{ROOT/"src/freelancer/Client"}',
    str(ROOT/'tools/cursors/check_gpu.cpp'),'/Fecheck_nn_gpu.exe','/link','d3d9.lib','user32.lib'],
    cwd=out,env=env,check=True)
subprocess.run([str(out/'check_nn_gpu.exe'),str(out)],check=True)
