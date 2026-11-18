"""Compile protocol tests and exercise MP rejection in the built Server.dll."""
from pathlib import Path
import subprocess
import sys
import shutil
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    compiler, env = compiler_env()
    out = ROOT / 'src/obj/train_courier/rpg1/bin'
    # Match the Common import library used to link this server. No live writes.
    shutil.copy2(Path('D:/Games/FL_MOD/bin/Common.dll'), out / 'Common.dll')
    env['PATH'] = str(ROOT / 'bin') + ';' + env['PATH']
    source = ROOT / 'tools/train_courier/check_space_transfer.cpp'
    command = [str(compiler / 'cl.exe'), '/nologo', '/std:c++17', '/W4', '/EHsc', '/MD',
               '/D_ITERATOR_DEBUG_LEVEL=1', '/I' + str(ROOT / 'src/include'), str(source),
               '/Fe:space_transfer_check.exe', '/Fo:space_transfer_check.obj', '/link',
               '/LIBPATH:' + str(out), 'Common.lib']
    subprocess.run(command, cwd=out, env=env, check=True)
    subprocess.run([str(out / 'space_transfer_check.exe'), str(out / 'Server.dll')],
                   cwd=out, env=env, check=True, timeout=30)
    inputs = [source, Path(__file__), ROOT / 'src/include/player_ship_transfer_state.h',
              ROOT / 'src/Server/player_ship_transfer.inl', out / 'Server.dll', out / 'Common.dll']
    report = {'scope': 'protocol and actual MP entry guard; no SP world/visual validation',
              'sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}}
    (out / 'space_transfer_checked.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
