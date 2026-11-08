"""Compile and run the production dialogue UI state flow with fake game boundaries."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

out = ROOT / 'out/rpg_cutscenes/client_check'
out.mkdir(parents=True, exist_ok=True)
source = (ROOT / 'src/freelancer/Client/rpg_dialog.cpp').read_text()
source = re.sub(r'^#include [^\n]+\n', '', source, flags=re.M)
(out / 'client.inc').write_text(source)
deformable = (ROOT / 'src/freelancer/Client/gf_thorn_deformable.cpp').read_text()
functions = []
for signature in ('GENRESULT DACOM_API FThornDeformable::AdvanceTime(', 'void FThornDeformable::Stop()'):
    start = deformable.index(signature)
    end = deformable.index('\n}\n', start) + 3
    functions.append(deformable[start:end])
(out / 'deformable.inc').write_text('\n'.join(functions))
compiler, env = compiler_env()
subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/std:c++17', '/EHsc', '/MT',
                '/I' + str(out), str(Path(__file__).with_name('test_client.cpp')),
                '/Fe:' + str(out / 'test.exe'), '/Fo:' + str(out / 'test.obj')], cwd=out, env=env, check=True)
subprocess.run([str(out / 'test.exe')], cwd=out, check=True)
subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/std:c++17', '/EHsc', '/MT',
                '/I' + str(out), str(Path(__file__).with_name('test_deformable.cpp')),
                '/Fe:' + str(out / 'deformable.exe'), '/Fo:' + str(out / 'deformable.obj')], cwd=out, env=env, check=True)
subprocess.run([str(out / 'deformable.exe')], cwd=out, check=True)
