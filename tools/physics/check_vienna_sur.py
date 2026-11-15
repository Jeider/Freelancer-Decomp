"""Exercise the production detached-part filter with installed Vienna SUR ledges."""
import os
from pathlib import Path
import struct
import subprocess
import sys

from check_gravity import function

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/tradelane'))
from docking_surface import parts


def main():
    out = ROOT / 'src/obj/vienna_sur_check'
    out.mkdir(parents=True, exist_ok=True)
    code = r'''
#include <cassert>
#include <cstdio>
#include "ivp_compact_builder/ivp_compact_ledge.h"
struct CObject {
    bool attached = true;
    long part_to_inst(unsigned id) const { return attached && id == 0 ? 1 : -1; }
};
struct IVP_SurfaceManager_OutList { int Capacity, Count; void** Elems; };
'''
    source = 'src/Common/common_physys_build.cpp'
    code += function(source, 'bool PhySys_LedgeIsAttached(')
    code += function(source, 'void PhySys_DropDetachedLedges(')
    code += '\nint main() { CObject owner;\n'
    count = 0
    for path in sorted(Path('D:/Games/FL_MOD/DATA/SOLAR/misc').glob('vienna_*.sur')):
        surface = dict(parts(path.read_bytes())[0][1])[b'surf']
        stack = [struct.unpack_from('<I', surface, 32)[0]]
        while stack:
            offset = stack.pop()
            right, ledge = struct.unpack_from('<ii', surface, offset)
            if right:
                stack.extend([offset + 28, offset + right])
            if not ledge:
                continue
            client, flags = struct.unpack_from('<II', surface, offset + ledge + 4)
            inner = bool(flags & 3)
            assert inner or client == 0, (path, client)
            # Same physical hull must survive when attached. After detach only
            # structural hulls survive; terminal hulls must be removed.
            code += f'''{{ IVP_Compact_Ledge ledge{{}};
ledge.ClientData = {client}; ledge.SizeAndFlags = {flags}u;
void* entries[] = {{&ledge}};
IVP_SurfaceManager_OutList list{{1, 1, entries}};
owner.attached = true; PhySys_DropDetachedLedges(&owner, &list);
assert(list.Count == 1);
owner.attached = false; PhySys_DropDetachedLedges(&owner, &list);
assert(list.Count == {int(inner)});
}}\n'''
            count += 1
    assert count > 100
    code += f'puts("PASS: {count} installed Vienna ledges, attached and detached filtering"); }}\n'
    (out / 'check.cpp').write_text(code)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10')
    version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(map(str, [vc/'include', ROOT/'src/IVP'] +
        [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')]))
    env['LIB'] = ';'.join(map(str, [vc/'lib/x86'] +
        [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')]))
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17',
                    '/W4', '/WX', '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'],
                   cwd=out, env=env, check=True)
    subprocess.run([str(out/'check.exe')], cwd=out, check=True)


if __name__ == '__main__':
    main()
