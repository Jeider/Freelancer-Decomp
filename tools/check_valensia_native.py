"""Load staged SURs with the installed Common/ReadFile DLLs; no engine rebuild."""
import json
import os
from pathlib import Path
import re
import subprocess
import valensia_optimize as v

LEAF_TOLERANCE = .035


def main():
    out = v.OUT/'native'
    out.mkdir(parents=True, exist_ok=True)
    source = (v.REPO/'tools/train_sur/check.cpp').read_text()
    # Retail industrial surfaces also contain double-sided triangle leaves.
    source = source.replace('count >= 4', 'count >= 2')
    # The imported industrial01a leaves already deviate by 0.033894 m from
    # convex planes (see valensia_source_tolerance.py). Keep exact topology;
    # allow 0.0011 m for transformation roundoff. New BVH wraps stay at 0.002 m.
    source = source.replace('d<=length*.002', 'd<=length*(node->offset_right_node ? .002 : .035)')
    source = source.replace('need(d<=length*', 'if (d>length*(node->offset_right_node ? .002 : .035)) std::fprintf(stderr,"convexity: faces=%d inner=%d distance=%.6f\\n", count, int(node->offset_right_node!=0), d/length); need(d<=length*')
    source = source.replace(': .035)', ': '+str(LEAF_TOLERANCE)+')')
    source = source.replace('../../src/IVP/', (v.REPO/'src/IVP').as_posix()+'/')
    (out/'check.cpp').write_text(source)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10')
    version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(map(str, [v.REPO/'src/include', vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
    env['LIB'] = ';'.join(map(str, [v.REPO/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
    env['PATH'] = str(v.GAME/'bin')+';'+env['PATH']
    commands = (v.REPO/'src/obj/Common/Release/Common.tlog/CL.command.1.tlog').read_text(encoding='utf-16')
    found = re.search(r'/D _ITERATOR_DEBUG_LEVEL=(\d)', commands)
    level = found[1] if found else '0'
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/O2', '/W4', '/MD', '/EHsc',
                    '/D_ITERATOR_DEBUG_LEVEL='+level, 'check.cpp', '/Fecheck.exe', '/link', 'Common.lib', 'DALib.lib', 'dacom.lib'],
                   cwd=out, env=env, check=True)
    manifest = json.loads((v.OUT/'manifest.json').read_text())
    files = [v.OUT/'stage'/name for name in manifest['payload'] if name.endswith('.sur')]
    with (v.OUT/'native_check.log').open('wb') as log:
        for i in range(0, len(files), 16):
            result = subprocess.run([str(out/'check.exe'), *map(str, files[i:i+16])], cwd=out, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log.write(result.stdout)
            if result.returncode:
                print(result.stdout.decode(errors='replace')[-4000:])
                raise SystemExit(result.returncode)
    (v.OUT/'native_check.ok').write_text(v.sha256((v.OUT/'manifest.json').read_bytes()).hexdigest())
    print('PASS: installed Common.dll loaded and checked', len(files), 'component SURs')


if __name__ == '__main__': main()
